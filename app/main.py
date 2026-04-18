from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from app.config import get_settings
from app.database.session import init_db
from app.handlers import register_handlers
from app.logging_config import init_sentry_if_configured, setup_logging
from app.middlewares.db_session import DbSessionMiddleware
from app.middlewares.rbac_context import RbacContextMiddleware
from app.middlewares.rate_limit import RateLimitMiddleware
from app.middlewares.user_context import UserContextMiddleware
from app.integrations.sheets_outbox import worker_loop as sheets_outbox_worker
from app.services.news_dispatch_service import dlq_worker_loop, news_worker_loop


async def main() -> None:
    settings = get_settings()
    setup_logging(json_logs=settings.json_logs, level=settings.log_level)
    init_sentry_if_configured()
    await init_db()

    bot = Bot(
        settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=RedisStorage.from_url(settings.redis_url))

    dp.update.middleware(DbSessionMiddleware())
    dp.update.middleware(UserContextMiddleware())
    dp.update.middleware(RbacContextMiddleware())
    dp.update.middleware(RateLimitMiddleware())

    register_handlers(dp)

    asyncio.create_task(news_worker_loop(bot))
    asyncio.create_task(dlq_worker_loop(bot))
    asyncio.create_task(sheets_outbox_worker())

    logging.getLogger(__name__).info("Bot starting polling…")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
