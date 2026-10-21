"""
Relational Database Models for AICTE ONE
"""
from datetime import datetime, date, timezone
import json
from sqlalchemy import (
    Column, String, Integer, Text, Boolean, Date, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from backend.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id = Column(String(50), primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    department = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

class Institution(Base):
    __tablename__ = "institutions"
    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    permanent_id = Column(String(50), unique=True, nullable=False, index=True)
    state = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=False, index=True)
    city = Column(String(100), nullable=False)
    address = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, index=True)
    institution_type = Column(String(100), nullable=False)
    affiliation = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    approval_status = Column(String(50), default="Approved")
    approval_period = Column(String(50), default="2026-2027")
    programmes_count = Column(Integer, default=0)
    total_intake = Column(Integer, default=0)
    data_source = Column(String(100), default="Official AICTE Directory")
    verified_status = Column(String(50), default="Verified")
    last_verified = Column(Date, default=date.today)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    applications = relationship("Application", back_populates="institution", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="institution", cascade="all, delete-orphan")
    compliance_obligations = relationship("ComplianceObligation", back_populates="institution", cascade="all, delete-orphan")
    complaints = relationship("Complaint", back_populates="institution", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="institution", cascade="all, delete-orphan")

class Application(Base):
    __tablename__ = "applications"
    id = Column(String(50), primary_key=True)
    institution_id = Column(String(50), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(100), nullable=False)
    type = Column(String(100), nullable=False)
    academic_year = Column(String(50), default="2026-2027")
    current_stage = Column(String(100), default="Preliminary validation", index=True)
    status = Column(String(50), default="New submission")
    owner = Column(String(100), default="Unassigned")
    progress = Column(Integer, default=10)
    submitted_at = Column(Date, default=date.today)
    due_date = Column(Date, nullable=True)
    deficiency_count = Column(Integer, default=0)
    last_action = Column(Text, nullable=True)
    next_action = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    institution = relationship("Institution", back_populates="applications")
    documents = relationship("Document", back_populates="application")
    evc_schedules = relationship("EVCSchedule", back_populates="application", cascade="all, delete-orphan")
    stages = relationship("ApplicationStage", back_populates="application", cascade="all, delete-orphan")

class ApplicationStage(Base):
    __tablename__ = "application_stages"
    id = Column(String(50), primary_key=True)
    application_id = Column(String(50), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    stage_name = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)
    actor = Column(String(100), nullable=False)
    remarks = Column(Text, nullable=True)
    deficiencies = Column(Text, nullable=True)
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
    committee_members = Column(Text, nullable=True)
    report_submitted = Column(Boolean, default=False)
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
    created_at = Column(DateTime, default=utc_now)

    institution = relationship("Institution", back_populates="documents")
    application = relationship("Application", back_populates="documents")

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

class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(String(50), primary_key=True)
    institution_id = Column(String(50), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
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
    closed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    institution = relationship("Institution", back_populates="complaints")

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
