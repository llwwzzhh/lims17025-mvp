"""Raw data, review, report, nonconformity and validation records."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RawDataRecord(Base):
    __tablename__ = "raw_data_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("test_tasks.id"), index=True)
    sample_id: Mapped[int] = mapped_column(ForeignKey("samples.id"), index=True)
    record_type: Mapped[str] = mapped_column(String(60), default="measurement")
    values: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    source_filename: Mapped[str | None] = mapped_column(String(255))
    source_sha256: Mapped[str | None] = mapped_column(String(64))
    recorded_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class DataCorrection(Base):
    __tablename__ = "data_corrections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    raw_data_id: Mapped[int] = mapped_column(ForeignKey("raw_data_records.id"), index=True)
    previous_values: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    corrected_values: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    reason: Mapped[str] = mapped_column(Text)
    corrected_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    corrected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WorkflowReview(Base):
    __tablename__ = "workflow_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("test_tasks.id"), index=True)
    stage: Mapped[str] = mapped_column(String(30))
    decision: Mapped[str] = mapped_column(String(30))
    comments: Mapped[str | None] = mapped_column(Text)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("test_tasks.id"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    content: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    revision_reason: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Nonconformity(Base):
    __tablename__ = "nonconformities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nc_code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(240))
    description: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(100))
    task_id: Mapped[int | None] = mapped_column(ForeignKey("test_tasks.id"), index=True)
    sample_id: Mapped[int | None] = mapped_column(ForeignKey("samples.id"), index=True)
    report_id: Mapped[int | None] = mapped_column(ForeignKey("reports.id"), index=True)
    immediate_action: Mapped[str | None] = mapped_column(Text)
    root_cause: Mapped[str | None] = mapped_column(Text)
    corrective_action: Mapped[str | None] = mapped_column(Text)
    effectiveness_check: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="open", index=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    closed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SystemValidationRecord(Base):
    __tablename__ = "system_validation_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    validation_code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    system_version: Mapped[str] = mapped_column(String(80))
    scope: Mapped[str] = mapped_column(Text)
    test_summary: Mapped[str] = mapped_column(Text)
    outcome: Mapped[str] = mapped_column(String(30), default="planned")
    evidence_reference: Mapped[str | None] = mapped_column(String(500))
    performed_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
