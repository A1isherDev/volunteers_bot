from __future__ import annotations

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import FAQ


class FAQService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all_ordered(self) -> list[FAQ]:
        r = await self.session.execute(select(FAQ).order_by(FAQ.sort_order, FAQ.id))
        return list(r.scalars().all())

    async def get(self, faq_id: int) -> FAQ | None:
        r = await self.session.execute(select(FAQ).where(FAQ.id == faq_id))
        return r.scalar_one_or_none()

    async def create(
        self,
        question_uz: str,
        answer_uz: str,
        question_ru: str | None,
        answer_ru: str | None,
    ) -> FAQ:
        max_sort = await self.session.scalar(select(func.max(FAQ.sort_order)))
        nxt = (max_sort or 0) + 1
        f = FAQ(
            sort_order=nxt,
            question_uz=question_uz,
            answer_uz=answer_uz,
            question_ru=question_ru,
            answer_ru=answer_ru,
        )
        self.session.add(f)
        await self.session.flush()
        return f

    async def update_qa(
        self,
        faq_id: int,
        *,
        question_uz: str | None = None,
        answer_uz: str | None = None,
        question_ru: str | None = None,
        answer_ru: str | None = None,
    ) -> bool:
        f = await self.get(faq_id)
        if not f:
            return False
        if question_uz is not None:
            f.question_uz = question_uz
        if answer_uz is not None:
            f.answer_uz = answer_uz
        if question_ru is not None:
            f.question_ru = question_ru
        if answer_ru is not None:
            f.answer_ru = answer_ru
        await self.session.flush()
        return True

    async def delete(self, faq_id: int) -> bool:
        r = await self.session.execute(delete(FAQ).where(FAQ.id == faq_id))
        return r.rowcount > 0
