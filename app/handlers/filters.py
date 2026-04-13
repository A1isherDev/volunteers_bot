from aiogram.filters import Filter
from aiogram.types import Message

from app.config import get_settings
from app.database.models import UserRole


class IsRegistered(Filter):
    async def __call__(self, _, data: dict) -> bool:
        return data.get("db_user") is not None


class IsAdmin(Filter):
    async def __call__(self, _, data: dict) -> bool:
        u = data.get("db_user")
        if not u:
            return False
        return u.role in (UserRole.admin.value, UserRole.super_admin.value)


class IsSuperAdmin(Filter):
    async def __call__(self, _, data: dict) -> bool:
        u = data.get("db_user")
        if not u:
            return False
        s = get_settings()
        if u.telegram_id in s.parsed_super_admin_ids():
            return True
        return u.role == UserRole.super_admin.value


class InAdminGroup(Filter):
    async def __call__(self, message: Message) -> bool:
        s = get_settings()
        return message.chat is not None and message.chat.id == s.admin_group_id
