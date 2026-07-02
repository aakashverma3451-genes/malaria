from __future__ import annotations

from app.celery_app import celery_app


@celery_app.task(name="app.tasks.maintenance.cleanup_expired_uploads")
def cleanup_expired_uploads() -> dict:
    """Remove stale MinIO objects and RawFile records for failed uploads > 24h old.

    Placeholder — full implementation in Stage 4 (file upload).
    """
    return {"cleaned": 0}
