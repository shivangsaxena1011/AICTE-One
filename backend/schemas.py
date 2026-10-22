"""
Pydantic Request & Response Schemas
"""
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict

# Auth & Identity Schemas
class LoginRequest(BaseModel):
    username: str = Field(..., description="Email or Username")
    password: str = Field(..., description="Plaintext password")
    mfa_code: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: str
    department: Optional[str] = None
    institution_id: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    is_mfa_enabled: bool = False
    permissions: List[str] = []
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class PasswordResetRequest(BaseModel):
    account: str = Field(..., description="Email or Username")

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class MFASetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
    message: str

class MFAVerifyRequest(BaseModel):
    code: str

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
    route_type: Optional[str] = "SCRUTINY_EVC"
    workflow_definition_id: Optional[str] = None
    current_stage: Optional[str] = "Preliminary validation"
    stage_code: Optional[str] = "PRELIMINARY_VALIDATION"
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
    next_stage: Optional[str] = None
    stage_code: Optional[str] = None
    status: Optional[str] = "In review"
    actor: Optional[str] = None
    remarks: Optional[str] = None
    deficiencies: Optional[List[str]] = []
    idempotency_key: Optional[str] = None
    bypass_prereq_override: Optional[bool] = False

class ApplicationResponse(ApplicationBase):
    id: str
    institution_name: Optional[str] = None
    permanent_id: Optional[str] = None
    workflow_version: Optional[int] = 1
    stage_due_date: Optional[date] = None
    is_paused: Optional[bool] = False
    is_escalated: Optional[bool] = False
    escalation_level: Optional[int] = 0
    submitted_at: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Workflow Definition Schemas
class WorkflowStageConfig(BaseModel):
    stage_code: str
    stage_name: str
    sequence_order: int
    allowed_transitions: List[str]
    required_roles: List[str]
    prerequisites: Optional[List[str]] = []
    sla_days: Optional[int] = 7
    is_terminal: Optional[bool] = False

class WorkflowDefinitionCreate(BaseModel):
    name: str
    code: str
    category: Optional[str] = "Technical"
    academic_year: Optional[str] = "2026-2027"
    route_type: str
    stages: List[WorkflowStageConfig]
    description: Optional[str] = None

class WorkflowDefinitionResponse(BaseModel):
    id: str
    name: str
    code: str
    category: str
    academic_year: str
    route_type: str
    version: int
    is_active: bool
    stages_config: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# EVC Schemas
class EVCCreate(BaseModel):
    application_id: str
    institution_id: Optional[str] = None
    visit_type: Optional[str] = "Physical Visit"
    scheduled_date: date
    committee_chair: str
    convener: Optional[str] = None
    committee_members: Optional[str] = None
    expert_members: Optional[List[str]] = None
    conflicts_declared: Optional[bool] = False
    observations: Optional[str] = None
    remarks: Optional[str] = None

class EVCCompleteRequest(BaseModel):
    recommendation: str  # Recommended, Not Recommended, Conditional
    observations: str
    remarks: Optional[str] = None
    checklist_findings: Optional[Dict[str, Any]] = None
    geo_latitude: Optional[float] = None
    geo_longitude: Optional[float] = None

class EVCResponse(EVCCreate):
    id: str
    status: str
    report_submitted: bool
    convener: Optional[str] = None
    recommendation: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Undertakings Schemas
class UndertakingCreate(BaseModel):
    institution_id: str
    application_id: Optional[str] = None
    undertaking_type: str
    condition_ref: str
    description: Optional[str] = None
    statutory_deadline: date

class UndertakingReviewRequest(BaseModel):
    decision: str  # "Accept", "Reject"
    review_notes: str

class UndertakingResponse(BaseModel):
    id: str
    institution_id: str
    application_id: Optional[str] = None
    undertaking_type: str
    condition_ref: str
    description: Optional[str] = None
    statutory_deadline: date
    status: str
    evidence_file: Optional[str] = None
    evidence_submitted_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Document Validity Schemas
class DocumentValidityCreate(BaseModel):
    institution_id: str
    document_id: Optional[str] = None
    document_type: str
    document_ref_number: str
    issuing_authority: Optional[str] = None
    issue_date: date
    expiry_date: date
    advance_warning_days: Optional[int] = 60

class DocumentValidityResponse(BaseModel):
    id: str
    institution_id: str
    document_id: Optional[str] = None
    document_type: str
    document_ref_number: str
    issuing_authority: Optional[str] = None
    issue_date: date
    expiry_date: date
    advance_warning_days: int
    status: str
    renewal_application_ref: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Escalation Event Schemas
class EscalationResponse(BaseModel):
    id: str
    application_id: Optional[str] = None
    institution_id: str
    entity_type: str
    entity_id: str
    escalation_level: int
    trigger_reason: str
    escalated_to_role: str
    status: str
    resolution_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

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

# Phase 3: Correction Requests & Import Schemas
class InstitutionCorrectionCreate(BaseModel):
    reported_by: str
    contact_email: str
    field_name: str
    proposed_value: str
    rationale: str
    evidence_file: Optional[str] = None

class InstitutionCorrectionReview(BaseModel):
    decision: str  # "Approve" or "Reject"
    review_notes: str

class InstitutionCorrectionResponse(BaseModel):
    id: str
    institution_id: str
    reported_by: str
    contact_email: str
    field_name: str
    current_value: Optional[str] = None
    proposed_value: str
    evidence_file: Optional[str] = None
    rationale: str
    status: str
    review_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ImportPreviewRequest(BaseModel):
    file_path: Optional[str] = None
    sample_limit: Optional[int] = 15

class ImportConfirmRequest(BaseModel):
    file_path: Optional[str] = None
    batch_limit: Optional[int] = None

# Phase 4: Document Intelligence & Forensic Schemas
class DocumentReviewRequest(BaseModel):
    action: str  # CONFIRM_MATCH, CORRECT_FIELDS, DISMISS_FLAG, REQUEST_MORE_EVIDENCE, RECORD_OFFICIAL_FINDING
    justification: str
    field_corrections: Optional[Dict[str, Any]] = None
    official_finding: Optional[str] = None

class DocumentReviewResponse(BaseModel):
    document_id: str
    action: str
    previous_status: Optional[str] = None
    new_status: str
    reviewed_by: str
    reviewed_at: datetime
    justification: str

class ComplaintTriageRequest(BaseModel):
    complaint_id: Optional[str] = None
    institution_id: Optional[str] = None
    summary: str
    details: Optional[str] = None
    category: Optional[str] = None

class ComplaintTriageResponse(BaseModel):
    suggested_bureau: str
    suggested_category: str
    recommended_urgency: str  # Critical, High, Medium, Low
    urgency_reasoning: str
    extracted_entities: Dict[str, Any]
    missing_mandatory_information: List[str]
    potential_duplicate_cases: List[Dict[str, Any]]
    objective_summary: str
    statutory_disclaimer: str

class RiskRecommendationActionRequest(BaseModel):
    action: str  # ACCEPT, DISMISS, CORRECT
    notes: str
    corrected_data: Optional[Dict[str, Any]] = None

