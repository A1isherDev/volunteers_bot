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

    database_url: str = Field(
        default="sqlite+aiosqlite:///./volunteers_bot.db",
        validation_alias="DATABASE_URL",
    )

    broadcast_batch_size: int = Field(default=25, validation_alias="BROADCAST_BATCH_SIZE")
    broadcast_delay_sec: float = Field(default=0.05, validation_alias="BROADCAST_DELAY_SEC")

    rate_limit_messages: int = Field(default=20, validation_alias="RATE_LIMIT_MESSAGES")
    rate_limit_window_sec: int = Field(default=60, validation_alias="RATE_LIMIT_WINDOW_SEC")

    # Min seconds between new support tickets / suggestions per user (0 = off)
    creation_cooldown_sec: float = Field(default=45.0, validation_alias="CREATION_COOLDOWN_SEC")

    @field_validator("admin_group_id", mode="before")
    @classmethod
    def parse_admin_group(cls, v):
        if v is None or v == "":
            raise ValueError("ADMIN_GROUP_ID is required")
        return int(v)

    def parsed_admin_ids(self) -> set[int]:
        return self._parse_id_set(self.admin_ids)

    def parsed_super_admin_ids(self) -> set[int]:
        base = self._parse_id_set(self.super_admin_ids)
        if not base:
            base = self._parse_id_set(self.admin_ids)
        return base

    def is_env_privileged_user(self, telegram_id: int) -> bool:
        """True if this Telegram id is listed in ADMIN_IDS or SUPER_ADMIN_IDS (env bootstrap)."""
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
