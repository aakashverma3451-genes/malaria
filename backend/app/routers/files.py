from __future__ import annotations

import uuid
from datetime import timedelta

from fastapi import APIRouter, HTTPException, status
from minio import Minio
from sqlalchemy import select

from app.config import settings
from app.dependencies import CurrentToken, DB, RequireAnalyst
from app.models.sample import RawFile, Sample, UploadStatus
from app.schemas.sample import PresignedUploadResponse, RawFileInitUpload, RawFileSchema

router = APIRouter(prefix="/api/v1/files", tags=["files"])


def _minio_client() -> Minio:
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )


@router.post("/init-upload", response_model=PresignedUploadResponse, status_code=status.HTTP_201_CREATED)
async def init_upload(token: RequireAnalyst, db: DB, body: RawFileInitUpload) -> PresignedUploadResponse:
    result = await db.execute(select(Sample).where(Sample.id == body.sample_id))
    sample = result.scalar_one_or_none()
    if sample is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")

    from app.models.user import User
    user_result = await db.execute(select(User.id).where(User.keycloak_id == token.sub))
    user_id = user_result.scalar_one_or_none()
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    object_key = f"raw/{sample.project_id}/{body.sample_id}/{body.original_filename}"

    raw_file = RawFile(
        sample_id=body.sample_id,
        sequencing_run_id=body.sequencing_run_id,
        minio_object_key=object_key,
        original_filename=body.original_filename,
        file_type=body.file_type,
        file_size_bytes=body.file_size_bytes,
        uploaded_by_id=user_id,
        upload_status=UploadStatus.UPLOADING,
    )
    db.add(raw_file)
    await db.commit()
    await db.refresh(raw_file)

    client = _minio_client()
    presigned_url = client.presigned_put_object(
        settings.MINIO_BUCKET,
        object_key,
        expires=timedelta(hours=2),
    )

    return PresignedUploadResponse(
        file_id=raw_file.id,
        presigned_url=presigned_url,
        object_key=object_key,
    )


@router.post("/{file_id}/confirm", response_model=RawFileSchema)
async def confirm_upload(file_id: uuid.UUID, _: RequireAnalyst, db: DB) -> RawFile:
    result = await db.execute(select(RawFile).where(RawFile.id == file_id))
    raw_file = result.scalar_one_or_none()
    if raw_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    client = _minio_client()
    try:
        stat = client.stat_object(settings.MINIO_BUCKET, raw_file.minio_object_key)
        raw_file.file_size_bytes = stat.size or raw_file.file_size_bytes
        raw_file.upload_status = UploadStatus.COMPLETED
    except Exception:
        raw_file.upload_status = UploadStatus.FAILED
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File not found in storage")

    await db.commit()
    await db.refresh(raw_file)
    return raw_file


@router.get("/{file_id}/download-url")
async def download_url(file_id: uuid.UUID, _: CurrentToken, db: DB) -> dict:
    result = await db.execute(select(RawFile).where(RawFile.id == file_id))
    raw_file = result.scalar_one_or_none()
    if raw_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    client = _minio_client()
    url = client.presigned_get_object(
        settings.MINIO_BUCKET,
        raw_file.minio_object_key,
        expires=timedelta(hours=1),
    )
    return {"url": url, "expires_in_seconds": 3600}


@router.get("", response_model=list[RawFileSchema])
async def list_files(
    _: CurrentToken, db: DB, sample_id: uuid.UUID | None = None
) -> list[RawFile]:
    stmt = select(RawFile)
    if sample_id:
        stmt = stmt.where(RawFile.sample_id == sample_id)
    result = await db.execute(stmt.order_by(RawFile.uploaded_at.desc()))
    return list(result.scalars().all())
