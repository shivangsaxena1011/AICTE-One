"""
Compliance & Regulatory Obligations Router
Protected with RBAC & Multi-Institution Tenant Isolation
"""
import uuid
from typing import Optional, List
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models import ComplianceObligation, Institution, Undertaking, AuditLog, Notification, User
from backend.schemas import (
    ComplianceCreate, ComplianceResponse,
    UndertakingCreate, UndertakingResponse, UndertakingReviewRequest
)
from backend.services.escalation_service import escalation_service
from backend.auth import (
    get_current_user, require_roles, check_tenant_access,
    ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER, ROLE_SECURITY_OFFICER,
    ROLE_INSTITUTE_HEAD, ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR
)

router = APIRouter(prefix="/api/compliance", tags=["Compliance"])

@router.get("")
def list_compliance(
    status_filter: Optional[str] = Query(None, alias="status"),
    institution_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lists compliance obligations scoped by role permissions and tenant isolation:
    - Central AICTE compliance officers and admins see all institutions.
    - Institute Heads see ONLY obligations for their authorized institution.
    - Students and public visitors are denied access (403 Forbidden).
    """
    if user.role in {ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Regulatory compliance obligations are restricted to compliance officers and authorized institutional representatives."
        )

    query = db.query(ComplianceObligation)

    # Tenant isolation for Institute Heads
    if user.role == ROLE_INSTITUTE_HEAD:
        if not user.institution_id:
            return []
        query = query.filter(ComplianceObligation.institution_id == user.institution_id)
    elif institution_id:
        query = query.filter(ComplianceObligation.institution_id == institution_id)

    if status_filter:
        query = query.filter(ComplianceObligation.status == status_filter)

    obligations = query.order_by(ComplianceObligation.due_date).all()
    results = []
    today = date.today()

    for c in obligations:
        # Dynamically compute overdue if past due date and not satisfied
        current_status = c.status
        if current_status not in ["Satisfied by evidence", "Not applicable"]:
            if c.due_date < today:
                current_status = "Overdue"
            elif (c.due_date - today).days <= 7 and current_status != "Action required":
                current_status = "Due soon"

        results.append({
            "id": c.id,
            "institution_id": c.institution_id,
            "institution_name": c.institution.name if c.institution else "Unknown",
            "permanent_id": c.institution.permanent_id if c.institution else "Unknown",
            "title": c.title,
            "category": c.category,
            "due_date": c.due_date.isoformat(),
            "status": current_status,
            "responsible_party": c.responsible_party,
            "evidence_file": c.evidence_file,
            "review_notes": c.review_notes,
            "reviewed_by": c.reviewed_by,
            "reviewed_at": c.reviewed_at.isoformat() if c.reviewed_at else None
        })
    return results

@router.post("")
def create_compliance_obligation(
    payload: ComplianceCreate,
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db)
):
    """
    Creates a new statutory compliance obligation.
    Requires Super Administrator or Policy & Compliance Officer privilege.
    """
    inst = db.query(Institution).filter(Institution.id == payload.institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    new_id = f"CMP-{uuid.uuid4().hex[:5].upper()}"
    comp = ComplianceObligation(
        id=new_id,
        institution_id=payload.institution_id,
        title=payload.title,
        category=payload.category,
        due_date=payload.due_date,
        status="Upcoming",
        responsible_party=payload.responsible_party or "Institution",
        evidence_file=payload.evidence_file or "—",
        review_notes=payload.review_notes
    )
    db.add(comp)

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=user.username,
        role=user.role,
        action="Created Compliance Obligation",
        entity_type="Compliance",
        entity_id=comp.id,
        details=f"Created obligation '{comp.title}' due on {comp.due_date.isoformat()} for {inst.name}."
    )
    db.add(audit)
    db.commit()
    db.refresh(comp)
    return {"message": "Obligation created successfully", "id": comp.id}

@router.post("/{id}/upload-evidence")
async def upload_compliance_evidence(
    id: str,
    request: Request,
    evidence_filename: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    actor: Optional[str] = Form(None),
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER, ROLE_INSTITUTE_HEAD)),
    db: Session = Depends(get_db)
):
    """
    Uploads supporting compliance evidence for an obligation.
    Institute Heads can ONLY upload evidence for their designated institution.
    """
    comp = db.query(ComplianceObligation).filter(ComplianceObligation.id == id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Obligation not found")

    if user.role == ROLE_INSTITUTE_HEAD:
        if user.institution_id and user.institution_id != comp.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cross-institution access denied: Your account is restricted to institution '{user.institution_id}'."
            )

    content_type = request.headers.get("content-type", "")
    req_fname = evidence_filename
    req_actor = actor or user.username

    if "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict):
                req_fname = body.get("evidence_filename") or body.get("filename") or body.get("evidence_file") or req_fname
                req_actor = body.get("actor") or req_actor
        except Exception:
            pass

    fname = file.filename if file else (req_fname or f"Evidence_{comp.id}.pdf")
    comp.evidence_file = fname
    comp.status = "Evidence submitted"

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=user.username,
        role=user.role,
        action="Uploaded Compliance Evidence",
        entity_type="Compliance",
        entity_id=comp.id,
        details=f"Uploaded evidence file '{fname}' for obligation '{comp.title}'."
    )
    db.add(audit)
    db.commit()
    return {"message": "Evidence submitted successfully", "status": comp.status}

@router.post("/{id}/review")
async def review_compliance_obligation(
    id: str,
    request: Request,
    decision: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    reviewer: Optional[str] = Form(None),
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db)
):
    """
    Reviews and validates compliance evidence.
    Restricted to Compliance Officers and Super Admins.
    """
    comp = db.query(ComplianceObligation).filter(ComplianceObligation.id == id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Obligation not found")

    content_type = request.headers.get("content-type", "")
    req_decision = decision
    req_notes = notes
    req_reviewer = reviewer or user.full_name

    if "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict):
                req_decision = body.get("decision") or body.get("verdict") or req_decision
                req_notes = body.get("notes") or body.get("review_notes") or req_notes
                req_reviewer = body.get("reviewer") or req_reviewer
        except Exception:
            pass

    if not req_decision:
        req_decision = "Satisfied by evidence"
    if not req_notes:
        req_notes = "Evidence reviewed and approved according to regulations."

    comp.status = req_decision
    comp.review_notes = req_notes
    comp.reviewed_by = req_reviewer
    comp.reviewed_at = datetime.now(timezone.utc)

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=user.username,
        role=user.role,
        action="Reviewed Compliance Obligation",
        entity_type="Compliance",
        entity_id=comp.id,
        details=f"Marked '{comp.title}' as '{req_decision}'. Notes: {req_notes}."
    )
    db.add(audit)
    db.commit()
    return {"message": "Review recorded successfully", "status": comp.status}

# -------------------------------------------------------------
# Statutory Time-Bound Undertakings Register
# -------------------------------------------------------------

@router.get("/undertakings", response_model=List[UndertakingResponse])
def list_undertakings(
    status_filter: Optional[str] = Query(None, alias="status"),
    institution_id: Optional[str] = Query(None),
    application_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lists statutory time-bound undertakings with tenant isolation:
    - Central AICTE officers see all institutions across India.
    - Institute Heads see ONLY undertakings for their authorized institution.
    - Students and public visitors are forbidden.
    """
    if user.role in {ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Statutory undertakings are restricted to authorized personnel."
        )

    query = db.query(Undertaking)
    if user.role == ROLE_INSTITUTE_HEAD:
        if not user.institution_id:
            return []
        query = query.filter(Undertaking.institution_id == user.institution_id)
    elif institution_id:
        query = query.filter(Undertaking.institution_id == institution_id)

    if application_id:
        query = query.filter(Undertaking.application_id == application_id)
    if status_filter:
        query = query.filter(Undertaking.status == status_filter)

    return query.order_by(Undertaking.statutory_deadline).all()

@router.get("/undertakings/{id}", response_model=UndertakingResponse)
def get_undertaking(
    id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    u = db.query(Undertaking).filter(Undertaking.id == id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Undertaking not found")
    if user.role == ROLE_INSTITUTE_HEAD and user.institution_id != u.institution_id:
        raise HTTPException(status_code=403, detail="Cross-institution access denied")
    return u

@router.post("/undertakings", response_model=UndertakingResponse)
def create_undertaking(
    payload: UndertakingCreate,
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db)
):
    """Creates a statutory time-bound undertaking condition (Compliance Officer or Super Admin)."""
    inst = db.query(Institution).filter(Institution.id == payload.institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    new_id = f"UND-2026-{uuid.uuid4().hex[:5].upper()}"
    u = Undertaking(
        id=new_id,
        institution_id=payload.institution_id,
        application_id=payload.application_id,
        undertaking_type=payload.undertaking_type,
        condition_ref=payload.condition_ref,
        description=payload.description,
        statutory_deadline=payload.statutory_deadline,
        status="Pending Submission"
    )
    db.add(u)

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=user.username,
        role=user.role,
        action="Created Statutory Undertaking",
        entity_type="Undertaking",
        entity_id=u.id,
        details=f"Registered undertaking condition '{u.condition_ref}' ({u.undertaking_type}) for {inst.name} due {u.statutory_deadline.isoformat()}."
    )
    db.add(audit)
    db.commit()
    db.refresh(u)
    return u

@router.post("/undertakings/{id}/submit-evidence")
async def submit_undertaking_evidence(
    id: str,
    request: Request,
    evidence_file: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER, ROLE_INSTITUTE_HEAD)),
    db: Session = Depends(get_db)
):
    """Submits compliance evidence file for a statutory undertaking."""
    u = db.query(Undertaking).filter(Undertaking.id == id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Undertaking not found")

    if user.role == ROLE_INSTITUTE_HEAD and user.institution_id != u.institution_id:
        raise HTTPException(status_code=403, detail="Cross-institution submission denied")

    content_type = request.headers.get("content-type", "")
    fname = evidence_file
    if "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict):
                fname = body.get("evidence_file") or body.get("filename") or fname
        except Exception:
            pass

    if file:
        fname = file.filename
    if not fname:
        fname = f"Compliance_Evidence_{u.condition_ref}.pdf"

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    u.evidence_file = fname
    u.evidence_submitted_at = now
    u.status = "Evidence Submitted"

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=user.username,
        role=user.role,
        action="Submitted Undertaking Compliance Evidence",
        entity_type="Undertaking",
        entity_id=u.id,
        details=f"Submitted evidence file '{fname}' for condition {u.condition_ref}."
    )
    db.add(audit)
    db.commit()
    return {"message": "Compliance evidence submitted successfully", "status": u.status, "evidence_file": fname}

@router.post("/undertakings/{id}/review")
def review_undertaking(
    id: str,
    payload: UndertakingReviewRequest,
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db)
):
    """Reviews compliance evidence for an undertaking (Accept or Reject)."""
    u = db.query(Undertaking).filter(Undertaking.id == id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Undertaking not found")

    decision = payload.decision.strip()
    status_val = "Verified & Accepted" if "accept" in decision.lower() else "Rejected"
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    u.status = status_val
    u.review_notes = payload.review_notes
    u.reviewed_by = user.full_name or user.username
    u.reviewed_at = now

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=user.username,
        role=user.role,
        action="Reviewed Statutory Undertaking",
        entity_type="Undertaking",
        entity_id=u.id,
        details=f"Marked undertaking {u.condition_ref} as '{status_val}'. Notes: {payload.review_notes}."
    )
    db.add(audit)
    db.commit()
    return {"message": "Review recorded successfully", "undertaking_id": u.id, "status": u.status}

@router.post("/scan-undertakings")
def trigger_undertakings_scan(
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db)
):
    """Triggers automated statutory compliance check for overdue undertakings."""
    summary = escalation_service.check_undertakings_compliance(db)
    return summary
