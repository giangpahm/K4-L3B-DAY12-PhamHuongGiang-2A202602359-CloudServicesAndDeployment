from __future__ import annotations

import time
import uuid
from fastapi import HTTPException, status
from redis import Redis

WINDOW_SECONDS = 60


class RateLimiter:
    def __init__(self, client: Redis, limit_per_minute: int = 10):
        self.client = client
        self.limit = limit_per_minute

    def _key(self, user_id: str) -> str:
        return f"rate_limit:{user_id}"

    def hit_count(self, user_id: str, now: float) -> int:
        """Đếm số request của user trong 60 giây gần nhất."""
        key = self._key(user_id)
        window_start = now - WINDOW_SECONDS
        # Xóa các hit cũ hơn 60s
        self.client.zremrangebyscore(key, "-inf", window_start)
        return int(self.client.zcard(key))

    def check(self, user_id: str, now: float | None = None) -> None:
        """Kiểm tra trước, ghi nhận sau; nếu quá hạn mức raise 429."""
        curr_now = now if now is not None else time.time()
        count = self.hit_count(user_id, curr_now)
        if count >= self.limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="rate limit exceeded",
                headers={"Retry-After": str(WINDOW_SECONDS)},
            )

        key = self._key(user_id)
        member = f"{curr_now}:{uuid.uuid4().hex}"
        self.client.zadd(key, {member: curr_now})
        self.client.expire(key, WINDOW_SECONDS)