from datetime import datetime, date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---- User Context ----

class UserContext(BaseModel):
    user_id: str
    username: str
    email: str
    roles: list[str]
    dept_id: str | None = None
    clearance_level: int = 1


# ---- Wiki ----

class WikiPageCreate(BaseModel):
    title: str = Field(..., max_length=500)
    content: str
    slug: str = Field(..., max_length=500)
    parent_id: UUID | None = None
    sensitivity: str = Field(default="public", pattern="^(public|internal|confidential|secret)$")
    dept_id: str | None = None


class WikiPageUpdate(BaseModel):
    title: str | None = Field(None, max_length=500)
    content: str | None = None
    parent_id: UUID | None = None
    sensitivity: str | None = Field(None, pattern="^(public|internal|confidential|secret)$")
    edit_summary: str | None = None


class WikiPageResponse(BaseModel):
    id: UUID
    title: str
    content: str
    slug: str
    parent_id: UUID | None
    sensitivity: str
    dept_id: str | None
    created_by: str
    updated_by: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WikiPageListResponse(BaseModel):
    id: UUID
    title: str
    slug: str
    sensitivity: str
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Employee ----

class EmployeeResponse(BaseModel):
    employee_id: str
    name: str
    department: str | None
    level: str | None
    hire_date: date | None
    manager_id: str | None
    email: str | None
    status: str
    dept_id: str | None

    class Config:
        from_attributes = True


class EmployeeDetailResponse(EmployeeResponse):
    salary: float | None = None
    clearance_level: int = 1


# ---- Conversation / QA ----

class QARequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class QAResponse(BaseModel):
    answer: str
    sources: list[dict]
    intent: str
    confidence: float


class ConversationResponse(BaseModel):
    id: UUID
    question: str
    answer: str
    source_refs: list[dict]
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Knowledge Navigation ----

class NavNodeCreate(BaseModel):
    name: str = Field(..., max_length=200)
    parent_id: UUID | None = None
    icon: str | None = None
    description: str | None = None
    visibility_roles: list[str] = []


class NavNodeUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    parent_id: UUID | None = None
    icon: str | None = None
    description: str | None = None
    sort_order: int | None = None
    visibility_roles: list[str] | None = None


class NavNodeResponse(BaseModel):
    id: UUID
    name: str
    parent_id: UUID | None
    path: str | None
    icon: str | None
    description: str | None
    sort_order: int
    visibility_roles: list[str]
    children: list["NavNodeResponse"] = []

    class Config:
        from_attributes = True


# ---- Audit ----

class AuditLogResponse(BaseModel):
    id: int
    user_id: str
    action: str
    resource_type: str | None
    resource_id: str | None
    details: dict | None
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Generic ----

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
