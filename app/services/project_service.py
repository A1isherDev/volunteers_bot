from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Project
from app.repositories.project_repository import ProjectRepository


class ProjectService:
    def __init__(self, session: AsyncSession):
        self._repo = ProjectRepository(session)

    async def list_active(self) -> list[Project]:
        return await self._repo.list_active()

    async def get(self, project_id: int) -> Project | None:
        return await self._repo.get(project_id)

    async def create(self, title: str, description: str, *, sort_order: int = 0) -> Project:
        return await self._repo.create(title, description, sort_order=sort_order)
