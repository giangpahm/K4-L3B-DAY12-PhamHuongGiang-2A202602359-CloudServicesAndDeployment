from __future__ import annotations

import signal
from typing import Any


class Lifecycle:
    """Quản lý trạng thái dừng tiến trình và bắt tín hiệu SIGTERM / SIGINT."""

    def __init__(self):
        self.shutting_down: bool = False
        self._old_handlers: dict[int, Any] = {}

    @property
    def is_shutting_down(self) -> bool:
        return self.shutting_down

    def request_shutdown(self, signum: int | None = None, frame: Any = None) -> None:
        """Bật cờ báo tắt và chuyển tiếp tín hiệu cho handler cũ nếu có."""
        self.shutting_down = True
        if signum is not None and signum in self._old_handlers:
            old_handler = self._old_handlers[signum]
            if callable(old_handler):
                old_handler(signum, frame)

    def install(self) -> None:
        """Đăng ký chính phương thức self.request_shutdown làm handler."""
        for sig in (signal.SIGTERM, signal.SIGINT):
            self._old_handlers[sig] = signal.getsignal(sig)
            signal.signal(sig, self.request_shutdown)


lifecycle = Lifecycle()