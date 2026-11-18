"""Append-only operational records for LIMS workflows."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RawDataCreate(BaseModel):
    task_id: int
    record_type: str = Field(default="measurement", max_length=60)
    values: dict[str, Any]
    source_filename: str | None = None
    source_sha256: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{64}$")


class RawDataView(ORMModel):
    id: int
    task_id: int
    sample_id: int
    record_type: str
    values: dict[str, Any]
    source_filename: str | None
    source_sha256: str | None
    recorded_by: int
    recorded_at: datetime


class DataCorrectionCreate(BaseModel):
    corrected_values: dict[str, Any]
    reason: str = Field(min_length=3)


class DataCorrectionView(ORMModel):
    id: int
    raw_data_id: int
    previous_values: dict[str, Any]
    corrected_values: dict[str, Any]
    reason: str
    corrected_by: int
    corrected_at: datetime


class ReviewCreate(BaseModel):
    decision: str = Field(pattern="^(accepted|rejected|needs_correction)$")
    comments: str | None = None


class ReviewView(ORMModel):
    id: int
    task_id: int
    stage: str
    decision: str
    comments: str | None
    reviewer_id: int
    reviewed_at: datetime


class ReportCreate(BaseModel):
    report_code: str = Field(min_length=1, max_length=80)
    task_id: int
    content: dict[str, Any]


class ReportRevisionCreate(BaseModel):
    content: dict[str, Any]
    revision_reason: str = Field(min_length=3)


class ReportView(ORMModel):
    id: int
    report_code: str
    task_id: int
    version: int
    status: str
    content: dict[str, Any]
    revision_reason: str | None
    created_by: int
    approved_by: int | None
    created_at: datetime
    approved_at: datetime | None


class NonconformityCreate(BaseModel):
    nc_code: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=240)
    description: str = Field(min_length=1)
    source: str = Field(min_length=1, max_length=100)
    task_id: int | None = None
    sample_id: int | None = None
    report_id: int | None = None
    immediate_action: str | None = None
    owner_id: int | None = None


class NonconformityUpdate(BaseModel):
    immediate_action: str | None = None
    root_cause: str | None = None
    corrective_action: str | None = None
    effectiveness_check: str | None = None
    status: str = Field(pattern="^(open|investigating|action_pending|effectiveness_check|closed)$")


class NonconformityView(ORMModel):
    id: int
    nc_code: str
    title: str
    description: str
    source: str
    task_id: int | None
    sample_id: int | None
    report_id: int | None
    immediate_action: str | None
    root_cause: str | None
    corrective_action: str | None
    effectiveness_check: str | None
    status: str
    owner_id: int | None
    created_by: int
    closed_by: int | None
    created_at: datetime
    closed_at: datetime | None


class ValidationCreate(BaseModel):
    validation_code: str = Field(min_length=1, max_length=80)
    system_version: str = Field(min_length=1, max_length=80)
    scope: str
    test_summary: str
    outcome: str = Field(default="planned", pattern="^(planned|passed|failed|conditionally_accepted)$")
    evidence_reference: str | None = None


class ValidationView(ORMModel):
    id: int
    validation_code: str
    system_version: str
    scope: str
    test_summary: str
    outcome: str
    evidence_reference: str | None
    performed_by: int
    approved_by: int | None
    performed_at: datetime
    approved_at: datetime | None


class AuditView(ORMModel):
    id: int
    actor_user_id: int | None
    action: str
    entity_type: str
    entity_id: str | None
    details: dict[str, Any]
    created_at: datetime
