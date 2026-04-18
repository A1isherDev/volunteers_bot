from __future__ import annotations

import logging
import time
import uuid

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.config import get_settings
from app.i18n import t

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    """Sliding-window rate limit via Redis only (multi-worker safe)."""

    async def _allow(self, uid: int, limit: int, window: float) -> bool:
        try:
            from app.infrastructure.redis_connection import get_redis

            r = await get_redis()
            if r is None:
                logger.error("Rate limit: Redis unavailable; blocking request")
                return False
            now = time.time()
            key = f"rl:sliding:{uid}"
            await r.zremrangebyscore(key, 0, now - window)
            n = await r.zcard(key)
            if n >= limit:
                return False
            await r.zadd(key, {f"{uuid.uuid4().hex}": now})
            await r.expire(key, int(window) + 5)
            return True
        except Exception as e:
            logger.exception("Rate limit Redis error: %s", e)
            return False

    async def __call__(self, handler, event: TelegramObject, data: dict):
        settings = get_settings()
        uid = None
        lang = "uz"
        if isinstance(event, Message) and event.from_user:
            if event.chat.type != "private":
                return await handler(event, data)
            uid = event.from_user.id
            lang = getattr(data.get("db_user"), "language", None) or "uz"
        elif isinstance(event, CallbackQuery) and event.from_user:
            msg = event.message
            if msg is None or msg.chat.type != "private":
                return await handler(event, data)
            uid = event.from_user.id
            lang = getattr(data.get("db_user"), "language", None) or "uz"
        if uid is None:
            return await handler(event, data)

        window = float(settings.rate_limit_window_sec)
        limit = settings.rate_limit_messages
        if not await self._allow(uid, limit, window):
            if isinstance(event, Message):
                await event.answer(t(lang, "errors.rate_limited"))
            elif isinstance(event, CallbackQuery):
                await event.answer(t(lang, "errors.rate_limited"), show_alert=True)
            return None
        return await handler(event, data)
