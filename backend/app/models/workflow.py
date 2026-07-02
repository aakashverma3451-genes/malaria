from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    PositiveInt,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class WorkflowType(str, enum.Enum):
    SINGLE_SAMPLE_QC = "single_qc"
    SINGLE_SAMPLE_FULL = "single_full"
    POPULATION_JOINT_CALLING = "pop_joint"
    POPULATION_STRUCTURE = "pop_structure"
    POPULATION_PHYLOGENETICS = "pop_phylo"
    POPULATION_SELECTION = "pop_selection"
    POPULATION_FULL = "pop_full"


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResultType(str, enum.Enum):
    QC_REPORT = "qc_report"
    ALIGNMENT_STATS = "alignment_stats"
    VARIANT_CALLS = "variant_calls"
    ANNOTATED_VARIANTS = "annotated_variants"
    FWS = "fws"
    IBD_MATRIX = "ibd_matrix"
    ADMIXTURE = "admixture"
    PHYLOGENETIC_TREE = "phylogenetic_tree"
    DIVERSITY_STATS = "diversity_stats"
    SELECTION_SCAN = "selection_scan"
    FULL_REPORT = "full_report"
    OTHER = "other"


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"
    __table_args__ = (
        Index("ix_jobs_status", "status"),
        Index("ix_jobs_submitted_by", "submitted_by_id"),
        Index("ix_jobs_workflow_type", "workflow_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), default="")
    workflow_type: Mapped[WorkflowType] = mapped_column(SAEnum(WorkflowType))
    status: Mapped[JobStatus] = mapped_column(SAEnum(JobStatus), default=JobStatus.PENDING)
    parameters: Mapped[dict] = mapped_column(JSONB, default=dict)
    celery_task_id: Mapped[str] = mapped_column(String(255), default="")
    nextflow_run_name: Mapped[str] = mapped_column(String(255), default="")
    submitted_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT")
    )
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, default="")
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    output_dir: Mapped[str] = mapped_column(String(1000), default="")
    execution_log: Mapped[str] = mapped_column(Text, default="")

    samples: Mapped[list[AnalysisJobSample]] = relationship(
        "AnalysisJobSample", back_populates="job", cascade="all, delete-orphan", order_by="AnalysisJobSample.order"
    )
    results: Mapped[list[Result]] = relationship(
        "Result", back_populates="job", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AnalysisJob {self.id} [{self.status}]>"


class AnalysisJobSample(Base):
    __tablename__ = "analysis_job_samples"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analysis_jobs.id", ondelete="CASCADE")
    )
    sample_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("samples.id", ondelete="CASCADE")
    )
    order: Mapped[int] = mapped_column(Integer, default=0)

    job: Mapped[AnalysisJob] = relationship("AnalysisJob", back_populates="samples")
    sample: Mapped["Sample"] = relationship("Sample")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<AnalysisJobSample job={self.job_id} sample={self.sample_id}>"


class Result(Base):
    __tablename__ = "results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analysis_jobs.id", ondelete="CASCADE")
    )
    result_type: Mapped[ResultType] = mapped_column(SAEnum(ResultType))
    minio_object_key: Mapped[str] = mapped_column(String(1000), default="")
    summary_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job: Mapped[AnalysisJob] = relationship("AnalysisJob", back_populates="results")

    def __repr__(self) -> str:
        return f"<Result {self.result_type} job={self.job_id}>"
