from typing import Any

from aiogram.filters import Filter
from aiogram.types import Message

from app.config import get_settings
from app.database.models import User, UserRole


class IsRegistered(Filter):
    async def __call__(self, _: Any, db_user: User | None = None) -> bool:
        return db_user is not None


class IsAdmin(Filter):
    async def __call__(self, _: Any, db_user: User | None = None) -> bool:
        if not db_user:
            return False
        return db_user.role in (UserRole.admin.value, UserRole.super_admin.value)


class IsSuperAdmin(Filter):
    async def __call__(self, _: Any, db_user: User | None = None) -> bool:
        if not db_user:
            return False
        s = get_settings()
        if db_user.telegram_id in s.parsed_super_admin_ids():
            return True
        return db_user.role == UserRole.super_admin.value


class InAdminGroup(Filter):
    async def __call__(self, message: Message) -> bool:
        s = get_settings()
        return message.chat is not None and message.chat.id == s.admin_group_id
