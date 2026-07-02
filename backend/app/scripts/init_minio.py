"""Run once after first `docker compose up` to create the MinIO bucket."""
from __future__ import annotations

from minio import Minio
from minio.error import S3Error

from app.config import settings


def main() -> None:
    client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )
    if not client.bucket_exists(settings.MINIO_BUCKET):
        client.make_bucket(settings.MINIO_BUCKET)
        print(f"Created bucket: {settings.MINIO_BUCKET}")
    else:
        print(f"Bucket already exists: {settings.MINIO_BUCKET}")


if __name__ == "__main__":
    main()
