from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class ReportType(str, enum.Enum):
    SINGLE_SAMPLE = "single_sample"
    POPULATION = "population"
    CUSTOM = "custom"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analysis_jobs.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(255))
    report_type: Mapped[ReportType] = mapped_column(SAEnum(ReportType))
    minio_object_key: Mapped[str] = mapped_column(String(1000))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    generated_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT")
    )

    job: Mapped["AnalysisJob"] = relationship("AnalysisJob")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<Report {self.title}>"
