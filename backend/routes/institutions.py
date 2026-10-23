"""
Institutions Router: Authoritative Master Directory, Digital Twin, Search, Approval Verification,
Correction Workflows, Data Quality Monitoring, and Official Batch Import Pipeline
"""
import io
import csv
import os
import json
import uuid
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Body, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc, func

from backend.database import get_db
from backend.models import (
    Institution, Application, Document, ComplianceObligation, Complaint, Task,
    Undertaking, DocumentValidity, InstitutionCorrectionRequest, ImportLog, AuditLog, User
)
from backend.schemas import (
    InstitutionResponse, InstitutionCreate, InstitutionImportSummary,
    InstitutionCorrectionCreate, InstitutionCorrectionReview, InstitutionCorrectionResponse,
    ImportPreviewRequest, ImportConfirmRequest
)
from backend.services.institution_importer import institution_importer
from backend.services.institution_search import institution_search
from backend.auth import (
    get_current_user, get_optional_user, require_roles, check_tenant_access,
    ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER, ROLE_COMPLIANCE_OFFICER,
    ROLE_INSTITUTE_HEAD, ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR
)

router = APIRouter(prefix="/api/institutions", tags=["Institutions"])

# -------------------------------------------------------------
# 1. Authoritative Directory Search & Listing
# -------------------------------------------------------------
@router.get("/stats")
def get_institutions_stats(db: Session = Depends(get_db)):
    """
    Returns authoritative aggregate stats and distinct filter options across all 8,800+ institutions.
    """
    total = db.query(func.count(Institution.id)).scalar() or 0
    approved = db.query(func.count(Institution.id)).filter(Institution.approval_status == "Approved").scalar() or 0
    total_programmes = db.query(func.sum(Institution.programmes_count)).scalar() or 0
    total_intake = db.query(func.sum(Institution.total_intake)).scalar() or 0

    raw_states = db.query(Institution.state).distinct().all()
    states = sorted([s[0] for s in raw_states if s[0] and s[0].strip()])

    raw_cats = db.query(Institution.category).distinct().all()
    categories = sorted([c[0] for c in raw_cats if c[0] and c[0].strip()])

    raw_types = db.query(Institution.institution_type).distinct().all()
    institution_types = sorted([t[0] for t in raw_types if t[0] and t[0].strip()])

    return {
        "total_institutions": total,
        "approved_count": approved,
        "total_programmes": int(total_programmes),
        "total_intake": int(total_intake),
        "states": states,
        "categories": categories,
        "institution_types": institution_types
    }

@router.get("", response_model=dict)
def list_institutions(
    q: Optional[str] = Query(None, description="Search by name, permanent_id, or city"),
    search: Optional[str] = Query(None, description="Search alias for q"),
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    institution_type: Optional[str] = Query(None),
    approval_status: Optional[str] = Query(None),
    sort_by: str = Query("name"),
    order: str = Query("asc"),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Public directory search: accessible to both unauthenticated public visitors and authorized officers.
    Supports partial text, stable IDs, and multi-field filters.
    """
    query = db.query(Institution)

    search_term = (q or search or "").strip()
    if search_term:
        search_filter = or_(
            Institution.name.ilike(f"%{search_term}%"),
            Institution.permanent_id.ilike(f"%{search_term}%"),
            Institution.aicte_id.ilike(f"%{search_term}%"),
            Institution.city.ilike(f"%{search_term}%"),
            Institution.district.ilike(f"%{search_term}%")
        )
        query = query.filter(search_filter)

    if state:
        query = query.filter(Institution.state.ilike(f"%{state}%"))
    if district:
        query = query.filter(Institution.district.ilike(f"%{district}%"))
    if category:
        query = query.filter(Institution.category == category)
    if institution_type:
        query = query.filter(Institution.institution_type == institution_type)
    if approval_status:
        query = query.filter(Institution.approval_status == approval_status)

    total = query.count()

    sort_col = getattr(Institution, sort_by, Institution.name)
    query = query.order_by(asc(sort_col) if order == "asc" else desc(sort_col))

    offset = (page - 1) * limit
    institutions = query.offset(offset).limit(limit).all()

    data = []
    for inst in institutions:
        data.append({
            "id": inst.id,
            "permanent_id": inst.permanent_id,
            "aicte_id": inst.aicte_id,
            "name": inst.name,
            "state": inst.state,
            "district": inst.district,
            "city": inst.city,
            "address": inst.address,
            "category": inst.category,
            "institution_type": inst.institution_type,
            "affiliation": inst.affiliation,
            "website": inst.website,
            "approval_status": inst.approval_status,
            "approval_period": inst.approval_period,
            "programmes_count": inst.programmes_count,
            "total_intake": inst.total_intake,
            "women_only": bool(inst.women_only),
            "minority": bool(inst.minority),
            "data_source": inst.data_source,
            "verified_status": inst.verified_status,
            "last_verified": inst.last_verified.isoformat() if inst.last_verified else None,
            "applications_count": len(inst.applications),
            "documents_count": len(inst.documents),
            "compliance_count": len(inst.compliance_obligations),
            "complaints_count": len(inst.complaints)
        })

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if limit else 1,
        "data": data,
        "items": data
    }

# -------------------------------------------------------------
# 2. Advanced Matching (Acronyms, Fuzzy & Partial Name Matching)
# -------------------------------------------------------------
@router.get("/search")
@router.get("/search/advanced")
def advanced_institution_search(
    q: str = Query(..., description="Institution name, acronym (e.g. VJTI, COEP, OIST), or official identifier"),
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Authoritative matching engine:
    Expands common educational abbreviations and returns confirmed vs suggested matches.
    """
    return institution_search.search_institutions(db, query_str=q, state=state, district=district, limit=limit)

# -------------------------------------------------------------
# 3. Official Approval Verification Module
# -------------------------------------------------------------
@router.get("/verify")
@router.get("/verify/{id}")
@router.get("/{id}/approval-verification")
def verify_institution_approval(
    id: Optional[str] = None,
    q: Optional[str] = Query(None),
    academic_year: str = Query("2026-2027"),
    db: Session = Depends(get_db)
):
    """
    Public Verification Gateway:
    Determines status (Approved, Approval Expired, Pending, Not Approved, Needs Verification)
    based on authoritative records without guessing.
    """
    target = id or q
    if not target:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either path identifier or query parameter 'q' must be provided."
        )
    return institution_search.verify_approval(db, institution_identifier=target, academic_year=academic_year)

# -------------------------------------------------------------
# 4. Data Quality Dashboard
# -------------------------------------------------------------
@router.get("/data-quality")
def get_data_quality_metrics(
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER, ROLE_SECURITY_OFFICER)),
    db: Session = Depends(get_db)
):
    """
    Evaluates master database completeness, stale records, duplicate candidates, and missing attributes.
    """
    total = db.query(Institution).count()
    missing_district = db.query(Institution).filter(or_(Institution.district == None, Institution.district == "")).count()
    missing_address = db.query(Institution).filter(or_(Institution.address == None, Institution.address == "")).count()
    missing_website = db.query(Institution).filter(or_(Institution.website == None, Institution.website == "")).count()
    unverified = db.query(Institution).filter(Institution.verified_status != "Verified").count()

    today = date.today()
    one_year_ago = today.replace(year=today.year - 1)
    stale_records = db.query(Institution).filter(
        or_(Institution.last_verified == None, Institution.last_verified < one_year_ago)
    ).count()

    return {
        "total_institutions": total,
        "data_quality_score": round(((total - unverified - missing_district) / max(total, 1)) * 100.0, 1),
        "flags": {
            "missing_district_count": missing_district,
            "missing_address_count": missing_address,
            "missing_website_count": missing_website,
            "unverified_status_count": unverified,
            "stale_records_past_1_year": stale_records
        },
        "last_audit_run": datetime.now(timezone.utc).isoformat()
    }

# -------------------------------------------------------------
# 5. Public / Institutional Discrepancy & Correction Requests
# -------------------------------------------------------------
@router.post("/{id}/correction-request", response_model=InstitutionCorrectionResponse)
def submit_correction_request(
    id: str,
    payload: InstitutionCorrectionCreate,
    db: Session = Depends(get_db)
):
    """
    Submits a correction request reporting an official data mismatch without altering
    the production record until authorized officer review.
    """
    inst = db.query(Institution).filter(or_(Institution.id == id, Institution.permanent_id == id)).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    current_val = getattr(inst, payload.field_name, None)
    req_id = f"CORR-{uuid.uuid4().hex[:6].upper()}"

    corr = InstitutionCorrectionRequest(
        id=req_id,
        institution_id=inst.id,
        reported_by=payload.reported_by,
        contact_email=payload.contact_email,
        field_name=payload.field_name,
        current_value=str(current_val) if current_val is not None else None,
        proposed_value=payload.proposed_value,
        evidence_file=payload.evidence_file,
        rationale=payload.rationale,
        status="Pending Review"
    )
    db.add(corr)
    db.commit()
    db.refresh(corr)
    return corr

@router.get("/{id}/correction-requests", response_model=List[InstitutionCorrectionResponse])
def list_institution_correction_requests(
    id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    inst = db.query(Institution).filter(or_(Institution.id == id, Institution.permanent_id == id)).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    if user.role == ROLE_INSTITUTE_HEAD and user.institution_id != inst.id and user.institution_id != inst.permanent_id:
        raise HTTPException(status_code=403, detail="Cross-institution access denied")

    return db.query(InstitutionCorrectionRequest).filter(
        InstitutionCorrectionRequest.institution_id == inst.id
    ).order_by(desc(InstitutionCorrectionRequest.created_at)).all()

@router.post("/correction-requests/{req_id}/review")
def review_correction_request(
    req_id: str,
    payload: InstitutionCorrectionReview,
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db)
):
    """Reviews and resolves a reported institutional discrepancy."""
    corr = db.query(InstitutionCorrectionRequest).filter(InstitutionCorrectionRequest.id == req_id).first()
    if not corr:
        raise HTTPException(status_code=404, detail="Correction request not found")

    is_approved = "approve" in payload.decision.lower()
    corr.status = "Approved" if is_approved else "Rejected"
    corr.review_notes = payload.review_notes
    corr.reviewed_by = user.full_name or user.username
    corr.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)

    # If approved, apply the correction to the institution record safely
    if is_approved and hasattr(corr.institution, corr.field_name):
        old_val = getattr(corr.institution, corr.field_name)
        setattr(corr.institution, corr.field_name, corr.proposed_value)
        corr.institution.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        audit = AuditLog(
            id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
            actor=user.username,
            role=user.role,
            action="Approved Discrepancy Correction",
            entity_type="Institution",
            entity_id=corr.institution.id,
            details=f"Updated field '{corr.field_name}' from '{old_val}' to '{corr.proposed_value}'. Notes: {payload.review_notes}."
        )
        db.add(audit)

    db.commit()
    return {
        "message": f"Correction request marked as {corr.status}",
        "request_id": corr.id,
        "status": corr.status
    }

# -------------------------------------------------------------
# 6. Comprehensive Tabbed Institution Digital Twin Profile
# -------------------------------------------------------------
@router.get("/{id}")
@router.get("/{id}/twin")
def get_institution_digital_twin(
    id: str,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Returns permission-aware, comprehensive institutional Digital Twin profile.
    Separates public details from confidential regulatory proceedings.
    """
    inst = db.query(Institution).filter(or_(Institution.id == id, Institution.permanent_id == id)).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    # Enforce tenant isolation for Institute Heads
    if user and user.role == ROLE_INSTITUTE_HEAD:
        if user.institution_id and user.institution_id != inst.id and user.institution_id != inst.permanent_id:
            raise HTTPException(
                status_code=403,
                detail=f"Cross-institution access forbidden: Your account is restricted to institution '{user.institution_id}'."
            )

    is_privileged_or_owner = False
    if user:
        if user.role != ROLE_STUDENT_COMPLAINANT and user.role != ROLE_PUBLIC_VISITOR:
            if user.role == ROLE_INSTITUTE_HEAD:
                if user.institution_id == inst.id or user.institution_id == inst.permanent_id:
                    is_privileged_or_owner = True
            else:
                is_privileged_or_owner = True

    apps = [{
        "id": a.id, "type": a.type, "category": a.category, "route_type": a.route_type or "SCRUTINY_EVC",
        "current_stage": a.current_stage, "stage_code": a.stage_code, "status": a.status,
        "progress": a.progress, "owner": a.owner,
        "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
        "due_date": a.due_date.isoformat() if a.due_date else None,
        "deficiency_count": a.deficiency_count,
        "resubmission_count": a.resubmission_count or 0,
        "is_paused": bool(a.is_paused),
        "is_escalated": bool(a.is_escalated)
    } for a in inst.applications] if is_privileged_or_owner else []

    docs = [{
        "id": d.id, "name": d.name, "document_type": d.document_type, "status": d.status,
        "confidence": d.confidence, "findings": d.findings, "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
        "authority_ref": d.authority_ref, "verification_source": d.verification_source, "is_anomaly": d.is_anomaly
    } for d in inst.documents] if is_privileged_or_owner else []

    comps = [{
        "id": c.id, "title": c.title, "category": c.category, "due_date": c.due_date.isoformat(),
        "status": c.status, "responsible_party": c.responsible_party, "evidence_file": c.evidence_file,
        "review_notes": c.review_notes
    } for c in inst.compliance_obligations] if is_privileged_or_owner else []

    undertakings = [{
        "id": u.id, "undertaking_type": u.undertaking_type, "condition_ref": u.condition_ref,
        "statutory_deadline": u.statutory_deadline.isoformat(), "status": u.status,
        "evidence_file": u.evidence_file, "reviewed_by": u.reviewed_by
    } for u in inst.undertakings] if is_privileged_or_owner else []

    validities = [{
        "id": v.id, "document_type": v.document_type, "document_ref_number": v.document_ref_number,
        "issue_date": v.issue_date.isoformat(), "expiry_date": v.expiry_date.isoformat(),
        "advance_warning_days": v.advance_warning_days, "status": v.status,
        "renewal_application_ref": v.renewal_application_ref
    } for v in inst.document_validities] if is_privileged_or_owner else []

    cases = [{
        "id": c.id, "case_number": c.case_number, "bureau": c.bureau, "category": c.category,
        "summary": c.summary, "status": c.status, "received_date": c.received_date.isoformat() if c.received_date else None,
        "assigned_to": c.assigned_to, "related_case_id": c.related_case_id, "overlap_score": c.overlap_score
    } for c in inst.complaints if not c.is_confidential] if is_privileged_or_owner else []

    tasks = [{
        "id": t.id, "title": t.title, "category": t.category, "priority": t.priority,
        "status": t.status, "due_date": t.due_date.isoformat() if t.due_date else None,
        "assigned_to": t.assigned_to, "bureau": t.bureau
    } for t in inst.tasks] if is_privileged_or_owner else []

    corrections = [{
        "id": cr.id, "field_name": cr.field_name, "current_value": cr.current_value,
        "proposed_value": cr.proposed_value, "status": cr.status, "reported_by": cr.reported_by,
        "created_at": cr.created_at.strftime("%Y-%m-%d %H:%M:%S")
    } for cr in inst.correction_requests] if is_privileged_or_owner else []

    audit_records = []
    if is_privileged_or_owner:
        related_ids = [inst.id, inst.permanent_id] + [a.id for a in inst.applications] + [d.id for d in inst.documents] + [c.id for c in inst.compliance_obligations] + [c.id for c in inst.complaints]
        audits = db.query(AuditLog).filter(or_(
            AuditLog.entity_id.in_(related_ids),
            AuditLog.details.ilike(f"%{inst.name}%")
        )).order_by(desc(AuditLog.timestamp)).limit(15).all()

        audit_records = [{
            "id": a.id, "timestamp": a.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "actor": a.actor, "role": a.role, "action": a.action, "record": a.entity_id, "detail": a.details
        } for a in audits]

    return {
        "institution": {
            "id": inst.id,
            "permanent_id": inst.permanent_id,
            "aicte_id": inst.aicte_id or "—",
            "name": inst.name,
            "state": inst.state,
            "district": inst.district,
            "city": inst.city,
            "address": inst.address,
            "category": inst.category,
            "institution_type": inst.institution_type,
            "affiliation": inst.affiliation,
            "website": inst.website,
            "approval_status": inst.approval_status,
            "approval_period": inst.approval_period,
            "programmes_count": inst.programmes_count,
            "total_intake": inst.total_intake,
            "women_only": bool(inst.women_only),
            "minority": bool(inst.minority),
            "data_source": inst.data_source,
            "verified_status": inst.verified_status,
            "last_verified": inst.last_verified.isoformat() if inst.last_verified else None
        },
        "applications": apps,
        "documents": docs,
        "compliance_obligations": comps,
        "undertakings": undertakings,
        "document_validities": validities,
        "complaints": cases,
        "tasks": tasks,
        "correction_requests": corrections,
        "activity_timeline": audit_records,
        "tabs": {
            "applications": apps,
            "documents": docs,
            "compliance_obligations": comps,
            "undertakings": undertakings,
            "document_validities": validities,
            "complaints": cases,
            "tasks": tasks,
            "correction_requests": corrections,
            "activity_timeline": audit_records
        }
    }

# -------------------------------------------------------------
# 7. Authoritative Dataset Batch Importer Pipeline
# -------------------------------------------------------------
@router.post("/import/preview")
def preview_dataset_import(
    payload: ImportPreviewRequest,
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db)
):
    """
    Validates institutional data source file (defaulting to official all-institutions.txt),
    detects duplicates, and returns structured preview.
    """
    target_path = payload.file_path or os.path.join(os.path.dirname(__file__), "..", "..", "all-institutions.txt")
    if not os.path.exists(target_path):
        target_path = r"C:\Users\shiva\Downloads\all-institutions.txt"

    if not os.path.exists(target_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset file not found at: {target_path}"
        )

    records = institution_importer.load_records_from_source(target_path)
    if not records:
        raise HTTPException(status_code=400, detail="Failed to parse records from dataset file.")

    return institution_importer.validate_and_preview(records, db, preview_limit=payload.sample_limit or 15)

@router.post("/import/confirm")
def confirm_dataset_import(
    payload: ImportConfirmRequest,
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Executes official batch import of deduplicated institutional records.
    Restricted to Super Administrator.
    """
    target_path = payload.file_path or os.path.join(os.path.dirname(__file__), "..", "..", "all-institutions.txt")
    if not os.path.exists(target_path):
        target_path = r"C:\Users\shiva\Downloads\all-institutions.txt"

    if not os.path.exists(target_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset file not found at: {target_path}"
        )

    records = institution_importer.load_records_from_source(target_path)
    if not records:
        raise HTTPException(status_code=400, detail="Failed to parse records from dataset file.")

    summary = institution_importer.execute_import(
        raw_records=records,
        db=db,
        imported_by=user.username,
        source_name=os.path.basename(target_path),
        batch_limit=payload.batch_limit
    )
    return summary

@router.post("", response_model=InstitutionResponse)
def create_institution(
    payload: InstitutionCreate,
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    existing = db.query(Institution).filter(Institution.permanent_id == payload.permanent_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Institution with Permanent ID {payload.permanent_id} already exists.")

    new_id = payload.id or f"INST-{uuid.uuid4().hex[:6].upper()}"
    inst = Institution(
        id=new_id,
        name=payload.name,
        permanent_id=payload.permanent_id,
        state=payload.state,
        district=payload.district,
        city=payload.city,
        address=payload.address or "",
        category=payload.category,
        institution_type=payload.institution_type,
        affiliation=payload.affiliation,
        website=payload.website,
        approval_status=payload.approval_status or "Approved",
        approval_period=payload.approval_period or "2026-2027",
        programmes_count=payload.programmes_count or 0,
        total_intake=payload.total_intake or 0,
        data_source=payload.data_source or "Official AICTE Directory",
        verified_status=payload.verified_status or "Verified",
        last_verified=date.today()
    )
    db.add(inst)

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=user.username,
        role=user.role,
        action="Created Institution Record",
        entity_type="Institution",
        entity_id=inst.id,
        details=f"Added {inst.name} ({inst.permanent_id}) to institutional directory."
    )
    db.add(audit)
    db.commit()
    db.refresh(inst)
    return inst

def sanitize_csv_cell(val: Any) -> str:
    """Neutralizes OWASP CSV/Excel Formula Injection."""
    if val is None:
        return ""
    s = str(val).strip()
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{s}"
    return s

@router.get("/export-csv")
def export_institutions_csv(
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER, ROLE_COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db)
):
    """Exports all current institution records as a formatted CSV with audit trail."""
    institutions = db.query(Institution).order_by(Institution.name).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Institution ID", "Permanent ID", "AICTE ID", "Institution Name", "State", "District",
        "City", "Category", "Institution Type", "Affiliation", "Approval Status",
        "Approval Period", "Programmes", "Total Intake", "Data Source", "Verified Status"
    ])
    for inst in institutions:
        writer.writerow([
            sanitize_csv_cell(inst.id),
            sanitize_csv_cell(inst.permanent_id),
            sanitize_csv_cell(inst.aicte_id),
            sanitize_csv_cell(inst.name),
            sanitize_csv_cell(inst.state),
            sanitize_csv_cell(inst.district),
            sanitize_csv_cell(inst.city),
            sanitize_csv_cell(inst.category),
            sanitize_csv_cell(inst.institution_type),
            sanitize_csv_cell(inst.affiliation),
            sanitize_csv_cell(inst.approval_status),
            sanitize_csv_cell(inst.approval_period),
            sanitize_csv_cell(inst.programmes_count),
            sanitize_csv_cell(inst.total_intake),
            sanitize_csv_cell(inst.data_source),
            sanitize_csv_cell(inst.verified_status)
        ])

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=user.username,
        role=user.role,
        action="Exported Institution Directory CSV",
        entity_type="InstitutionMaster",
        entity_id="ALL",
        details=f"Exported {len(institutions)} institution records to CSV."
    )
    db.add(audit)
    db.commit()

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=aicte_institutions_directory.csv"}
    )
