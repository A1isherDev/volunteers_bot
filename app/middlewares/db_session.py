import logging

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.database.session import get_session_factory

logger = logging.getLogger(__name__)


class DbSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        factory = get_session_factory()
        after_commit: list = []
        data["session"] = None  # set below; keeps key for type checkers
        data["after_commit_tasks"] = after_commit
        async with factory() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                for task in after_commit:
                    await task
                return result
            except Exception:
                await session.rollback()
                logger.exception("Rolling back DB session after error")
                raise
