"""One-time data defaults after schema is created (no hardcoded user-facing options)."""

from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import FAQCategory

logger = logging.getLogger(__name__)


async def bootstrap_defaults(session: AsyncSession) -> None:
    """Ensure at least one FAQ category exists so admin can attach FAQs."""
    n = await session.scalar(select(func.count()).select_from(FAQCategory))
    if n == 0:
        session.add(
            FAQCategory(
                name_uz="Umumiy",
                name_ru="Общее",
                is_active=True,
                sort_order=0,
            )
        )
        await session.flush()
        logger.info("Bootstrap: created default FAQ category")
