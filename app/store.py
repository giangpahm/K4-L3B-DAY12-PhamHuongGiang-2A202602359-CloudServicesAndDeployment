from __future__ import annotations

import json
from redis import Redis

HISTORY_MAX_MESSAGES = 10
HISTORY_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 ngày


def get_redis_client(url: str = "redis://localhost:6379/0") -> Redis:
    """Tạo client Redis. Nếu URL bắt đầu bằng fake:// thì trả về FakeRedis."""
    if url.startswith("fake://"):
        import fakeredis
        return fakeredis.FakeRedis(decode_responses=True)
    return Redis.from_url(url, decode_responses=True)


class ConversationStore:
    """Lưu lịch sử hội thoại vào Redis để đảm bảo ứng dụng stateless."""

    def __init__(
        self,
        client: Redis,
        ttl_seconds: int = HISTORY_TTL_SECONDS,
        max_messages: int = HISTORY_MAX_MESSAGES,
    ):
        self.client = client
        self.ttl_seconds = ttl_seconds
        self.max_messages = max_messages

    @staticmethod
    def _key(user_id: str) -> str:
        return f"history:{user_id}"

    def get_history(self, user_id: str) -> list[dict]:
        """Đọc danh sách tin nhắn của user từ Redis."""
        key = self._key(user_id)
        raw_items = self.client.lrange(key, 0, -1)
        if not raw_items:
            return []
        history = []
        for item in raw_items:
            if isinstance(item, bytes):
                item = item.decode("utf-8")
            history.append(json.loads(item))
        return history

    def append(self, user_id: str, role: str, content: str) -> None:
        """Ghi nhận tin nhắn mới và cắt bớt nếu vượt HISTORY_MAX_MESSAGES."""
        key = self._key(user_id)
        message = {"role": role, "content": content}
        serialized = json.dumps(message, ensure_ascii=False)
        self.client.rpush(key, serialized)

        if self.max_messages and self.max_messages > 0:
            self.client.ltrim(key, -self.max_messages, -1)

        self.client.expire(key, self.ttl_seconds)

    def ping(self) -> bool:
        """Kiểm tra Redis còn sống, không bao giờ raise exception."""
        try:
            return bool(self.client.ping())
        except Exception:
            return False