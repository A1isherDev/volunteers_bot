from collections import defaultdict, deque
from time import monotonic

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.config import get_settings
from app.i18n import t


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self._hits: dict[int, deque[float]] = defaultdict(deque)

    def _prune(self, uid: int, window: float) -> None:
        dq = self._hits[uid]
        now = monotonic()
        while dq and now - dq[0] > window:
            dq.popleft()

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
        self._prune(uid, window)
        dq = self._hits[uid]
        if len(dq) >= limit:
            if isinstance(event, Message):
                await event.answer(t(lang, "errors.rate_limited"))
            elif isinstance(event, CallbackQuery):
                await event.answer(t(lang, "errors.rate_limited"), show_alert=True)
            return None
        dq.append(monotonic())
        return await handler(event, data)
