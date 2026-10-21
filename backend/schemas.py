"""
Pydantic Request & Response Schemas
"""
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict

# Institution Schemas
class InstitutionBase(BaseModel):
    name: str
    permanent_id: str
    state: str
    district: str
    city: str
    address: Optional[str] = None
    category: str
    institution_type: str
    affiliation: Optional[str] = None
    website: Optional[str] = None
    approval_status: Optional[str] = "Approved"
    approval_period: Optional[str] = "2026-2027"
    programmes_count: Optional[int] = 0
    total_intake: Optional[int] = 0
    data_source: Optional[str] = "Official AICTE Directory"
    verified_status: Optional[str] = "Verified"

class InstitutionCreate(InstitutionBase):
    id: Optional[str] = None

class InstitutionResponse(InstitutionBase):
    id: str
    last_verified: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class InstitutionImportSummary(BaseModel):
    total_rows: int
    created: int
    updated: int
    skipped_duplicates: int
    rejected_errors: int
    errors: List[str]

# Application Schemas
class ApplicationBase(BaseModel):
    institution_id: str
    category: str
    type: str
    academic_year: Optional[str] = "2026-2027"
    current_stage: Optional[str] = "Preliminary validation"
    status: Optional[str] = "New submission"
    owner: Optional[str] = "Unassigned"
    progress: Optional[int] = 10
    due_date: Optional[date] = None
    deficiency_count: Optional[int] = 0
    last_action: Optional[str] = None
    next_action: Optional[str] = None

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationStageTransition(BaseModel):
    next_stage: str
    status: str
    actor: str
    remarks: Optional[str] = None
    deficiencies: Optional[List[str]] = []

class ApplicationResponse(ApplicationBase):
    id: str
    institution_name: Optional[str] = None
    permanent_id: Optional[str] = None
    submitted_at: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# EVC Schemas
class EVCCreate(BaseModel):
    application_id: str
    institution_id: str
    visit_type: Optional[str] = "Physical Visit"
    scheduled_date: date
    committee_chair: str
    committee_members: Optional[str] = None
    observations: Optional[str] = None
    remarks: Optional[str] = None

class EVCResponse(EVCCreate):
    id: str
    status: str
    report_submitted: bool
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Document Schemas
class DocumentUploadRequest(BaseModel):
    institution_id: str
    application_id: Optional[str] = None
    name: str
    document_type: str
    authority_ref: Optional[str] = None
    issuing_authority: Optional[str] = None
    file_base64: Optional[str] = None

class DocumentResponse(BaseModel):
    id: str
    institution_id: str
    institution_name: Optional[str] = None
    application_id: Optional[str] = None
    name: str
    document_type: str
    file_path: Optional[str] = None
    file_size: Optional[int] = 0
    file_hash: Optional[str] = None
    uploaded_at: Optional[date] = None
    status: str
    confidence: str
    extracted_fields: Optional[Any] = None
    findings: Optional[str] = None
    issuing_authority: Optional[str] = None
    authority_ref: Optional[str] = None
    verification_source: Optional[str] = None
    verification_response: Optional[str] = None
    is_anomaly: bool = False

    model_config = ConfigDict(from_attributes=True)

# Compliance Schemas
class ComplianceCreate(BaseModel):
    institution_id: str
    title: str
    category: str
    due_date: date
    responsible_party: Optional[str] = "Institution"
    evidence_file: Optional[str] = None
    review_notes: Optional[str] = None

class ComplianceResponse(ComplianceCreate):
    id: str
    institution_name: Optional[str] = None
    status: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Complaint & Coordination Schemas
class ComplaintCreate(BaseModel):
    institution_id: str
    bureau: str
    category: str
    summary: str
    details: Optional[str] = None
    channel: Optional[str] = "Online Portal"
    assigned_to: Optional[str] = "Unassigned"
    due_date: Optional[date] = None

class ComplaintResponse(ComplaintCreate):
    id: str
    institution_name: Optional[str] = None
    case_number: Optional[str] = None
    status: str
    received_date: Optional[date] = None
    related_case_id: Optional[str] = None
    overlap_score: int = 0
    overlap_reason: Optional[str] = None
    resolution_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class CoordinationLinkCreate(BaseModel):
    case_a_id: str
    case_b_id: str
    rationale: str
    coordinating_bureau: Optional[str] = None
    coordinating_officer: Optional[str] = None

# Task Schemas
class TaskCreate(BaseModel):
    title: str
    category: str
    priority: Optional[str] = "Medium"
    due_date: Optional[date] = None
    assigned_to: str
    bureau: str
    institution_id: Optional[str] = None
    application_id: Optional[str] = None
    complaint_id: Optional[str] = None
    document_id: Optional[str] = None
    obligation_id: Optional[str] = None
    resolution_notes: Optional[str] = None

class TaskResponse(TaskCreate):
    id: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Copilot & Graph Schemas
class CopilotQuery(BaseModel):
    query: str
    institution_id: Optional[str] = None
    use_gemini: Optional[bool] = False
    api_key: Optional[str] = None

class Citation(BaseModel):
    record_id: str
    record_type: str
    title: str
    status: Optional[str] = None

class CopilotResponse(BaseModel):
    answer: str
    citations: List[Citation]
    facts: List[str]
    rule_results: List[str]
    recommendations: List[str]
    provider: str

# Audit Schema
class AuditLogResponse(BaseModel):
    id: str
    timestamp: datetime
    actor: str
    role: str
    action: str
    entity_type: str
    entity_id: str
    details: Optional[str] = None
    changes_json: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
