from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Organism(str, enum.Enum):
    PF = "pf"
    PV = "pv"
    AG = "ag"
    OTHER = "other"


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("name", "created_by_id", name="uq_project_name_user"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    organism: Mapped[Organism] = mapped_column(SAEnum(Organism), default=Organism.PF)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    created_by: Mapped["User"] = relationship("User", back_populates="projects", foreign_keys=[created_by_id])  # type: ignore[name-defined]
    samples: Mapped[list[Sample]] = relationship("Sample", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Project {self.name}>"


class Sample(Base):
    __tablename__ = "samples"
    __table_args__ = (
        UniqueConstraint("sample_id", "project_id", name="uq_sample_id_project"),
        Index("ix_samples_project_id", "project_id"),
        Index("ix_samples_sample_id", "sample_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE")
    )
    sample_id: Mapped[str] = mapped_column(String(100))
    external_id: Mapped[str] = mapped_column(String(100), default="")
    species: Mapped[Organism] = mapped_column(SAEnum(Organism), default=Organism.PF)
    collection_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    collection_location: Mapped[str] = mapped_column(String(255), default="")
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped[Project] = relationship("Project", back_populates="samples")
    raw_files: Mapped[list[RawFile]] = relationship("RawFile", back_populates="sample", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Sample {self.sample_id}>"


class Instrument(str, enum.Enum):
    ILLUMINA_MISEQ = "illumina_miseq"
    ILLUMINA_HISEQ = "illumina_hiseq"
    ILLUMINA_NEXTSEQ = "illumina_nextseq"
    ILLUMINA_NOVASEQ = "illumina_novaseq"
    ION_TORRENT = "ion_torrent"
    NANOPORE = "nanopore"
    OTHER = "other"


class SequencingRun(Base):
    __tablename__ = "sequencing_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[str] = mapped_column(String(100), unique=True)
    instrument: Mapped[Instrument] = mapped_column(SAEnum(Instrument), default=Instrument.OTHER)
    chip_id: Mapped[str] = mapped_column(String(100), default="")
    run_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    raw_files: Mapped[list[RawFile]] = relationship("RawFile", back_populates="sequencing_run")

    def __repr__(self) -> str:
        return f"<SequencingRun {self.run_id}>"


class FileType(str, enum.Enum):
    FASTQ_R1 = "fastq_r1"
    FASTQ_R2 = "fastq_r2"
    FASTQ_SINGLE = "fastq_single"
    BAM = "bam"
    VCF = "vcf"
    OTHER = "other"


class UploadStatus(str, enum.Enum):
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"


class RawFile(Base):
    __tablename__ = "raw_files"
    __table_args__ = (Index("ix_raw_files_sample_id", "sample_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sample_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("samples.id", ondelete="CASCADE")
    )
    sequencing_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sequencing_runs.id", ondelete="SET NULL"), nullable=True
    )
    minio_object_key: Mapped[str] = mapped_column(String(1000))
    original_filename: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[FileType] = mapped_column(SAEnum(FileType), default=FileType.OTHER)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger)
    md5_checksum: Mapped[str] = mapped_column(String(32), default="")
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False)
    upload_status: Mapped[UploadStatus] = mapped_column(
        SAEnum(UploadStatus), default=UploadStatus.UPLOADING, index=True
    )
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT")
    )
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sample: Mapped[Sample] = relationship("Sample", back_populates="raw_files")
    sequencing_run: Mapped[SequencingRun | None] = relationship("SequencingRun", back_populates="raw_files")

    def __repr__(self) -> str:
        return f"<RawFile {self.original_filename}>"
