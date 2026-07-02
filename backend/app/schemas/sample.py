from __future__ import annotations

import re
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.sample import FileType, Instrument, Organism, UploadStatus


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    organism: Organism = Organism.PF


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    organism: Organism | None = None


class ProjectSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str
    organism: Organism
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class SampleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: uuid.UUID
    sample_id: str = Field(min_length=1, max_length=100)
    external_id: str = ""
    species: Organism = Organism.PF
    collection_date: date | None = None
    collection_location: str = ""
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    metadata_: dict = Field(default_factory=dict, alias="metadata")
    notes: str = ""

    @field_validator("sample_id")
    @classmethod
    def validate_sample_id(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z0-9_\-\.]+$", v):
            raise ValueError("sample_id may only contain letters, digits, _, -, and .")
        return v


class SampleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    project_id: uuid.UUID
    sample_id: str
    external_id: str
    species: Organism
    collection_date: date | None
    collection_location: str
    latitude: float | None
    longitude: float | None
    metadata_: dict = Field(alias="metadata")
    notes: str
    created_at: datetime


class RawFileInitUpload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sample_id: uuid.UUID
    original_filename: str = Field(min_length=1, max_length=500)
    file_size_bytes: int = Field(gt=0)
    file_type: FileType
    sequencing_run_id: uuid.UUID | None = None

    @field_validator("original_filename")
    @classmethod
    def sanitize_filename(cls, v: str) -> str:
        name = re.sub(r"[^\w\-_\. ]", "_", v.split("/")[-1].split("\\")[-1])
        if not name:
            raise ValueError("Filename is invalid after sanitization")
        return name


class RawFileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sample_id: uuid.UUID
    original_filename: str
    file_type: FileType
    file_size_bytes: int
    md5_checksum: str
    is_validated: bool
    upload_status: UploadStatus
    uploaded_at: datetime


class PresignedUploadResponse(BaseModel):
    file_id: uuid.UUID
    presigned_url: str
    object_key: str
    expires_in_seconds: int = 7200
