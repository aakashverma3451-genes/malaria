from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserRole


class UserProfileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    institution: str
    max_concurrent_jobs: int
    storage_quota_gb: int


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    profile: UserProfileSchema | None = None


class UserUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str | None = None
    last_name: str | None = None
    institution: str | None = None
