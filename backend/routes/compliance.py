"""
Compliance & Regulatory Obligations Router
"""
import uuid
from typing import Optional
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models import ComplianceObligation, Institution, AuditLog
from backend.schemas import ComplianceCreate, ComplianceResponse

router = APIRouter(prefix="/api/compliance", tags=["Compliance"])

@router.get("")
def list_compliance(
    status: Optional[str] = Query(None),
    institution_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(ComplianceObligation)
    if status:
        query = query.filter(ComplianceObligation.status == status)
    if institution_id:
        query = query.filter(ComplianceObligation.institution_id == institution_id)

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
def create_compliance_obligation(payload: ComplianceCreate, db: Session = Depends(get_db)):
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
        actor="Compliance Officer",
        role="Compliance Division",
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
    actor: Optional[str] = Form("Institution Representative"),
    db: Session = Depends(get_db)
):
    comp = db.query(ComplianceObligation).filter(ComplianceObligation.id == id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Obligation not found")

    content_type = request.headers.get("content-type", "")
    req_fname = evidence_filename
    req_actor = actor

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
        actor=req_actor or "Institution Representative",
        role="Institution User",
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
    decision: Optional[str] = Form(None), # "Satisfied by evidence", "Action required", "Overdue"
    notes: Optional[str] = Form(None),
    reviewer: Optional[str] = Form("Compliance Officer"),
    db: Session = Depends(get_db)
):
    comp = db.query(ComplianceObligation).filter(ComplianceObligation.id == id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Obligation not found")

    content_type = request.headers.get("content-type", "")
    req_decision = decision
    req_notes = notes
    req_reviewer = reviewer

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
    comp.reviewed_by = req_reviewer or "Compliance Officer"
    comp.reviewed_at = datetime.now(timezone.utc)

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=comp.reviewed_by,
        role="Compliance Officer",
        action="Reviewed Compliance Obligation",
        entity_type="Compliance",
        entity_id=comp.id,
        details=f"Marked '{comp.title}' as '{req_decision}'. Notes: {req_notes}."
    )
    db.add(audit)
    db.commit()
    return {"message": "Review recorded successfully", "status": comp.status}
