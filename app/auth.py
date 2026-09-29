from __future__ import annotations

import secrets
from fastapi import Header, HTTPException, status
from app.config import get_settings

ANONYMOUS_USER = "anonymous"


def get_current_user(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> str:
    """Xác thực API key bằng secrets.compare_digest và trả về user_id."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )

    settings = get_settings()
    if not secrets.compare_digest(x_api_key, settings.agent_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return x_user_id if (x_user_id and x_user_id.strip()) else ANONYMOUS_USER