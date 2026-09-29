from __future__ import annotations

from datetime import datetime, timezone
from fastapi import HTTPException, status
from redis import Redis

KEY_TTL_SECONDS = 60 * 60 * 24 * 60  # 60 ngày


class CostGuard:
    def __init__(self, client: Redis, monthly_budget_usd: float = 10.0):
        self.client = client
        self.budget = monthly_budget_usd

    @staticmethod
    def _key(user_id: str, month: str | None = None) -> str:
        current_month = month or datetime.now(timezone.utc).strftime("%Y-%m")
        return f"cost:{user_id}:{current_month}"

    def spent(self, user_id: str, month: str | None = None) -> float:
        """Số tiền user đã dùng trong tháng."""
        key = self._key(user_id, month)
        val = self.client.get(key)
        if val is None:
            return 0.0
        return float(val)

    def check(self, user_id: str, estimated_cost: float = 0.0) -> None:
        """Nếu chi phí hiện tại + dự kiến > budget -> raise 402."""
        current_spent = self.spent(user_id)
        if (current_spent + estimated_cost) > self.budget:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="monthly budget exceeded",
            )

    def record(self, user_id: str, cost: float, month: str | None = None) -> float:
        """Cộng dồn chi phí vào Redis và gia hạn TTL."""
        key = self._key(user_id, month)
        total = self.client.incrbyfloat(key, cost)
        self.client.expire(key, KEY_TTL_SECONDS)
        return float(total)