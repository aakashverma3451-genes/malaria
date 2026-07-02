from __future__ import annotations

import time
from datetime import datetime, timezone

import redis.asyncio as aioredis
from fastapi import APIRouter
from sqlalchemy import text

from app.config import settings
from app.database import AsyncSessionLocal

router = APIRouter(tags=["health"])

VERSION = "0.1.0"


@router.get("/health", include_in_schema=False)
@router.get("/api/v1/health")
async def health_check() -> dict:
    checks: dict[str, dict] = {}
    overall = "healthy"

    # Database
    t0 = time.monotonic()
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = {"status": "up", "latency_ms": round((time.monotonic() - t0) * 1000, 1)}
    except Exception as exc:
        checks["database"] = {"status": "down", "error": str(exc)}
        overall = "unhealthy"

    # Redis
    t0 = time.monotonic()
    try:
        r = aioredis.from_url(settings.REDIS_URL, socket_timeout=2)
        await r.ping()
        await r.aclose()
        checks["redis"] = {"status": "up", "latency_ms": round((time.monotonic() - t0) * 1000, 1)}
    except Exception as exc:
        checks["redis"] = {"status": "down", "error": str(exc)}
        if overall == "healthy":
            overall = "degraded"

    return {
        "status": overall,
        "version": VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }
