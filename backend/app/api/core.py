"""Core business endpoints for customer, contract, sample, method, equipment and task records."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import write_audit
from app.core.security import current_user, require_permission
from app.db import get_db
from app.models.core import Contract, ControlledDocument, Customer, DocumentVersion, Equipment, Sample, SampleEvent, TestTask, TestTemplate
from app.models.identity import User
from app.schemas_core import (
    ContractCreate, ContractReview, ContractView, CustomerCreate, CustomerView,
    DocumentCreate, DocumentVersionCreate, DocumentVersionView, DocumentView,
    EquipmentCreate, EquipmentStatusUpdate, EquipmentView, SampleCreate,
    SampleEventCreate, SampleEventView, SampleView, TaskCreate, TaskView,
    TemplateCreate, TemplateView,
)

router = APIRouter(prefix="/api", tags=["core workflow"])


@router.post("/customers", response_model=CustomerView, status_code=201)
async def create_customer(payload: CustomerCreate, actor: Annotated[User, Depends(require_permission("contracts.manage"))], db: Annotated[AsyncSession, Depends(get_db)]):
    item = Customer(**payload.model_dump())
    db.add(item)
    await db.flush()
    await write_audit(db, actor_user_id=actor.id, action="customer.create", entity_type="customer", entity_id=str(item.id))
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/customers", response_model=list[CustomerView])
async def list_customers(_: Annotated[User, Depends(require_permission("contracts.read"))], db: Annotated[AsyncSession, Depends(get_db)]):
    return list((await db.scalars(select(Customer).order_by(Customer.id.desc()))).all())


@router.post("/contracts", response_model=ContractView, status_code=201)
async def create_contract(payload: ContractCreate, actor: Annotated[User, Depends(require_permission("contracts.manage"))], db: Annotated[AsyncSession, Depends(get_db)]):
    if await db.get(Customer, payload.customer_id) is None:
        raise HTTPException(404, "Customer not found")
    item = Contract(**payload.model_dump(), created_by=actor.id)
    db.add(item)
    await db.flush()
    await write_audit(db, actor_user_id=actor.id, action="contract.create", entity_type="contract", entity_id=str(item.id))
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/contracts", response_model=list[ContractView])
async def list_contracts(_: Annotated[User, Depends(require_permission("contracts.read"))], db: Annotated[AsyncSession, Depends(get_db)]):
    return list((await db.scalars(select(Contract).order_by(Contract.id.desc()))).all())


@router.post("/contracts/{contract_id}/review", response_model=ContractView)
async def review_contract(contract_id: int, payload: ContractReview, actor: Annotated[User, Depends(require_permission("contracts.review"))], db: Annotated[AsyncSession, Depends(get_db)]):
    item = await db.get(Contract, contract_id)
    if item is None:
        raise HTTPException(404, "Contract not found")
    item.review_status = payload.status
    item.review_notes = payload.notes
    item.reviewed_by = actor.id
    item.reviewed_at = datetime.now(timezone.utc)
    await write_audit(db, actor_user_id=actor.id, action="contract.review", entity_type="contract", entity_id=str(item.id), details={"status": payload.status, "notes": payload.notes})
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/samples", response_model=SampleView, status_code=201)
async def create_sample(payload: SampleCreate, actor: Annotated[User, Depends(require_permission("samples.manage"))], db: Annotated[AsyncSession, Depends(get_db)]):
    contract = await db.get(Contract, payload.contract_id)
    if contract is None or contract.customer_id != payload.customer_id:
        raise HTTPException(422, "Contract must exist and belong to the selected customer")
    if contract.review_status != "accepted":
        raise HTTPException(409, "Contract must be accepted before sample registration")
    item = Sample(**payload.model_dump(), created_by=actor.id)
    db.add(item)
    await db.flush()
    db.add(SampleEvent(sample_id=item.id, event_type="received", location=None, notes="Sample registered", actor_user_id=actor.id))
    await write_audit(db, actor_user_id=actor.id, action="sample.create", entity_type="sample", entity_id=str(item.id), details={"sample_code": item.sample_code})
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/samples", response_model=list[SampleView])
async def list_samples(_: Annotated[User, Depends(require_permission("samples.read"))], db: Annotated[AsyncSession, Depends(get_db)]):
    return list((await db.scalars(select(Sample).order_by(Sample.id.desc()))).all())


@router.post("/samples/{sample_id}/events", response_model=SampleEventView, status_code=201)
async def add_sample_event(sample_id: int, payload: SampleEventCreate, actor: Annotated[User, Depends(require_permission("samples.manage"))], db: Annotated[AsyncSession, Depends(get_db)]):
    sample = await db.get(Sample, sample_id)
    if sample is None:
        raise HTTPException(404, "Sample not found")
    item = SampleEvent(sample_id=sample.id, actor_user_id=actor.id, **payload.model_dump())
    db.add(item)
    sample.status = payload.event_type
    await write_audit(db, actor_user_id=actor.id, action="sample.event", entity_type="sample", entity_id=str(sample.id), details=payload.model_dump())
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/samples/{sample_id}/events", response_model=list[SampleEventView])
async def sample_events(sample_id: int, _: Annotated[User, Depends(require_permission("samples.read"))], db: Annotated[AsyncSession, Depends(get_db)]):
    if await db.get(Sample, sample_id) is None:
        raise HTTPException(404, "Sample not found")
    return list((await db.scalars(select(SampleEvent).where(SampleEvent.sample_id == sample_id).order_by(SampleEvent.occurred_at))).all())


@router.post("/documents", response_model=DocumentView, status_code=201)
async def create_document(payload: DocumentCreate, actor: Annotated[User, Depends(require_permission("documents.manage"))], db: Annotated[AsyncSession, Depends(get_db)]):
    item = ControlledDocument(**payload.model_dump(), created_by=actor.id)
    db.add(item)
    await db.flush()
    db.add(DocumentVersion(document_id=item.id, version=item.current_version, change_summary="Initial version", status="draft", created_by=actor.id))
    await write_audit(db, actor_user_id=actor.id, action="document.create", entity_type="document", entity_id=str(item.id))
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/documents", response_model=list[DocumentView])
async def list_documents(_: Annotated[User, Depends(require_permission("documents.read"))], db: Annotated[AsyncSession, Depends(get_db)]):
    return list((await db.scalars(select(ControlledDocument).order_by(ControlledDocument.id.desc()))).all())


@router.post("/documents/{document_id}/versions", response_model=DocumentVersionView, status_code=201)
async def add_document_version(document_id: int, payload: DocumentVersionCreate, actor: Annotated[User, Depends(require_permission("documents.manage"))], db: Annotated[AsyncSession, Depends(get_db)]):
    document = await db.get(ControlledDocument, document_id)
    if document is None:
        raise HTTPException(404, "Document not found")
    item = DocumentVersion(document_id=document.id, created_by=actor.id, **payload.model_dump())
    document.current_version = payload.version
    document.status = "draft"
    db.add(item)
    await write_audit(db, actor_user_id=actor.id, action="document.version.create", entity_type="document", entity_id=str(document.id), details={"version": payload.version})
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/documents/{document_id}/versions/{version_id}/approve", response_model=DocumentVersionView)
async def approve_document_version(document_id: int, version_id: int, actor: Annotated[User, Depends(require_permission("documents.approve"))], db: Annotated[AsyncSession, Depends(get_db)]):
    item = await db.get(DocumentVersion, version_id)
    document = await db.get(ControlledDocument, document_id)
    if item is None or document is None or item.document_id != document_id:
        raise HTTPException(404, "Document version not found")
    item.status = "approved"
    item.approved_by = actor.id
    item.approved_at = datetime.now(timezone.utc)
    document.status = "active"
    await write_audit(db, actor_user_id=actor.id, action="document.version.approve", entity_type="document_version", entity_id=str(item.id))
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/documents/{document_id}/versions", response_model=list[DocumentVersionView])
async def document_versions(document_id: int, _: Annotated[User, Depends(require_permission("documents.read"))], db: Annotated[AsyncSession, Depends(get_db)]):
    if await db.get(ControlledDocument, document_id) is None:
        raise HTTPException(404, "Document not found")
    return list((await db.scalars(select(DocumentVersion).where(DocumentVersion.document_id == document_id).order_by(DocumentVersion.id.desc()))).all())


@router.post("/equipment", response_model=EquipmentView, status_code=201)
async def create_equipment(payload: EquipmentCreate, actor: Annotated[User, Depends(require_permission("equipment.manage"))], db: Annotated[AsyncSession, Depends(get_db)]):
    item = Equipment(**payload.model_dump(), created_by=actor.id)
    db.add(item)
    await db.flush()
    await write_audit(db, actor_user_id=actor.id, action="equipment.create", entity_type="equipment", entity_id=str(item.id))
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/equipment", response_model=list[EquipmentView])
async def list_equipment(_: Annotated[User, Depends(require_permission("equipment.read"))], db: Annotated[AsyncSession, Depends(get_db)]):
    return list((await db.scalars(select(Equipment).order_by(Equipment.id.desc()))).all())


@router.patch("/equipment/{equipment_id}/status", response_model=EquipmentView)
async def set_equipment_status(equipment_id: int, payload: EquipmentStatusUpdate, actor: Annotated[User, Depends(require_permission("equipment.manage"))], db: Annotated[AsyncSession, Depends(get_db)]):
    item = await db.get(Equipment, equipment_id)
    if item is None:
        raise HTTPException(404, "Equipment not found")
    old_status = item.status
    item.status = payload.status
    if payload.notes:
        item.notes = payload.notes
    await write_audit(db, actor_user_id=actor.id, action="equipment.status", entity_type="equipment", entity_id=str(item.id), details={"old": old_status, "new": item.status, "notes": payload.notes})
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/test-templates", response_model=TemplateView, status_code=201)
async def create_template(payload: TemplateCreate, actor: Annotated[User, Depends(require_permission("templates.manage"))], db: Annotated[AsyncSession, Depends(get_db)]):
    if payload.method_document_id is not None:
        doc = await db.get(ControlledDocument, payload.method_document_id)
        if doc is None or doc.status != "active":
            raise HTTPException(422, "Referenced method must exist and be active")
    item = TestTemplate(**payload.model_dump(), created_by=actor.id)
    db.add(item)
    await db.flush()
    await write_audit(db, actor_user_id=actor.id, action="template.create", entity_type="test_template", entity_id=str(item.id))
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/test-templates", response_model=list[TemplateView])
async def list_templates(_: Annotated[User, Depends(require_permission("templates.read"))], db: Annotated[AsyncSession, Depends(get_db)]):
    return list((await db.scalars(select(TestTemplate).order_by(TestTemplate.id.desc()))).all())


@router.post("/tasks", response_model=TaskView, status_code=201)
async def create_task(payload: TaskCreate, actor: Annotated[User, Depends(require_permission("tasks.manage"))], db: Annotated[AsyncSession, Depends(get_db)]):
    sample = await db.get(Sample, payload.sample_id)
    template = await db.get(TestTemplate, payload.template_id)
    if sample is None or template is None or not template.is_active:
        raise HTTPException(422, "Sample and active test template are required")
    if payload.equipment_id is not None:
        equipment = await db.get(Equipment, payload.equipment_id)
        if equipment is None or equipment.status != "available":
            raise HTTPException(409, "Equipment is unavailable")
        now = datetime.now(timezone.utc)
        if equipment.calibration_due_at and equipment.calibration_due_at < now:
            raise HTTPException(409, "Equipment calibration is overdue")
        if equipment.maintenance_due_at and equipment.maintenance_due_at < now:
            raise HTTPException(409, "Equipment maintenance is overdue")
    item = TestTask(**payload.model_dump(), created_by=actor.id)
    db.add(item)
    await db.flush()
    await write_audit(db, actor_user_id=actor.id, action="task.create", entity_type="test_task", entity_id=str(item.id))
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/tasks", response_model=list[TaskView])
async def list_tasks(_: Annotated[User, Depends(require_permission("tasks.read"))], db: Annotated[AsyncSession, Depends(get_db)]):
    return list((await db.scalars(select(TestTask).order_by(TestTask.id.desc()))).all())


@router.post("/tasks/{task_id}/start", response_model=TaskView)
async def start_task(task_id: int, actor: Annotated[User, Depends(require_permission("tasks.execute"))], db: Annotated[AsyncSession, Depends(get_db)]):
    item = await db.get(TestTask, task_id)
    if item is None:
        raise HTTPException(404, "Task not found")
    if item.status != "planned":
        raise HTTPException(409, "Only planned tasks can be started")
    if item.equipment_id:
        equipment = await db.get(Equipment, item.equipment_id)
        now = datetime.now(timezone.utc)
        if equipment is None or equipment.status != "available" or (equipment.calibration_due_at and equipment.calibration_due_at < now) or (equipment.maintenance_due_at and equipment.maintenance_due_at < now):
            raise HTTPException(409, "Equipment is unavailable or overdue")
    item.status = "in_progress"
    item.started_at = datetime.now(timezone.utc)
    await write_audit(db, actor_user_id=actor.id, action="task.start", entity_type="test_task", entity_id=str(item.id))
    await db.commit()
    await db.refresh(item)
    return item
