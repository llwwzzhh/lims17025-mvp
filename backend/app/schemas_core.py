"""Core LIMS API request and response schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CustomerCreate(BaseModel):
    customer_code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=200)
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None


class CustomerView(CustomerCreate, ORMModel):
    id: int
    created_at: datetime


class ContractCreate(BaseModel):
    contract_code: str = Field(min_length=1, max_length=60)
    customer_id: int
    scope: str
    method_requirements: dict[str, Any] = Field(default_factory=dict)


class ContractReview(BaseModel):
    status: str = Field(pattern="^(accepted|rejected|needs_clarification)$")
    notes: str | None = None


class ContractView(ORMModel):
    id: int
    contract_code: str
    customer_id: int
    scope: str
    method_requirements: dict[str, Any]
    review_status: str
    review_notes: str | None
    reviewed_by: int | None
    reviewed_at: datetime | None
    created_by: int
    created_at: datetime


class SampleCreate(BaseModel):
    sample_code: str = Field(min_length=1, max_length=80)
    customer_id: int
    contract_id: int
    manufacturer: str | None = None
    model: str = Field(min_length=1, max_length=200)
    lot_number: str | None = None
    serial_number: str | None = None
    quantity: int = Field(gt=0)
    condition_on_receipt: str | None = None


class SampleEventCreate(BaseModel):
    event_type: str = Field(min_length=1, max_length=40)
    location: str | None = None
    notes: str | None = None


class SampleView(ORMModel):
    id: int
    sample_code: str
    customer_id: int
    contract_id: int
    manufacturer: str | None
    model: str
    lot_number: str | None
    serial_number: str | None
    quantity: int
    condition_on_receipt: str | None
    status: str
    received_at: datetime
    created_by: int


class SampleEventView(ORMModel):
    id: int
    sample_id: int
    event_type: str
    location: str | None
    notes: str | None
    actor_user_id: int
    occurred_at: datetime


class DocumentCreate(BaseModel):
    document_code: str = Field(min_length=1, max_length=60)
    title: str = Field(min_length=1, max_length=240)
    document_type: str = Field(min_length=1, max_length=40)
    current_version: str = Field(min_length=1, max_length=40)


class DocumentVersionCreate(BaseModel):
    version: str = Field(min_length=1, max_length=40)
    change_summary: str
    file_reference: str | None = None


class DocumentView(ORMModel):
    id: int
    document_code: str
    title: str
    document_type: str
    current_version: str
    status: str
    created_by: int
    created_at: datetime


class DocumentVersionView(ORMModel):
    id: int
    document_id: int
    version: str
    change_summary: str
    file_reference: str | None
    status: str
    approved_by: int | None
    approved_at: datetime | None
    created_by: int
    created_at: datetime


class EquipmentCreate(BaseModel):
    equipment_code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=200)
    model: str | None = None
    serial_number: str | None = None
    location: str | None = None
    calibration_due_at: datetime | None = None
    maintenance_due_at: datetime | None = None
    notes: str | None = None


class EquipmentView(ORMModel):
    id: int
    equipment_code: str
    name: str
    model: str | None
    serial_number: str | None
    location: str | None
    status: str
    calibration_due_at: datetime | None
    maintenance_due_at: datetime | None
    notes: str | None
    created_by: int
    created_at: datetime


class EquipmentStatusUpdate(BaseModel):
    status: str = Field(pattern="^(available|in_use|out_of_service|retired)$")
    notes: str | None = None


class TemplateCreate(BaseModel):
    template_code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=200)
    test_type: str = Field(min_length=1, max_length=100)
    method_document_id: int | None = None
    method_version: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    acceptance_criteria: dict[str, Any] = Field(default_factory=dict)


class TemplateView(ORMModel):
    id: int
    template_code: str
    name: str
    test_type: str
    method_document_id: int | None
    method_version: str | None
    parameters: dict[str, Any]
    acceptance_criteria: dict[str, Any]
    is_active: bool
    created_by: int
    created_at: datetime


class TaskCreate(BaseModel):
    task_code: str = Field(min_length=1, max_length=60)
    sample_id: int
    template_id: int
    equipment_id: int | None = None
    method_version: str | None = None
    assigned_to: int | None = None
    notes: str | None = None


class TaskView(ORMModel):
    id: int
    task_code: str
    sample_id: int
    template_id: int
    equipment_id: int | None
    method_version: str | None
    status: str
    assigned_to: int | None
    created_by: int
    started_at: datetime | None
    completed_at: datetime | None
    notes: str | None
    created_at: datetime
