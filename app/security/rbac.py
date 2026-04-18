from __future__ import annotations

from enum import Enum

from app.config import get_settings
from app.database.models import User, UserRole


class Permission(str, Enum):
    """Coarse permissions mapped from roles + env lists."""

    user_basic = "user_basic"
    volunteer = "volunteer"
    admin_panel = "admin_panel"
    super_admin = "super_admin"


def role_grants(telegram_id: int, user: User | None) -> set[Permission]:
    s = get_settings()
    grants: set[Permission] = {Permission.user_basic}
    if user:
        if user.role == UserRole.volunteer.value:
            grants.add(Permission.volunteer)
        if user.role in (UserRole.admin.value, UserRole.super_admin.value):
            grants.add(Permission.admin_panel)
            grants.add(Permission.volunteer)
        if user.role == UserRole.super_admin.value:
            grants.add(Permission.super_admin)
    if s.is_env_privileged_user(telegram_id):
        grants.add(Permission.admin_panel)
        if telegram_id in s.parsed_super_admin_ids():
            grants.add(Permission.super_admin)
    return grants


def has_permission(telegram_id: int, user: User | None, perm: Permission) -> bool:
    return perm in role_grants(telegram_id, user)


def has_any_role_db(user: User | None, *roles: str) -> bool:
    if not user:
        return False
    return user.role in roles
