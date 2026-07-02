from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import CurrentToken, DB, RequireAnalyst
from app.models.workflow import AnalysisJob, AnalysisJobSample, JobStatus
from app.schemas.workflow import AnalysisJobSchema, JobSubmit

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get("", response_model=list[AnalysisJobSchema])
async def list_jobs(token: CurrentToken, db: DB) -> list[AnalysisJob]:
    stmt = select(AnalysisJob)
    if not token.is_admin:
        user_id = await _user_id(token.sub, db)
        stmt = stmt.where(AnalysisJob.submitted_by_id == user_id)
    result = await db.execute(stmt.order_by(AnalysisJob.submitted_at.desc()))
    return list(result.scalars().all())


@router.post("/submit", response_model=AnalysisJobSchema, status_code=status.HTTP_201_CREATED)
async def submit_job(token: RequireAnalyst, db: DB, body: JobSubmit) -> AnalysisJob:
    user_id = await _user_id(token.sub, db)

    job = AnalysisJob(
        name=body.name,
        workflow_type=body.workflow_type,
        parameters=body.parameters,
        submitted_by_id=user_id,
    )
    db.add(job)
    await db.flush()

    for i, sample_id in enumerate(body.sample_ids):
        db.add(AnalysisJobSample(job_id=job.id, sample_id=sample_id, order=i))

    await db.commit()
    await db.refresh(job)

    # Dispatch Celery task
    try:
        from app.tasks.pipeline import run_pipeline
        task = run_pipeline.delay(str(job.id))
        job.celery_task_id = task.id
        job.status = JobStatus.QUEUED
        await db.commit()
    except Exception:
        pass  # Celery unavailable in dev — job stays PENDING

    return job


@router.get("/{job_id}", response_model=AnalysisJobSchema)
async def get_job(job_id: uuid.UUID, token: CurrentToken, db: DB) -> AnalysisJob:
    job = await _get_or_404(job_id, db)
    if not token.is_admin:
        user_id = await _user_id(token.sub, db)
        if job.submitted_by_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return job


@router.post("/{job_id}/cancel", response_model=AnalysisJobSchema)
async def cancel_job(job_id: uuid.UUID, token: CurrentToken, db: DB) -> AnalysisJob:
    job = await _get_or_404(job_id, db)
    if job.status not in (JobStatus.PENDING, JobStatus.QUEUED, JobStatus.RUNNING):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job cannot be cancelled")
    job.status = JobStatus.CANCELLED
    await db.commit()
    await db.refresh(job)
    return job


async def _get_or_404(job_id: uuid.UUID, db: DB) -> AnalysisJob:
    result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


async def _user_id(keycloak_sub: str, db: DB) -> uuid.UUID:
    from app.models.user import User
    result = await db.execute(select(User.id).where(User.keycloak_id == keycloak_sub))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return row
