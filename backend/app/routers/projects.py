from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import CurrentToken, DB, RequireAnalyst
from app.models.sample import Project
from app.models.user import UserRole
from app.schemas.sample import ProjectCreate, ProjectSchema, ProjectUpdate

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.get("", response_model=list[ProjectSchema])
async def list_projects(token: CurrentToken, db: DB) -> list[Project]:
    stmt = select(Project)
    if not token.is_admin:
        stmt = stmt.where(Project.created_by_id == await _resolve_user_id(token.sub, db))
    result = await db.execute(stmt.order_by(Project.created_at.desc()))
    return list(result.scalars().all())


@router.post("", response_model=ProjectSchema, status_code=status.HTTP_201_CREATED)
async def create_project(token: RequireAnalyst, db: DB, body: ProjectCreate) -> Project:
    user_id = await _resolve_user_id(token.sub, db)
    project = Project(**body.model_dump(), created_by_id=user_id)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectSchema)
async def get_project(project_id: uuid.UUID, token: CurrentToken, db: DB) -> Project:
    project = await _get_or_404(project_id, db)
    _check_access(project, token)
    return project


@router.patch("/{project_id}", response_model=ProjectSchema)
async def update_project(
    project_id: uuid.UUID, token: CurrentToken, db: DB, body: ProjectUpdate
) -> Project:
    project = await _get_or_404(project_id, db)
    _check_access(project, token, require_owner=True)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(project, field, value)
    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: uuid.UUID, token: CurrentToken, db: DB) -> None:
    project = await _get_or_404(project_id, db)
    _check_access(project, token, require_owner=True)
    await db.delete(project)
    await db.commit()


async def _get_or_404(project_id: uuid.UUID, db: DB) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def _check_access(project: Project, token: CurrentToken, require_owner: bool = False) -> None:
    if token.is_admin:
        return
    if require_owner and str(project.created_by_id) != token.sub:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the project owner")


async def _resolve_user_id(keycloak_sub: str, db: DB) -> uuid.UUID:
    from app.models.user import User
    result = await db.execute(select(User.id).where(User.keycloak_id == keycloak_sub))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found — call /api/v1/users/me first")
    return row
