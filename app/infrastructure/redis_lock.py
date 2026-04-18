"""Distributed locks for multi-worker workers (SET NX EX)."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def redis_lock(key: str, *, ttl_sec: int = 120) -> AsyncIterator[bool]:
    """Yields True if lock acquired. If Redis is down, yields True (best-effort)."""
    from app.infrastructure.redis_connection import get_redis

    r = await get_redis()
    if r is None:
        yield True
        return
    acquired = bool(await r.set(key, "1", nx=True, ex=ttl_sec))
    try:
        yield acquired
    finally:
        if acquired:
            try:
                await r.delete(key)
            except Exception as e:
                logger.debug("lock release %s: %s", key, e)
