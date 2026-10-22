"""
Relational Database Models for AICTE ONE (SHANKH)
"""
from datetime import datetime, date, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Text, Boolean, Date, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from backend.database import Base

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class User(Base):
    __tablename__ = "users"
    id = Column(String(50), primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, index=True)  # Primary Role Code (e.g. SUPER_ADMIN)
    department = Column(String(100), nullable=True)
    institution_id = Column(String(50), ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    is_mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(100), nullable=True)
    passkey_credential_id = Column(String(255), nullable=True)
    passkey_public_key = Column(Text, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    institution = relationship("Institution", foreign_keys=[institution_id])

class Role(Base):
    __tablename__ = "roles"
    id = Column(String(50), primary_key=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_system_role = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")

class Permission(Base):
    __tablename__ = "permissions"
    id = Column(String(50), primary_key=True)
    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    module = Column(String(50), nullable=False, index=True)
    action = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)

class RolePermission(Base):
    __tablename__ = "role_permissions"
    id = Column(String(50), primary_key=True)
    role_id = Column(String(50), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_id = Column(String(50), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True)

    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission")

class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(128), unique=True, nullable=False, index=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    is_revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="sessions")

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(128), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)

class LoginHistory(Base):
    __tablename__ = "login_history"
    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=True, index=True)
    username_attempted = Column(String(100), nullable=False, index=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    success = Column(Boolean, default=False)
    failure_reason = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=utc_now)

class Institution(Base):
    __tablename__ = "institutions"
    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    permanent_id = Column(String(50), unique=True, nullable=False, index=True)
    aicte_id = Column(String(50), nullable=True, index=True)
    state = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=False, index=True)
    city = Column(String(100), nullable=False)
    address = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, index=True)
    institution_type = Column(String(100), nullable=False)
    affiliation = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    approval_status = Column(String(50), default="Approved", index=True)
    approval_period = Column(String(50), default="2026-2027")
    programmes_count = Column(Integer, default=0)
    total_intake = Column(Integer, default=0)
    women_only = Column(Boolean, default=False)
    minority = Column(Boolean, default=False)
    is_demo_record = Column(Boolean, default=False)
    data_source = Column(String(100), default="Official AICTE Directory")
    verified_status = Column(String(50), default="Verified")
    last_verified = Column(Date, default=date.today)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    applications = relationship("Application", back_populates="institution", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="institution", cascade="all, delete-orphan")
    compliance_obligations = relationship("ComplianceObligation", back_populates="institution", cascade="all, delete-orphan")
    undertakings = relationship("Undertaking", back_populates="institution", cascade="all, delete-orphan")
    document_validities = relationship("DocumentValidity", back_populates="institution", cascade="all, delete-orphan")
    complaints = relationship("Complaint", back_populates="institution", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="institution", cascade="all, delete-orphan")
    correction_requests = relationship("InstitutionCorrectionRequest", back_populates="institution", cascade="all, delete-orphan")

class InstitutionCorrectionRequest(Base):
    __tablename__ = "institution_correction_requests"
    id = Column(String(50), primary_key=True)
    institution_id = Column(String(50), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    reported_by = Column(String(100), nullable=False)
    contact_email = Column(String(255), nullable=False)
    field_name = Column(String(100), nullable=False)  # e.g. approval_status, intake, name, address
    current_value = Column(Text, nullable=True)
    proposed_value = Column(Text, nullable=False)
    evidence_file = Column(String(255), nullable=True)
    rationale = Column(Text, nullable=False)
    status = Column(String(50), default="Pending Review", index=True) # Pending Review, Approved, Rejected
    review_notes = Column(Text, nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    institution = relationship("Institution", back_populates="correction_requests")

class ImportLog(Base):
    __tablename__ = "import_logs"
    id = Column(String(50), primary_key=True)
    source_file = Column(String(255), nullable=False)
    imported_by = Column(String(100), nullable=False)
    total_records = Column(Integer, default=0)
    imported_count = Column(Integer, default=0)
    updated_count = Column(Integer, default=0)
    skipped_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    status = Column(String(50), default="Success")  # Success, Partial, Failed
    summary_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

class WorkflowDefinition(Base):
    __tablename__ = "workflow_definitions"
    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    category = Column(String(100), default="Technical")
    academic_year = Column(String(50), default="2026-2027")
    route_type = Column(String(50), nullable=False)  # SCRUTINY_ONLY, SCRUTINY_EVC, EVC_SAC_SHC, EVC_ONLY, CUSTOM
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    stages_config = Column(Text, nullable=False)  # JSON representation of ordered stages
    rules_config = Column(Text, nullable=True)   # JSON representation of prerequisites/rules
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    stages = relationship("WorkflowStageDefinition", back_populates="workflow", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="workflow_definition")

class WorkflowStageDefinition(Base):
    __tablename__ = "workflow_stage_definitions"
    id = Column(String(50), primary_key=True)
    workflow_id = Column(String(50), ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    stage_code = Column(String(50), nullable=False, index=True)
    stage_name = Column(String(100), nullable=False)
    sequence_order = Column(Integer, nullable=False)
    allowed_transitions_json = Column(Text, nullable=False)  # JSON list of allowed next stage codes
    required_roles_json = Column(Text, nullable=False)       # JSON list of authorized role codes
    prerequisites_json = Column(Text, nullable=True)         # JSON list of prerequisites (e.g. docs, checks)
    sla_days = Column(Integer, default=7)
    escalation_policy_json = Column(Text, nullable=True)     # JSON escalation rules
    is_terminal = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)

    workflow = relationship("WorkflowDefinition", back_populates="stages")

class Application(Base):
    __tablename__ = "applications"
    id = Column(String(50), primary_key=True)
    institution_id = Column(String(50), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_definition_id = Column(String(50), ForeignKey("workflow_definitions.id", ondelete="SET NULL"), nullable=True, index=True)
    workflow_version = Column(Integer, default=1)
    route_type = Column(String(50), default="SCRUTINY_EVC")
    stage_code = Column(String(50), default="PRELIMINARY_VALIDATION", index=True)
    category = Column(String(100), nullable=False)
    type = Column(String(100), nullable=False)
    academic_year = Column(String(50), default="2026-2027")
    current_stage = Column(String(100), default="Preliminary validation", index=True)
    status = Column(String(50), default="New submission")
    owner = Column(String(100), default="Unassigned")
    assigned_role = Column(String(50), default="POLICY_COMPLIANCE_OFFICER")
    assigned_user_id = Column(String(50), nullable=True)
    progress = Column(Integer, default=10)
    submitted_at = Column(Date, default=date.today)
    due_date = Column(Date, nullable=True)
    stage_entered_at = Column(DateTime, default=utc_now)
    stage_due_date = Column(Date, nullable=True)
    is_paused = Column(Boolean, default=False)
    paused_at = Column(DateTime, nullable=True)
    total_pause_days = Column(Integer, default=0)
    resubmission_count = Column(Integer, default=0)
    is_escalated = Column(Boolean, default=False)
    escalation_level = Column(Integer, default=0)
    last_idempotency_key = Column(String(100), nullable=True)
    deficiency_count = Column(Integer, default=0)
    last_action = Column(Text, nullable=True)
    next_action = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    institution = relationship("Institution", back_populates="applications")
    workflow_definition = relationship("WorkflowDefinition", back_populates="applications")
    documents = relationship("Document", back_populates="application")
    evc_schedules = relationship("EVCSchedule", back_populates="application", cascade="all, delete-orphan")
    stages = relationship("ApplicationStage", back_populates="application", cascade="all, delete-orphan")
    undertakings = relationship("Undertaking", back_populates="application")
    escalations = relationship("EscalationEvent", back_populates="application", cascade="all, delete-orphan")

class ApplicationStage(Base):
    __tablename__ = "application_stages"
    id = Column(String(50), primary_key=True)
    application_id = Column(String(50), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    stage_code = Column(String(50), nullable=True)
    from_stage = Column(String(100), nullable=True)
    to_stage = Column(String(100), nullable=True)
    stage_name = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)
    action = Column(String(50), default="ADVANCE")
    actor = Column(String(100), nullable=False)
    time_spent_hours = Column(Float, default=0.0)
    sla_breached = Column(Boolean, default=False)
    remarks = Column(Text, nullable=True)
    deficiencies = Column(Text, nullable=True)
    idempotency_key = Column(String(100), nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    application = relationship("Application", back_populates="stages")

class EVCSchedule(Base):
    __tablename__ = "evc_schedules"
    id = Column(String(50), primary_key=True)
    application_id = Column(String(50), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    institution_id = Column(String(50), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False)
    visit_type = Column(String(50), default="Physical Visit")
    scheduled_date = Column(Date, nullable=False)
    status = Column(String(50), default="Scheduled")
    committee_chair = Column(String(100), nullable=False)
    convener = Column(String(100), nullable=True)
    committee_members = Column(Text, nullable=True)
    expert_members_json = Column(Text, nullable=True)
    conflicts_declared = Column(Boolean, default=False)
    geo_latitude = Column(Float, nullable=True)
    geo_longitude = Column(Float, nullable=True)
    report_submitted = Column(Boolean, default=False)
    recommendation = Column(String(50), nullable=True)  # Recommended, Not Recommended, Conditional
    checklist_findings_json = Column(Text, nullable=True)
    observations = Column(Text, nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    application = relationship("Application", back_populates="evc_schedules")

class Document(Base):
    __tablename__ = "documents"
    id = Column(String(50), primary_key=True)
    institution_id = Column(String(50), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(String(50), ForeignKey("applications.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    document_type = Column(String(100), nullable=False)
    file_path = Column(String(255), nullable=True)
    file_size = Column(Integer, default=0)
    file_hash = Column(String(100), nullable=True)
    uploaded_at = Column(Date, default=date.today)
    status = Column(String(50), default="Verification pending")
    confidence = Column(String(20), default="Not processed")
    extracted_fields = Column(Text, nullable=True)
    findings = Column(Text, nullable=True)
    issuing_authority = Column(String(255), nullable=True)
    authority_ref = Column(String(100), nullable=True)
    verification_source = Column(String(100), default="Not verified")
    verification_response = Column(Text, nullable=True)
    is_anomaly = Column(Boolean, default=False)
    confidentiality_level = Column(String(50), default="Internal")  # Public, Internal, Confidential
    uploaded_by = Column(String(100), nullable=True)
    review_status = Column(String(50), default="Pending Human Review")  # Pending Human Review, Confirmed Match, Flagged Discrepancy, Dismissed, Approved with Override, Rejected
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    human_overridden_fields = Column(Text, nullable=True)
    forensic_report_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    institution = relationship("Institution", back_populates="documents")
    application = relationship("Application", back_populates="documents")
    review_history = relationship("DocumentReviewHistory", back_populates="document", cascade="all, delete-orphan")

class ComplianceObligation(Base):
    __tablename__ = "compliance_obligations"
    id = Column(String(50), primary_key=True)
    institution_id = Column(String(50), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String(50), default="Upcoming")
    responsible_party = Column(String(100), default="Institution")
    evidence_file = Column(String(255), nullable=True)
    review_notes = Column(Text, nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    institution = relationship("Institution", back_populates="compliance_obligations")

class Undertaking(Base):
    __tablename__ = "undertakings"
    id = Column(String(50), primary_key=True)
    institution_id = Column(String(50), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(String(50), ForeignKey("applications.id", ondelete="SET NULL"), nullable=True, index=True)
    undertaking_type = Column(String(100), nullable=False)  # Faculty Cadre, Endowment Deposit, Land Conversion, Building Completion
    condition_ref = Column(String(100), nullable=False)    # e.g. APH-2026-Clause-4.2
    description = Column(Text, nullable=True)
    statutory_deadline = Column(Date, nullable=False)
    status = Column(String(50), default="Pending Submission") # Pending Submission, Evidence Submitted, Verified & Accepted, Rejected, Overdue
    evidence_file = Column(String(255), nullable=True)
    evidence_submitted_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    institution = relationship("Institution", back_populates="undertakings")
    application = relationship("Application", back_populates="undertakings")

class DocumentValidity(Base):
    __tablename__ = "document_validities"
    id = Column(String(50), primary_key=True)
    institution_id = Column(String(50), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(50), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True)
    document_type = Column(String(100), nullable=False) # Land Lease, Building Safety, Fire Safety NOC, Affiliating Univ NOC
    document_ref_number = Column(String(100), nullable=False)
    issuing_authority = Column(String(255), nullable=True)
    issue_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    advance_warning_days = Column(Integer, default=60)
    status = Column(String(50), default="Active") # Active, Expiring Soon, Expired, Renewed
    renewal_application_ref = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    institution = relationship("Institution", back_populates="document_validities")
    document = relationship("Document")

class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(String(50), primary_key=True)
    institution_id = Column(String(50), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    complainant_id = Column(String(50), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    case_number = Column(String(100), nullable=True)
    bureau = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False)
    summary = Column(Text, nullable=False)
    details = Column(Text, nullable=True)
    channel = Column(String(100), default="Online Portal")
    status = Column(String(50), default="Received")
    assigned_to = Column(String(100), default="Unassigned")
    received_date = Column(Date, default=date.today)
    due_date = Column(Date, nullable=True)
    related_case_id = Column(String(50), nullable=True)
    overlap_score = Column(Integer, default=0)
    overlap_reason = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    is_confidential = Column(Boolean, default=False)
    ragging_flag = Column(Boolean, default=False)
    ai_triage_json = Column(Text, nullable=True)
    triage_urgency = Column(String(20), default="Normal")  # Critical, High, Medium, Low
    missing_info_flags = Column(Text, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    institution = relationship("Institution", back_populates="complaints")
    complainant = relationship("User", foreign_keys=[complainant_id])

class CoordinationLink(Base):
    __tablename__ = "coordination_links"
    id = Column(String(50), primary_key=True)
    case_a_id = Column(String(50), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False)
    case_b_id = Column(String(50), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="Proposed")
    confidence_score = Column(Integer, default=85)
    matching_factors = Column(Text, nullable=True)
    rationale = Column(Text, nullable=True)
    coordinating_bureau = Column(String(100), nullable=True)
    coordinating_officer = Column(String(100), nullable=True)
    confirmed_by = Column(String(100), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(String(50), primary_key=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    priority = Column(String(50), default="Medium")
    status = Column(String(50), default="Pending")
    due_date = Column(Date, nullable=True)
    assigned_to = Column(String(100), nullable=False)
    bureau = Column(String(100), nullable=False)
    institution_id = Column(String(50), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True)
    application_id = Column(String(50), nullable=True)
    complaint_id = Column(String(50), nullable=True)
    document_id = Column(String(50), nullable=True)
    obligation_id = Column(String(50), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    institution = relationship("Institution", back_populates="tasks")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String(50), primary_key=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(String(50), default="System")
    urgency = Column(String(50), default="Info")
    link_type = Column(String(50), nullable=True)
    link_id = Column(String(50), nullable=True)
    is_read = Column(Boolean, default=False)
    user_id = Column(String(50), default="all")
    created_at = Column(DateTime, default=utc_now)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String(50), primary_key=True)
    timestamp = Column(DateTime, default=utc_now)
    actor = Column(String(100), nullable=False)
    role = Column(String(100), nullable=False)
    action = Column(String(255), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    changes_json = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_id = Column(String(50), nullable=True)

class EscalationEvent(Base):
    __tablename__ = "escalation_events"
    id = Column(String(50), primary_key=True)
    application_id = Column(String(50), ForeignKey("applications.id", ondelete="CASCADE"), nullable=True, index=True)
    institution_id = Column(String(50), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False) # Application, Undertaking, DocumentValidity
    entity_id = Column(String(50), nullable=False)
    escalation_level = Column(Integer, default=1) # 1: Regional Officer, 2: Bureau Head, 3: Member Secretary
    trigger_reason = Column(Text, nullable=False)
    escalated_to_role = Column(String(50), nullable=False)
    status = Column(String(50), default="Active") # Active, Acknowledged, Resolved
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    resolved_at = Column(DateTime, nullable=True)

    institution = relationship("Institution")
    application = relationship("Application", back_populates="escalations")

class DocumentReviewHistory(Base):
    __tablename__ = "document_review_history"
    id = Column(String(50), primary_key=True)
    document_id = Column(String(50), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer = Column(String(100), nullable=False)
    role = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)  # CONFIRM_MATCH, CORRECT_FIELDS, DISMISS_FLAG, REQUEST_MORE_EVIDENCE, RECORD_OFFICIAL_FINDING
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    justification = Column(Text, nullable=False)
    field_corrections_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utc_now)

    document = relationship("Document", back_populates="review_history")

class RiskRecommendation(Base):
    __tablename__ = "risk_recommendations"
    id = Column(String(50), primary_key=True)
    entity_type = Column(String(50), nullable=False, index=True) # Application, Institution, Officer, WorkflowStage
    entity_id = Column(String(50), nullable=False, index=True)
    institution_id = Column(String(50), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True, index=True)
    category = Column(String(100), nullable=False) # Deadline Breach Risk, Repeated Deficiency, Bottleneck Dwell Time, Workload Imbalance
    severity = Column(String(20), default="Medium") # Critical, High, Medium, Low
    title = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=False)
    supporting_indicators_json = Column(Text, nullable=True)
    status = Column(String(50), default="Active") # Active, Accepted, Dismissed, Corrected
    action_taken_by = Column(String(100), nullable=True)
    action_notes = Column(Text, nullable=True)
    action_timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

