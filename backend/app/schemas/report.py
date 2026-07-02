from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.report import ReportType


class ReportSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    title: str
    report_type: ReportType
    minio_object_key: str
    generated_at: datetime
    generated_by_id: uuid.UUID
