from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = Field(..., validation_alias="BOT_TOKEN")
    admin_ids: str = Field(default="", validation_alias="ADMIN_IDS")
    super_admin_ids: str = Field(default="", validation_alias="SUPER_ADMIN_IDS")
    admin_group_id: int = Field(..., validation_alias="ADMIN_GROUP_ID")

    # Apply schema with: alembic upgrade head (see migrations/versions/0001_initial_schema.py)
    database_url: str = Field(
        default="sqlite+aiosqlite:///./volunteers_bot.db",
        validation_alias="DATABASE_URL",
    )

    # Required for FSM, rate limits, metrics, news queue (multi-worker safe).
    redis_url: str = Field(..., min_length=1, validation_alias="REDIS_URL")
    news_queue_key: str = Field(default="volunteers_bot:news_queue", validation_alias="NEWS_QUEUE_KEY")
    news_dlq_key: str = Field(default="volunteers_bot:news_dlq", validation_alias="NEWS_DLQ_KEY")
    fsm_redis_key_prefix: str = Field(default="fsm", validation_alias="FSM_REDIS_KEY_PREFIX")

    admin_ticket_topic_id: int | None = Field(default=None, validation_alias="ADMIN_TICKET_TOPIC_ID")

    broadcast_batch_size: int = Field(default=25, validation_alias="BROADCAST_BATCH_SIZE")
    broadcast_delay_sec: float = Field(default=0.05, validation_alias="BROADCAST_DELAY_SEC")
    news_messages_per_sec: float = Field(default=25.0, validation_alias="NEWS_MESSAGES_PER_SEC")
    news_max_retries: int = Field(default=3, validation_alias="NEWS_MAX_RETRIES")
    news_retry_base_delay_sec: float = Field(default=0.5, validation_alias="NEWS_RETRY_BASE_DELAY_SEC")

    rate_limit_messages: int = Field(default=20, validation_alias="RATE_LIMIT_MESSAGES")
    rate_limit_window_sec: int = Field(default=60, validation_alias="RATE_LIMIT_WINDOW_SEC")

    creation_cooldown_sec: float = Field(default=45.0, validation_alias="CREATION_COOLDOWN_SEC")

    json_logs: bool = Field(default=False, validation_alias="JSON_LOGS")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    sentry_dsn: str = Field(default="", validation_alias="SENTRY_DSN")

    google_credentials_path: str = Field(default="", validation_alias="GOOGLE_CREDENTIALS_PATH")
    google_sheet_id: str = Field(default="", validation_alias="GOOGLE_SHEET_ID")

    api_host: str = Field(default="127.0.0.1", validation_alias="API_HOST")
    api_port: int = Field(default=8080, validation_alias="API_PORT")
    api_enable: bool = Field(default=False, validation_alias="API_ENABLE")

    @field_validator("admin_group_id", mode="before")
    @classmethod
    def parse_admin_group(cls, v):
        if v is None or v == "":
            raise ValueError("ADMIN_GROUP_ID is required")
        return int(v)

    @field_validator("admin_ticket_topic_id", mode="before")
    @classmethod
    def parse_admin_ticket_topic(cls, v):
        if v is None or v == "":
            return None
        return int(v)

    def parsed_admin_ids(self) -> set[int]:
        return self._parse_id_set(self.admin_ids)

    def parsed_super_admin_ids(self) -> set[int]:
        base = self._parse_id_set(self.super_admin_ids)
        if not base:
            base = self._parse_id_set(self.admin_ids)
        return base

    def is_env_privileged_user(self, telegram_id: int) -> bool:
        return telegram_id in self.parsed_admin_ids() or telegram_id in self.parsed_super_admin_ids()

    @staticmethod
    def _parse_id_set(raw: str) -> set[int]:
        if not raw or not raw.strip():
            return set()
        out: set[int] = set()
        for part in raw.split(","):
            part = part.strip()
            if part:
                out.add(int(part))
        return out


@lru_cache
def get_settings() -> Settings:
    return Settings()
