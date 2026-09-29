from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    agent_api_key: str = Field(..., description="API key bảo vệ agent")

    port: int = Field(default=8000, description="Cổng lắng nghe")
    redis_url: str = Field(default="redis://localhost:6379/0", description="URL Redis")
    rate_limit_per_minute: int = Field(default=10, description="Giới hạn request/phút")
    monthly_budget_usd: float = Field(default=10.0, description="Ngân sách tháng")
    log_level: str = Field(default="info", description="Mức log")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


try:
    settings = get_settings()
except Exception:
    settings = None