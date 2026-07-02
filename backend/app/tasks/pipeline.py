from __future__ import annotations

from app.celery_app import celery_app


@celery_app.task(bind=True, name="app.tasks.pipeline.run_pipeline")
def run_pipeline(self, job_id: str) -> dict:
    """Launch a Nextflow pipeline for the given AnalysisJob.

    Placeholder — full implementation in Stage 3 (Nextflow integration).
    """
    return {"job_id": job_id, "status": "queued"}
