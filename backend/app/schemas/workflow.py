from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.workflow import JobStatus, ResultType, WorkflowType

_POPULATION_WORKFLOWS = {
    WorkflowType.POPULATION_JOINT_CALLING,
    WorkflowType.POPULATION_STRUCTURE,
    WorkflowType.POPULATION_PHYLOGENETICS,
    WorkflowType.POPULATION_SELECTION,
    WorkflowType.POPULATION_FULL,
}


class JobSubmit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = ""
    workflow_type: WorkflowType
    sample_ids: list[uuid.UUID] = Field(min_length=1)
    parameters: dict = Field(default_factory=dict)

    @field_validator("sample_ids")
    @classmethod
    def validate_sample_count(cls, v: list[uuid.UUID], info: ...) -> list[uuid.UUID]:
        workflow = info.data.get("workflow_type")
        if workflow in _POPULATION_WORKFLOWS and len(v) < 2:
            raise ValueError("Population workflows require at least 2 samples")
        return v


class JobStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: JobStatus
    progress_percent: int = Field(ge=0, le=100, default=0)
    execution_log: str = ""
    error_message: str = ""


class AnalysisJobSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    workflow_type: WorkflowType
    status: JobStatus
    parameters: dict
    progress_percent: int
    celery_task_id: str
    submitted_by_id: uuid.UUID
    submitted_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str
    execution_log: str


class ResultSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    result_type: ResultType
    minio_object_key: str
    summary_data: dict
    created_at: datetime
