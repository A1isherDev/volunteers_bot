from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.services.user_service import UserService


class UserContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ):
        session = data.get("session")
        if session is None:
            return await handler(event, data)

        user = None
        tg_user = None
        if isinstance(event, Message):
            tg_user = event.from_user
        elif isinstance(event, CallbackQuery):
            tg_user = event.from_user

        if tg_user is not None:
            svc = UserService(session)
            db_user = await svc.get_by_telegram_id(tg_user.id)
            if db_user:
                db_user = await svc.ensure_env_roles(db_user)
                await svc.touch_activity(tg_user.id, username=tg_user.username)
                await session.refresh(db_user)
            data["db_user"] = db_user
            data["tg_user"] = tg_user
        else:
            data["db_user"] = None
            data["tg_user"] = None

        return await handler(event, data)
