from __future__ import annotations

import uuid
from datetime import timedelta

from fastapi import APIRouter, HTTPException, status
from minio import Minio
from sqlalchemy import select

from app.config import settings
from app.dependencies import CurrentToken, DB
from app.models.workflow import Result
from app.schemas.workflow import ResultSchema

router = APIRouter(prefix="/api/v1/results", tags=["results"])


@router.get("", response_model=list[ResultSchema])
async def list_results(_: CurrentToken, db: DB, job_id: uuid.UUID | None = None) -> list[Result]:
    stmt = select(Result)
    if job_id:
        stmt = stmt.where(Result.job_id == job_id)
    result = await db.execute(stmt.order_by(Result.created_at.desc()))
    return list(result.scalars().all())


@router.get("/{result_id}/download-url")
async def get_download_url(result_id: uuid.UUID, _: CurrentToken, db: DB) -> dict:
    result = await db.execute(select(Result).where(Result.id == result_id))
    r = result.scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found")
    if not r.minio_object_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No file for this result")

    client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )
    url = client.presigned_get_object(
        settings.MINIO_BUCKET, r.minio_object_key, expires=timedelta(hours=1)
    )
    return {"url": url, "expires_in_seconds": 3600}
