"""Admin-side helpers (permissions checks can grow here)."""

from __future__ import annotations

from app.database.models import User, UserRole


def is_bot_admin(user: User | None) -> bool:
    if not user:
        return False
    return user.role in (UserRole.admin.value, UserRole.super_admin.value)
