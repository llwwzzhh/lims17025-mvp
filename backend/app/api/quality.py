"""Raw data, review, report, nonconformity, audit and validation endpoints."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import write_audit
from app.core.security import require_permission
from app.db import get_db
from app.models.core import Sample, TestTask
from app.models.identity import AuditLog, User
from app.models.quality import DataCorrection, Nonconformity, RawDataRecord, Report, SystemValidationRecord, WorkflowReview
from app.schemas_quality import (
    AuditView, DataCorrectionCreate, DataCorrectionView, NonconformityCreate,
    NonconformityUpdate, NonconformityView, RawDataCreate, RawDataView,
    ReportCreate, ReportRevisionCreate, ReportView, ReviewCreate, ReviewView,
    ValidationCreate, ValidationView,
)

router = APIRouter(prefix="/api", tags=["records and quality"])


@router.post("/raw-data", response_model=RawDataView, status_code=201)
async def record_raw_data(payload: RawDataCreate, actor: Annotated[User, Depends(require_permission("data.record"))], db: Annotated[AsyncSession, Depends(get_db)]):
    task = await db.get(TestTask, payload.task_id)
    if task is None:
        raise HTTPException(404, "Task not found")
    if task.status not in {"in_progress", "completed"}:
        raise HTTPException(409, "Raw data can only be recorded for an active or completed task")
    item = RawDataRecord(task_id=task.id, sample_id=task.sample_id, recorded_by=actor.id, **payload.model_dump())
    db.add(item)
    await db.flush()
    await write_audit(db, actor_user_id=actor.id, action="raw_data.create", entity_type="raw_data", entity_id=str(item.id), details={"task_id": task.id, "source_filename": item.source_filename, "source_sha256": item.source_sha256})
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/raw-data", response_model=list[RawDataView])
async def list_raw_data(_: Annotated[User, Depends(require_permission("data.read"))], db: Annotated[AsyncSession, Depends(get_db)], task_id: int | None = None):
    query = select(RawDataRecord).order_by(RawDataRecord.recorded_at.desc()).limit(500)
    if task_id is not None:
        query = query.where(RawDataRecord.task_id == task_id)
    return list((await db.scalars(query)).all())


@router.post("/raw-data/{record_id}/corrections", response_model=DataCorrectionView, status_code=201)
async def correct_raw_data(record_id: int, payload: DataCorrectionCreate, actor: Annotated[User, Depends(require_permission("data.correct"))], db: Annotated[AsyncSession, Depends(get_db)]):
    record = await db.get(RawDataRecord, record_id)
    if record is None:
        raise HTTPException(404, "Raw data record not found")
    correction = DataCorrection(raw_data_id=record.id, previous_values=record.values, corrected_values=payload.corrected_values, reason=payload.reason, corrected_by=actor.id)
    # Keep the original raw record immutable. The correction is a separate, attributable event.
    db.add(correction)
    await write_audit(db, actor_user_id=actor.id, action="raw_data.correct", entity_type="raw_data", entity_id=str(record.id), details={"correction_reason": payload.reason})
    await db.commit()
    await db.refresh(correction)
    return correction


@router.get("/raw-data/{record_id}/corrections", response_model=list[DataCorrectionView])
async def list_data_corrections(record_id: int, _: Annotated[User, Depends(require_permission("data.read"))], db: Annotated[AsyncSession, Depends(get_db)]):
    if await db.get(RawDataRecord, record_id) is None:
        raise HTTPException(404, "Raw data record not found")
    return list((await db.scalars(select(DataCorrection).where(DataCorrection.raw_data_id == record_id).order_by(DataCorrection.corrected_at))).all())


@router.post("/tasks/{task_id}/complete", response_model=ReviewView, status_code=201)
async def complete_task(task_id: int, _: Annotated[User, Depends(require_permission("tasks.execute"))], db: Annotated[AsyncSession, Depends(get_db)]):
    task = await db.get(TestTask, task_id)
    if task is None:
        raise HTTPException(404, "Task not found")
    if task.status != "in_progress":
        raise HTTPException(409, "Only in-progress tasks can be completed")
    task.status = "completed"
    task.completed_at = datetime.now(timezone.utc)
    await db.commit()
    return ReviewView.model_construct(task_id=task.id, stage="execution", decision="accepted", reviewer_id=task.assigned_to or task.created_by, comments="Execution completed", reviewed_at=task.completed_at, id=0)


@router.post("/tasks/{task_id}/reviews", response_model=ReviewView, status_code=201)
async def review_task(task_id: int, payload: ReviewCreate, actor: Annotated[User, Depends(require_permission("tasks.review"))], db: Annotated[AsyncSession, Depends(get_db)]):
    task = await db.get(TestTask, task_id)
    if task is None:
        raise HTTPException(404, "Task not found")
    if task.status not in {"completed", "under_review"}:
        raise HTTPException(409, "Task must be completed before review")
    item = WorkflowReview(task_id=task.id, stage="technical", decision=payload.decision, comments=payload.comments, reviewer_id=actor.id)
    task.status = "reviewed" if payload.decision == "accepted" else "in_progress" if payload.decision == "needs_correction" else "rejected"
    db.add(item)
    await write_audit(db, actor_user_id=actor.id, action="task.review", entity_type="test_task", entity_id=str(task.id), details={"decision": payload.decision})
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/tasks/{task_id}/reviews", response_model=list[ReviewView])
async def list_task_reviews(task_id: int, _: Annotated[User, Depends(require_permission("tasks.read"))], db: Annotated[AsyncSession, Depends(get_db)]):
    if await db.get(TestTask, task_id) is None:
        raise HTTPException(404, "Task not found")
    return list((await db.scalars(select(WorkflowReview).where(WorkflowReview.task_id == task_id).order_by(WorkflowReview.reviewed_at))).all())


@router.post("/reports", response_model=ReportView, status_code=201)
async def create_report(payload: ReportCreate, actor: Annotated[User, Depends(require_permission("reports.create"))], db: Annotated[AsyncSession, Depends(get_db)]):
    task = await db.get(TestTask, payload.task_id)
    if task is None or task.status != "reviewed":
        raise HTTPException(409, "Task must pass technical review before report creation")
    item = Report(report_code=payload.report_code, task_id=task.id, content=payload.content, created_by=actor.id)
    db.add(item)
    await db.flush()
    await write_audit(db, actor_user_id=actor.id, action="report.create", entity_type="report", entity_id=str(item.id))
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/reports", response_model=list[ReportView])
async def list_reports(_: Annotated[User, Depends(require_permission("reports.read"))], db: Annotated[AsyncSession, Depends(get_db)]):
    return list((await db.scalars(select(Report).order_by(Report.created_at.desc()).limit(500))).all())


@router.post("/reports/{report_id}/approve", response_model=ReportView)
async def approve_report(report_id: int, actor: Annotated[User, Depends(require_permission("reports.approve"))], db: Annotated[AsyncSession, Depends(get_db)]):
    item = await db.get(Report, report_id)
    if item is None:
        raise HTTPException(404, "Report not found")
    if item.status != "draft":
        raise HTTPException(409, "Only draft reports can be approved")
    if item.created_by == actor.id:
        raise HTTPException(403, "Report author cannot approve their own report")
    item.status = "approved"
    item.approved_by = actor.id
    item.approved_at = datetime.now(timezone.utc)
    await write_audit(db, actor_user_id=actor.id, action="report.approve", entity_type="report", entity_id=str(item.id), details={"version": item.version})
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/reports/{report_id}/revisions", response_model=ReportView, status_code=201)
async def revise_report(report_id: int, payload: ReportRevisionCreate, actor: Annotated[User, Depends(require_permission("reports.create"))], db: Annotated[AsyncSession, Depends(get_db)]):
    original = await db.get(Report, report_id)
    if original is None:
        raise HTTPException(404, "Report not found")
    if original.status != "approved":
        raise HTTPException(409, "Only approved reports can be revised")
    latest = await db.scalar(select(Report).where(Report.report_code == original.report_code).order_by(Report.version.desc()))
    item = Report(report_code=original.report_code, task_id=original.task_id, version=(latest.version + 1 if latest else original.version + 1), status="draft", content=payload.content, revision_reason=payload.revision_reason, created_by=actor.id)
    db.add(item)
    await db.flush()
    await write_audit(db, actor_user_id=actor.id, action="report.revision.create", entity_type="report", entity_id=str(item.id), details={"previous_report_id": original.id, "version": item.version, "reason": payload.revision_reason})
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/nonconformities", response_model=NonconformityView, status_code=201)
async def create_nonconformity(payload: NonconformityCreate, actor: Annotated[User, Depends(require_permission("nonconformities.manage"))], db: Annotated[AsyncSession, Depends(get_db)]):
    item = Nonconformity(**payload.model_dump(), created_by=actor.id)
    db.add(item)
    await db.flush()
    await write_audit(db, actor_user_id=actor.id, action="nonconformity.create", entity_type="nonconformity", entity_id=str(item.id))
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/nonconformities", response_model=list[NonconformityView])
async def list_nonconformities(_: Annotated[User, Depends(require_permission("nonconformities.read"))], db: Annotated[AsyncSession, Depends(get_db)]):
    return list((await db.scalars(select(Nonconformity).order_by(Nonconformity.created_at.desc()).limit(500))).all())


@router.patch("/nonconformities/{nc_id}", response_model=NonconformityView)
async def update_nonconformity(nc_id: int, payload: NonconformityUpdate, actor: Annotated[User, Depends(require_permission("nonconformities.manage"))], db: Annotated[AsyncSession, Depends(get_db)]):
    item = await db.get(Nonconformity, nc_id)
    if item is None:
        raise HTTPException(404, "Nonconformity not found")
    if item.status == "closed":
        raise HTTPException(409, "Closed records cannot be edited")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    if item.status == "closed":
        if not item.effectiveness_check:
            raise HTTPException(422, "Effectiveness check is required before closure")
        item.closed_by = actor.id
        item.closed_at = datetime.now(timezone.utc)
    await write_audit(db, actor_user_id=actor.id, action="nonconformity.update", entity_type="nonconformity", entity_id=str(item.id), details=payload.model_dump(exclude_unset=True))
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/system-validations", response_model=ValidationView, status_code=201)
async def create_validation(payload: ValidationCreate, actor: Annotated[User, Depends(require_permission("system_validation.manage"))], db: Annotated[AsyncSession, Depends(get_db)]):
    item = SystemValidationRecord(**payload.model_dump(), performed_by=actor.id)
    db.add(item)
    await db.flush()
    await write_audit(db, actor_user_id=actor.id, action="system_validation.create", entity_type="system_validation", entity_id=str(item.id))
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/system-validations", response_model=list[ValidationView])
async def list_validations(_: Annotated[User, Depends(require_permission("system_validation.read"))], db: Annotated[AsyncSession, Depends(get_db)]):
    return list((await db.scalars(select(SystemValidationRecord).order_by(SystemValidationRecord.performed_at.desc()))).all())


@router.post("/system-validations/{record_id}/approve", response_model=ValidationView)
async def approve_validation(record_id: int, actor: Annotated[User, Depends(require_permission("system_validation.approve"))], db: Annotated[AsyncSession, Depends(get_db)]):
    item = await db.get(SystemValidationRecord, record_id)
    if item is None:
        raise HTTPException(404, "Validation record not found")
    if item.performed_by == actor.id:
        raise HTTPException(403, "Validation performer cannot approve their own record")
    if item.outcome == "planned":
        raise HTTPException(409, "Validation must have an outcome before approval")
    item.approved_by = actor.id
    item.approved_at = datetime.now(timezone.utc)
    await write_audit(db, actor_user_id=actor.id, action="system_validation.approve", entity_type="system_validation", entity_id=str(item.id))
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/audit-logs", response_model=list[AuditView])
async def list_audit_logs(
    _: Annotated[User, Depends(require_permission("audit.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    entity_type: str | None = None,
    entity_id: str | None = None,
    since: datetime | None = None,
    limit: int = Query(default=100, ge=1, le=500),
):
    query = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.where(AuditLog.entity_id == entity_id)
    if since:
        query = query.where(AuditLog.created_at >= since)
    return list((await db.scalars(query)).all())
