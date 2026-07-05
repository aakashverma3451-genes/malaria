from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.dependencies import CurrentToken, DB, RequireAdmin
from app.models.user import User, UserProfile
from app.schemas.user import UserSchema, UserUpdateSchema

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserSchema)
async def get_me(token: CurrentToken, db: DB) -> User:
    result = await db.execute(
        select(User).options(selectinload(User.profile)).where(User.keycloak_id == token.sub)
    )
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            keycloak_id=token.sub,
            email=token.email,
            first_name="",
            last_name="",
        )
        db.add(user)
        await db.flush()
        db.add(UserProfile(user_id=user.id))
        await db.commit()
        await db.refresh(user, attribute_names=["profile"])
    return user


@router.put("/me", response_model=UserSchema)
async def update_me(token: CurrentToken, db: DB, body: UserUpdateSchema) -> User:
    result = await db.execute(
        select(User).options(selectinload(User.profile)).where(User.keycloak_id == token.sub)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if body.first_name is not None:
        user.first_name = body.first_name
    if body.last_name is not None:
        user.last_name = body.last_name
    if body.institution is not None and user.profile:
        user.profile.institution = body.institution

    await db.commit()
    await db.refresh(user, attribute_names=["profile"])
    return user


@router.get("", response_model=list[UserSchema])
async def list_users(_: RequireAdmin, db: DB) -> list[User]:
    result = await db.execute(select(User).options(selectinload(User.profile)).order_by(User.email))
    return list(result.scalars().all())
