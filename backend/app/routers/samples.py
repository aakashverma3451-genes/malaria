from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import CurrentToken, DB, RequireAnalyst
from app.models.sample import Project, Sample
from app.schemas.sample import SampleCreate, SampleSchema

router = APIRouter(prefix="/api/v1/samples", tags=["samples"])


@router.get("", response_model=list[SampleSchema])
async def list_samples(
    token: CurrentToken, db: DB, project_id: uuid.UUID | None = None
) -> list[Sample]:
    stmt = select(Sample)
    if project_id:
        stmt = stmt.where(Sample.project_id == project_id)
    if not token.is_admin:
        stmt = stmt.join(Project).where(Project.created_by_id == await _user_id(token.sub, db))
    result = await db.execute(stmt.order_by(Sample.created_at.desc()))
    return list(result.scalars().all())


@router.post("", response_model=SampleSchema, status_code=status.HTTP_201_CREATED)
async def create_sample(token: RequireAnalyst, db: DB, body: SampleCreate) -> Sample:
    user_id = await _user_id(token.sub, db)
    data = body.model_dump(by_alias=False)
    data["created_by_id"] = user_id
    sample = Sample(**data)
    db.add(sample)
    await db.commit()
    await db.refresh(sample)
    return sample


@router.get("/{sample_id}", response_model=SampleSchema)
async def get_sample(sample_id: uuid.UUID, token: CurrentToken, db: DB) -> Sample:
    sample = await _get_or_404(sample_id, db)
    return sample


@router.delete("/{sample_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_sample(sample_id: uuid.UUID, _: CurrentToken, db: DB) -> None:
    sample = await _get_or_404(sample_id, db)
    await db.delete(sample)
    await db.commit()


async def _get_or_404(sample_id: uuid.UUID, db: DB) -> Sample:
    result = await db.execute(select(Sample).where(Sample.id == sample_id))
    sample = result.scalar_one_or_none()
    if sample is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")
    return sample


async def _user_id(keycloak_sub: str, db: DB) -> uuid.UUID:
    from app.models.user import User
    result = await db.execute(select(User.id).where(User.keycloak_id == keycloak_sub))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return row
