from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database.models import User, UserRole


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _env_roles(self, telegram_id: int) -> str:
        s = get_settings()
        if telegram_id in s.parsed_super_admin_ids():
            return UserRole.super_admin.value
        if telegram_id in s.parsed_admin_ids():
            return UserRole.admin.value
        return UserRole.user.value

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        r = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return r.scalar_one_or_none()

    async def touch_activity(self, telegram_id: int, username: str | None = None) -> None:
        vals = {"last_active_at": datetime.now(timezone.utc)}
        if username is not None:
            vals["username"] = username
        await self.session.execute(update(User).where(User.telegram_id == telegram_id).values(**vals))

    async def ensure_env_roles(self, user: User) -> User:
        env_role = self._env_roles(user.telegram_id)
        order = {UserRole.user.value: 0, UserRole.admin.value: 1, UserRole.super_admin.value: 2}
        if order.get(env_role, 0) > order.get(user.role, 0):
            user.role = env_role
            await self.session.flush()
        return user

    async def create_user(
        self,
        telegram_id: int,
        full_name: str,
        phone: str,
        region: str,
        age: int | None,
        language: str = "uz",
        username: str | None = None,
    ) -> User:
        role = self._env_roles(telegram_id)
        u = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            phone=phone,
            region=region,
            age=age,
            role=role,
            language=language,
        )
        self.session.add(u)
        await self.session.flush()
        return u

    async def set_language(self, telegram_id: int, lang: str) -> None:
        await self.session.execute(
            update(User).where(User.telegram_id == telegram_id).values(language=lang)
        )

    async def count_users(self) -> int:
        r = await self.session.execute(select(func.count()).select_from(User))
        return int(r.scalar_one())

    async def count_active_users(self, days: int = 7) -> int:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        r = await self.session.execute(select(func.count()).select_from(User).where(User.last_active_at >= since))
        return int(r.scalar_one())

    async def list_users_page(
        self,
        page: int = 1,
        per_page: int = 8,
        query: str | None = None,
    ) -> tuple[list[User], int]:
        filters = []
        if query and query.strip():
            term = f"%{query.strip().lower()}%"
            filters.append(
                or_(
                    func.lower(User.full_name).like(term),
                    func.lower(User.phone).like(term),
                    func.lower(User.region).like(term),
                    func.lower(func.coalesce(User.username, "")).like(term),
                )
            )
        count_stmt = select(func.count()).select_from(User)
        if filters:
            count_stmt = count_stmt.where(*filters)
        total = int((await self.session.execute(count_stmt)).scalar_one())
        pages = max(1, (total + per_page - 1) // per_page)
        page = max(1, min(page, pages))
        offset = (page - 1) * per_page
        stmt = select(User).order_by(User.registered_at.desc())
        if filters:
            stmt = stmt.where(*filters)
        r = await self.session.execute(stmt.offset(offset).limit(per_page))
        return list(r.scalars().all()), pages

    async def set_role(self, telegram_id: int, role: str) -> bool:
        u = await self.get_by_telegram_id(telegram_id)
        if not u:
            return False
        u.role = role
        await self.session.flush()
        return True

    async def all_telegram_ids(self) -> list[int]:
        r = await self.session.execute(select(User.telegram_id))
        return [row[0] for row in r.all()]
