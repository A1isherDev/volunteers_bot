"""Minimal FastAPI app: health + Redis-backed metrics snapshot."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI

from app.monitoring.metrics import get_counter, pfcount_day

app = FastAPI(title="Volunteers Bot API", version="1.0.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics/summary")
async def metrics_summary() -> dict[str, int | None]:
    """Counters when REDIS_URL is configured."""
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    keys = [
        "news_send_ok",
        "news_send_fail",
        "news_job_fail",
        "news_dlq_processed",
        "failed_news_deliveries",
        "tickets_created",
        f"tickets_day:{day}",
    ]
    out: dict[str, int | None] = {}
    for k in keys:
        out[k.replace("metrics:", "")] = await get_counter(k)
    out["approx_dau_today"] = await pfcount_day(day)
    return out


def create_app() -> FastAPI:
    return app
