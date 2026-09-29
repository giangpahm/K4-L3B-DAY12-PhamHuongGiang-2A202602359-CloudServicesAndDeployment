from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Response, status
from pydantic import BaseModel, Field
from redis import Redis

from app.auth import get_current_user
from app.config import get_settings
from app.cost_guard import CostGuard
from app.lifecycle import lifecycle
from app.logging_utils import log_event
from app.rate_limiter import RateLimiter
from app.store import ConversationStore, get_redis_client
from utils.mock_llm import ask_llm


@asynccontextmanager
async def lifespan(app: FastAPI):
    lifecycle.install()
    yield


app = FastAPI(title="Cloud AI Agent", lifespan=lifespan)


def get_redis() -> Redis:
    settings = get_settings()
    return get_redis_client(settings.redis_url)


def get_store(r: Redis = Depends(get_redis)) -> ConversationStore:
    return ConversationStore(r)


def get_rate_limiter(r: Redis = Depends(get_redis)) -> RateLimiter:
    settings = get_settings()
    return RateLimiter(r, limit_per_minute=settings.rate_limit_per_minute)


def get_cost_guard(r: Redis = Depends(get_redis)) -> CostGuard:
    settings = get_settings()
    return CostGuard(r, monthly_budget_usd=settings.monthly_budget_usd)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)


class AskResponse(BaseModel):
    answer: str
    user_id: str
    history_length: int
    cost_usd: float
    tokens: int


@app.get("/health")
def health(response: Response):
    if lifecycle.shutting_down:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "shutting_down"}
    log_event("health_check_called", level="info")
    return {"status": "ok"}


@app.get("/ready")
def ready(response: Response, store: ConversationStore = Depends(get_store)):
    if lifecycle.shutting_down:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "shutting_down"}

    if not store.ping():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unready", "reason": "redis_unavailable"}

    return {"status": "ready"}


@app.post("/ask", response_model=AskResponse)
def ask(
    req: AskRequest,
    user_id: str = Depends(get_current_user),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
    cost_guard: CostGuard = Depends(get_cost_guard),
    store: ConversationStore = Depends(get_store),
):
    rate_limiter.check(user_id)
    cost_guard.check(user_id)

    # 1. Lấy lịch sử trước khi xử lý câu hỏi mới
    history = store.get_history(user_id)
    initial_history_len = len(history)

    # 2. Gọi mock LLM
    llm_output = ask_llm(req.question, history=history)
    answer = llm_output.get("answer", "")
    cost_usd = float(llm_output.get("cost_usd", 0.001))
    tokens = int(llm_output.get("tokens", len(req.question)))

    # 3. Ghi nhận chi phí
    cost_guard.record(user_id, cost_usd)

    # 4. Ghi nhận cả tin nhắn của user và câu trả lời của assistant vào store
    store.append(user_id, "user", req.question)
    store.append(user_id, "assistant", answer)

    log_event("ask_completed", level="info", user_id=user_id, cost_usd=cost_usd)

    return AskResponse(
        answer=answer,
        user_id=user_id,
        history_length=initial_history_len,
        cost_usd=cost_usd,
        tokens=tokens,
    )