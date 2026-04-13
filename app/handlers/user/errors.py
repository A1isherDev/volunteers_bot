import logging

from aiogram import Router
from aiogram.types import ErrorEvent

logger = logging.getLogger(__name__)
router = Router(name="errors")


@router.errors()
async def global_error(event: ErrorEvent) -> bool:
    logger.exception(
        "Update caused error: update_id=%s exc=%s",
        getattr(event.update, "update_id", None),
        event.exception,
        exc_info=event.exception,
    )
    return True
