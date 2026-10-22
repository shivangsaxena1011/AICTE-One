"""
Complaint Intelligence & Cross-Bureau Coordination Router
Protected with RBAC, Case-Level Privacy & Whistleblower Protection
"""
import uuid
from typing import Optional, List
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Form, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from backend.database import get_db
from backend.models import Complaint, CoordinationLink, Institution, AuditLog, User
from backend.schemas import ComplaintCreate, CoordinationLinkCreate, ComplaintTriageRequest, ComplaintTriageResponse
from backend.services.overlap_detector import overlap_detector
from backend.services.complaint_ai_service import complaint_ai_service
from backend.auth import (
    get_current_user, require_roles,
    ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER, ROLE_COMPLAINT_OFFICER,
    ROLE_ANTI_RAGGING_OFFICER, ROLE_INSTITUTE_HEAD,
    ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR
)

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])

@router.get("")
def list_complaints(
    bureau: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    institution_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves complaints scoped by role permissions and data isolation policies:
    - Students see ONLY their own submitted grievances.
    - Institute Heads see non-confidential grievances filed against their own institution.
    - Anti-Ragging officers see ragging-related safety cases.
    - Central Complaint Officers and Admins see statutory bureau cases.
    - Public visitors receive 403 Forbidden.
    """
    if user.role == ROLE_PUBLIC_VISITOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Complaint registry is not accessible to anonymous public visitors."
        )

    query = db.query(Complaint)

    # 1. Complainant Isolation
    if user.role == ROLE_STUDENT_COMPLAINANT:
        query = query.filter(Complaint.complainant_id == user.id)

    # 2. Institutional Isolation
    elif user.role == ROLE_INSTITUTE_HEAD:
        if not user.institution_id:
            return []
        query = query.filter(
            Complaint.institution_id == user.institution_id,
            Complaint.is_confidential == False
        )

    # 3. Anti-Ragging Committee Isolation
    elif user.role == ROLE_ANTI_RAGGING_OFFICER:
        query = query.filter(
            or_(
                Complaint.ragging_flag == True,
                Complaint.category.ilike("%ragging%"),
                Complaint.bureau.ilike("%ragging%"),
                Complaint.assigned_to == user.full_name
            )
        )

    # General filters
    if bureau:
        query = query.filter(Complaint.bureau == bureau)
    if status_filter:
        query = query.filter(Complaint.status == status_filter)
    if institution_id and user.role != ROLE_INSTITUTE_HEAD:
        query = query.filter(Complaint.institution_id == institution_id)

    complaints = query.order_by(desc(Complaint.received_date)).all()
    results = []
    for c in complaints:
        # Hide internal resolution drafts from students before disposal
        res_notes = c.resolution_notes
        if user.role == ROLE_STUDENT_COMPLAINANT and c.status != "Disposed or closed":
            res_notes = "Under active investigation by AICTE Grievance Committee"

        results.append({
            "id": c.id,
            "case_number": c.case_number or c.id,
            "institution_id": c.institution_id,
            "institution_name": c.institution.name if c.institution else "Unknown",
            "permanent_id": c.institution.permanent_id if c.institution else "Unknown",
            "bureau": c.bureau,
            "category": c.category,
            "summary": c.summary,
            "details": c.details,
            "channel": c.channel,
            "status": c.status,
            "assigned_to": c.assigned_to,
            "received_date": c.received_date.isoformat() if c.received_date else None,
            "due_date": c.due_date.isoformat() if c.due_date else None,
            "related_case_id": c.related_case_id,
            "overlap_score": c.overlap_score,
            "overlap_reason": c.overlap_reason,
            "resolution_notes": res_notes
        })
    return results

@router.post("")
def register_complaint(
    payload: ComplaintCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    inst = db.query(Institution).filter(Institution.id == payload.institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    is_ragging = "ragging" in (payload.category + " " + payload.summary).lower()
    new_id = f"CASE-{uuid.uuid4().hex[:5].upper()}"
    cplt = Complaint(
        id=new_id,
        institution_id=payload.institution_id,
        complainant_id=user.id,
        case_number=f"GRV/{payload.bureau[:4]}/{uuid.uuid4().hex[:4].upper()}",
        bureau=payload.bureau,
        category=payload.category,
        summary=payload.summary,
        details=payload.details or payload.summary,
        channel=payload.channel or "Online Portal",
        status="Received",
        assigned_to=payload.assigned_to or "Unassigned",
        received_date=date.today(),
        due_date=payload.due_date,
        is_confidential=False,
        ragging_flag=is_ragging
    )
    db.add(cplt)

    # Overlap detection against existing complaints for this institution
    other_complaints = db.query(Complaint).filter(
        Complaint.institution_id == payload.institution_id,
        Complaint.id != new_id
    ).all()

    for other in other_complaints:
        overlap = overlap_detector.analyze_overlap(
            {"id": new_id, "institution_id": payload.institution_id, "category": payload.category, "summary": payload.summary, "details": payload.details},
            {"id": other.id, "institution_id": other.institution_id, "category": other.category, "summary": other.summary, "details": other.details}
        )
        if overlap.get("requires_coordination"):
            cplt.related_case_id = other.id
            cplt.overlap_score = overlap.get("score", 0)
            cplt.overlap_reason = overlap.get("reason")
            break

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=user.username,
        role=user.role,
        action="Registered Complaint Case",
        entity_type="Complaint",
        entity_id=cplt.id,
        details=f"Registered complaint for {inst.name}. Bureau: '{payload.bureau}'. Category: '{payload.category}'."
    )
    db.add(audit)
    db.commit()
    db.refresh(cplt)
    return {"message": "Complaint registered successfully", "id": cplt.id, "related_case": cplt.related_case_id}

@router.get("/overlaps")
@router.get("/detect-overlap")
@router.post("/detect-overlap")
def detect_case_overlaps(
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLAINT_OFFICER, ROLE_SECURITY_OFFICER, ROLE_ANTI_RAGGING_OFFICER)),
    db: Session = Depends(get_db)
):
    """
    Scans entire complaint registry and identifies potential cross-Bureau case overlaps.
    Restricted to statutory regulatory officers.
    """
    complaints = db.query(Complaint).all()
    comp_dicts = [{
        "id": c.id, "institution_id": c.institution_id, "institution_name": c.institution.name if c.institution else "",
        "bureau": c.bureau, "category": c.category, "summary": c.summary, "details": c.details or ""
    } for c in complaints]

    overlaps = overlap_detector.scan_all_complaints(comp_dicts)
    return overlaps

@router.post("/link-coordination")
def confirm_coordination_link(
    payload: CoordinationLinkCreate,
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLAINT_OFFICER, ROLE_SECURITY_OFFICER)),
    db: Session = Depends(get_db)
):
    case_a = db.query(Complaint).filter(Complaint.id == payload.case_a_id).first()
    case_b = db.query(Complaint).filter(Complaint.id == payload.case_b_id).first()
    if not case_a or not case_b:
        raise HTTPException(status_code=404, detail="One or both complaints not found")

    case_a.related_case_id = case_b.id
    case_b.related_case_id = case_a.id

    new_id = f"COORD-{uuid.uuid4().hex[:5].upper()}"
    link = CoordinationLink(
        id=new_id,
        case_a_id=case_a.id,
        case_b_id=case_b.id,
        status="Confirmed",
        confidence_score=94,
        rationale=payload.rationale,
        coordinating_bureau=payload.coordinating_bureau or case_a.bureau,
        coordinating_officer=payload.coordinating_officer or user.full_name,
        confirmed_by=user.username,
        confirmed_at=datetime.now(timezone.utc)
    )
    db.add(link)

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=user.username,
        role=user.role,
        action="Confirmed Case Relationship",
        entity_type="Coordination",
        entity_id=link.id,
        details=f"Linked {case_a.id} ({case_a.bureau}) and {case_b.id} ({case_b.bureau}). Rationale: {payload.rationale}."
    )
    db.add(audit)
    db.commit()
    return {"message": "Case coordination confirmed; independent case histories preserved.", "link_id": link.id}

@router.post("/{id}/transfer")
async def transfer_complaint(
    id: str,
    request: Request,
    new_bureau: Optional[str] = Form(None),
    reason: Optional[str] = Form(None),
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLAINT_OFFICER, ROLE_ANTI_RAGGING_OFFICER)),
    db: Session = Depends(get_db)
):
    cplt = db.query(Complaint).filter(Complaint.id == id).first()
    if not cplt:
        raise HTTPException(status_code=404, detail="Complaint not found")

    content_type = request.headers.get("content-type", "")
    req_bureau = new_bureau
    req_reason = reason

    if "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict):
                req_bureau = body.get("new_bureau") or body.get("bureau") or req_bureau
                req_reason = body.get("reason") or body.get("transfer_reason") or req_reason
        except Exception:
            pass

    if not req_bureau:
        raise HTTPException(status_code=400, detail="Target bureau is required")
    if not req_reason:
        req_reason = "Administrative reassignment"

    old_bureau = cplt.bureau
    cplt.bureau = req_bureau
    cplt.status = "Transferred"
    cplt.details = f"{cplt.details or ''}\n[Transferred from {old_bureau} to {req_bureau}: {req_reason}]"

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=user.username,
        role=user.role,
        action="Transferred Complaint Case",
        entity_type="Complaint",
        entity_id=cplt.id,
        details=f"Transferred case from {old_bureau} to {req_bureau}. Reason: {req_reason}."
    )
    db.add(audit)
    db.commit()
    return {"message": f"Case transferred to {req_bureau}"}

@router.post("/{id}/dispose")
async def dispose_complaint(
    id: str,
    request: Request,
    resolution_notes: Optional[str] = Form(None),
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLAINT_OFFICER, ROLE_ANTI_RAGGING_OFFICER)),
    db: Session = Depends(get_db)
):
    cplt = db.query(Complaint).filter(Complaint.id == id).first()
    if not cplt:
        raise HTTPException(status_code=404, detail="Complaint not found")

    content_type = request.headers.get("content-type", "")
    req_notes = resolution_notes

    if "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict):
                req_notes = body.get("resolution_notes") or body.get("notes") or req_notes
        except Exception:
            pass

    if not req_notes:
        raise HTTPException(status_code=400, detail="Resolution notes are required")

    cplt.status = "Disposed or closed"
    cplt.resolution_notes = req_notes
    cplt.closed_at = datetime.now(timezone.utc)

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=user.username,
        role=user.role,
        action="Disposed Complaint Case",
        entity_type="Complaint",
        entity_id=cplt.id,
        details=f"Case closed with resolution: {req_notes[:80]}..."
    )
    db.add(audit)
    db.commit()
    return {"message": "Case closed and disposed with recorded outcome"}

# -------------------------------------------------------------
# AI-Assisted Complaint Analysis & Triage
# -------------------------------------------------------------
@router.post("/triage-preview", response_model=ComplaintTriageResponse)
def preview_complaint_triage(
    payload: ComplaintTriageRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Previews AI categorization, urgency recommendation, missing entity detection,
    and potential duplicate warnings before case submission.
    """
    existing_cases = []
    if payload.institution_id:
        existing = db.query(Complaint).filter(Complaint.institution_id == payload.institution_id).all()
        existing_cases = [{"id": c.id, "case_number": c.case_number or c.id, "summary": c.summary, "details": c.details or "", "category": c.category} for c in existing]

    inst_name = ""
    if payload.institution_id:
        inst = db.query(Institution).filter(Institution.id == payload.institution_id).first()
        inst_name = inst.name if inst else ""

    return complaint_ai_service.analyze_complaint(
        summary=payload.summary,
        details=payload.details,
        institution_name=inst_name,
        existing_cases=existing_cases
    )

@router.post("/{id}/ai-triage", response_model=ComplaintTriageResponse)
def execute_complaint_ai_triage(
    id: str,
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLAINT_OFFICER, ROLE_ANTI_RAGGING_OFFICER)),
    db: Session = Depends(get_db)
):
    """
    Executes or updates AI triage for an existing registered grievance.
    Stores analysis in case record without altering legal status.
    """
    cplt = db.query(Complaint).filter(Complaint.id == id).first()
    if not cplt:
        raise HTTPException(status_code=404, detail="Complaint not found")

    other_cases = db.query(Complaint).filter(Complaint.id != cplt.id, Complaint.institution_id == cplt.institution_id).all()
    existing_cases = [{"id": c.id, "case_number": c.case_number or c.id, "summary": c.summary, "details": c.details or "", "category": c.category} for c in other_cases]

    inst_name = cplt.institution.name if cplt.institution else ""

    result = complaint_ai_service.analyze_complaint(
        summary=cplt.summary,
        details=cplt.details,
        institution_name=inst_name,
        existing_cases=existing_cases
    )

    import json
    cplt.ai_triage_json = json.dumps(result)
    cplt.triage_urgency = result["recommended_urgency"]
    cplt.missing_info_flags = "; ".join(result["missing_mandatory_information"])
    db.commit()

    return result

@router.get("/triage-queue")
def get_complaint_triage_queue(
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLAINT_OFFICER, ROLE_ANTI_RAGGING_OFFICER)),
    db: Session = Depends(get_db)
):
    """
    Returns grievances prioritized by AI triage urgency and unresolved overlaps.
    """
    query = db.query(Complaint).filter(
        Complaint.status.notin_(["Disposed or closed", "Resolved", "Closed"])
    )

    if user.role == ROLE_ANTI_RAGGING_OFFICER:
        query = query.filter(
            or_(Complaint.ragging_flag == True, Complaint.category.ilike("%ragging%"), Complaint.triage_urgency == "Critical")
        )

    complaints = query.order_by(
        desc(Complaint.triage_urgency == "Critical"),
        desc(Complaint.triage_urgency == "High"),
        desc(Complaint.received_date)
    ).limit(30).all()

    items = []
    for c in complaints:
        items.append({
            "id": c.id,
            "case_number": c.case_number or c.id,
            "institution_id": c.institution_id,
            "institution_name": c.institution.name if c.institution else "Unknown",
            "bureau": c.bureau,
            "category": c.category,
            "summary": c.summary,
            "status": c.status,
            "triage_urgency": c.triage_urgency or "Normal",
            "received_date": c.received_date.isoformat() if c.received_date else None,
            "missing_info_flags": c.missing_info_flags,
            "overlap_score": c.overlap_score or 0
        })
    return {
        "total_active_triage_items": len(items),
        "queue": items
    }

