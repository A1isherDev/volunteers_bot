"""Shared async Redis client (optional)."""

from __future__ import annotations

import logging

from app.config import get_settings

logger = logging.getLogger(__name__)

_redis = None


async def get_redis():
    """Returns None if REDIS_URL is not configured."""
    global _redis
    settings = get_settings()
    url = (settings.redis_url or "").strip()
    if not url:
        return None
    if _redis is None:
        import redis.asyncio as redis

        _redis = redis.from_url(url, decode_responses=True)
        logger.info("Redis client initialized")
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
