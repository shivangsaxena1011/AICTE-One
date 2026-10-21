"""
Complaint Intelligence & Cross-Bureau Coordination Router
"""
import uuid
from typing import Optional, List
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Form
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models import Complaint, CoordinationLink, Institution, AuditLog
from backend.schemas import ComplaintCreate, CoordinationLinkCreate
from backend.services.overlap_detector import overlap_detector
from backend.auth import require_roles, ROLE_VIGILANCE, ROLE_ADMIN

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])

@router.get("")
def list_complaints(
    bureau: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    institution_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Complaint)
    if bureau:
        query = query.filter(Complaint.bureau == bureau)
    if status:
        query = query.filter(Complaint.status == status)
    if institution_id:
        query = query.filter(Complaint.institution_id == institution_id)

    complaints = query.order_by(desc(Complaint.received_date)).all()
    results = []
    for c in complaints:
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
            "resolution_notes": c.resolution_notes
        })
    return results

@router.post("")
def register_complaint(payload: ComplaintCreate, db: Session = Depends(get_db)):
    inst = db.query(Institution).filter(Institution.id == payload.institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    new_id = f"CASE-{uuid.uuid4().hex[:5].upper()}"
    cplt = Complaint(
        id=new_id,
        institution_id=payload.institution_id,
        case_number=f"GRV/{payload.bureau[:4]}/{uuid.uuid4().hex[:4].upper()}",
        bureau=payload.bureau,
        category=payload.category,
        summary=payload.summary,
        details=payload.details or payload.summary,
        channel=payload.channel or "Online Portal",
        status="Received",
        assigned_to=payload.assigned_to or "Unassigned",
        received_date=date.today(),
        due_date=payload.due_date
    )
    db.add(cplt)

    # Check for potential overlaps with other complaints for the same institution
    other_complaints = db.query(Complaint).filter(
        Complaint.institution_id == payload.institution_id,
        Complaint.id != new_id
    ).all()

    for other in other_complaints:
        overlap = overlap_detector.analyze_overlap(
            {"id": new_id, "institution_id": payload.institution_id, "category": payload.category, "summary": payload.summary, "details": payload.details},
            {"id": other.id, "institution_id": other.institution_id, "category": other.category, "summary": other.summary, "details": other.details}
        )
        if overlap["requires_coordination"]:
            cplt.related_case_id = other.id
            cplt.overlap_score = overlap["score"]
            cplt.overlap_reason = overlap["reason"]
            break

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=payload.assigned_to or "Grievance Officer",
        role="Grievance Cell",
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
def detect_case_overlaps(db: Session = Depends(get_db)):
    """
    Scans entire complaint registry and identifies potential cross-Bureau case overlaps.
    """
    complaints = db.query(Complaint).all()
    comp_dicts = [{
        "id": c.id, "institution_id": c.institution_id, "institution_name": c.institution.name if c.institution else "",
        "bureau": c.bureau, "category": c.category, "summary": c.summary, "details": c.details or ""
    } for c in complaints]

    overlaps = overlap_detector.scan_all_complaints(comp_dicts)
    return overlaps

@router.post("/link-coordination")
def confirm_coordination_link(payload: CoordinationLinkCreate, actor: str = "Central Admin Officer", db: Session = Depends(get_db)):
    """
    Confirms coordination relationship between two cases while preserving independent case histories.
    """
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
        coordinating_officer=payload.coordinating_officer or case_a.assigned_to,
        confirmed_by=actor,
        confirmed_at=datetime.now(timezone.utc)
    )
    db.add(link)

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=actor,
        role="Coordination Officer",
        action="Confirmed Case Relationship",
        entity_type="Coordination",
        entity_id=link.id,
        details=f"Linked {case_a.id} ({case_a.bureau}) and {case_b.id} ({case_b.bureau}). Rationale: {payload.rationale}."
    )
    db.add(audit)
    db.commit()
    return {"message": "Case coordination confirmed; independent case histories preserved.", "link_id": link.id}

@router.post("/{id}/transfer")
def transfer_complaint(id: str, new_bureau: str = Form(...), reason: str = Form(...), actor: str = Form("Grievance Officer"), db: Session = Depends(get_db)):
    cplt = db.query(Complaint).filter(Complaint.id == id).first()
    if not cplt:
        raise HTTPException(status_code=404, detail="Complaint not found")

    old_bureau = cplt.bureau
    cplt.bureau = new_bureau
    cplt.status = "Transferred"
    cplt.details = f"{cplt.details or ''}\n[Transferred from {old_bureau} to {new_bureau}: {reason}]"

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=actor,
        role="Grievance Cell",
        action="Transferred Complaint Case",
        entity_type="Complaint",
        entity_id=cplt.id,
        details=f"Transferred case from {old_bureau} to {new_bureau}. Reason: {reason}."
    )
    db.add(audit)
    db.commit()
    return {"message": f"Case transferred to {new_bureau}"}

@router.post("/{id}/dispose")
def dispose_complaint(
    id: str,
    resolution_notes: str = Form(...),
    actor: str = Form("Disposal Officer"),
    auth: dict = Depends(require_roles(ROLE_VIGILANCE, ROLE_ADMIN)),
    db: Session = Depends(get_db)
):
    cplt = db.query(Complaint).filter(Complaint.id == id).first()
    if not cplt:
        raise HTTPException(status_code=404, detail="Complaint not found")

    cplt.status = "Disposed or closed"
    cplt.resolution_notes = resolution_notes
    cplt.closed_at = datetime.now(timezone.utc)

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=actor,
        role="Disposal Authority",
        action="Disposed Complaint Case",
        entity_type="Complaint",
        entity_id=cplt.id,
        details=f"Case closed with resolution: {resolution_notes[:80]}..."
    )
    db.add(audit)
    db.commit()
    return {"message": "Case closed and disposed with recorded outcome"}
