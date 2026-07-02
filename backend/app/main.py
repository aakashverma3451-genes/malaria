from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.routers import files, health, jobs, projects, results, samples, users

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Malaria Genomics Platform",
    version="0.1.0",
    description="Genomic surveillance platform for malaria parasites and mosquito vectors.",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    import logging
    import traceback

    if settings.DEBUG:
        logging.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}},
    )


# Routers
app.include_router(health.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(samples.router)
app.include_router(files.router)
app.include_router(jobs.router)
app.include_router(results.router)
