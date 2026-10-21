"""
Applications & Approval Workflow Router
"""
import uuid
from typing import Optional, List
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from backend.database import get_db
from backend.models import Application, ApplicationStage, Institution, Document, AuditLog
from backend.schemas import ApplicationCreate, ApplicationStageTransition

router = APIRouter(prefix="/api/applications", tags=["Applications"])

PERMITTED_STAGES = [
    "Preliminary validation",
    "Scrutiny",
    "Re-scrutiny",
    "EVC scheduling",
    "EVC completed",
    "SAC/SHC review",
    "Awaiting clarification",
    "Further processing",
    "Authorized disposition"
]

@router.get("")
def list_applications(
    q: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    institution_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Application)
    if stage:
        query = query.filter(Application.current_stage == stage)
    if status:
        query = query.filter(Application.status == status)
    if institution_id:
        query = query.filter(Application.institution_id == institution_id)

    apps = query.order_by(desc(Application.submitted_at)).all()
    results = []
    for a in apps:
        if q:
            q_lower = q.lower()
            if not (q_lower in a.id.lower() or q_lower in a.institution.name.lower() or q_lower in a.institution.permanent_id.lower()):
                continue

        results.append({
            "id": a.id,
            "institution_id": a.institution_id,
            "institution_name": a.institution.name,
            "permanent_id": a.institution.permanent_id,
            "category": a.category,
            "type": a.type,
            "academic_year": a.academic_year,
            "current_stage": a.current_stage,
            "status": a.status,
            "owner": a.owner,
            "progress": a.progress,
            "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
            "due_date": a.due_date.isoformat() if a.due_date else None,
            "deficiency_count": a.deficiency_count,
            "last_action": a.last_action,
            "next_action": a.next_action,
            "docs_count": f"{len(a.documents)}/7"
        })
    return results

@router.get("/{id}")
def get_application(id: str, db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    docs = [{
        "id": d.id, "name": d.name, "document_type": d.document_type, "status": d.status,
        "confidence": d.confidence, "findings": d.findings, "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
        "authority_ref": d.authority_ref, "is_anomaly": d.is_anomaly
    } for d in app.documents]

    stages = [{
        "id": s.id, "stage_name": s.stage_name, "status": s.status, "actor": s.actor,
        "remarks": s.remarks, "deficiencies": s.deficiencies,
        "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S")
    } for s in app.stages]

    return {
        "id": app.id,
        "institution_id": app.institution_id,
        "institution_name": app.institution.name,
        "permanent_id": app.institution.permanent_id,
        "category": app.category,
        "type": app.type,
        "academic_year": app.academic_year,
        "current_stage": app.current_stage,
        "status": app.status,
        "owner": app.owner,
        "progress": app.progress,
        "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
        "due_date": app.due_date.isoformat() if app.due_date else None,
        "deficiency_count": app.deficiency_count,
        "last_action": app.last_action,
        "next_action": app.next_action,
        "documents": docs,
        "stages": stages
    }

@router.post("")
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    inst = db.query(Institution).filter(Institution.id == payload.institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    new_id = f"APP-2026-{uuid.uuid4().hex[:4].upper()}"
    app = Application(
        id=new_id,
        institution_id=payload.institution_id,
        category=payload.category,
        type=payload.type,
        academic_year=payload.academic_year,
        current_stage="Preliminary validation",
        status="New submission",
        owner=payload.owner or "Intake Officer",
        progress=15,
        submitted_at=date.today(),
        due_date=payload.due_date,
        last_action="Application submitted for preliminary scrutiny",
        next_action="Perform automated document verification checklist"
    )
    db.add(app)

    # Initial stage log
    stage_log = ApplicationStage(
        id=f"STG-{uuid.uuid4().hex[:6].upper()}",
        application_id=app.id,
        stage_name="Preliminary validation",
        status="Initialized",
        actor=payload.owner or "Intake Officer",
        remarks="New application lodged in system."
    )
    db.add(stage_log)

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=payload.owner or "Admin Officer",
        role="Approval Officer",
        action="Created Approval Application",
        entity_type="Application",
        entity_id=app.id,
        details=f"Created {app.type} for {inst.name} ({inst.permanent_id})."
    )
    db.add(audit)
    db.commit()
    db.refresh(app)
    return app

@router.post("/{id}/transition")
def transition_application_stage(id: str, payload: ApplicationStageTransition, db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    old_stage = app.current_stage
    app.current_stage = payload.next_stage
    app.status = payload.status
    app.owner = payload.actor
    app.last_action = payload.remarks or f"Transitioned from {old_stage} to {payload.next_stage}"

    # Calculate progress indicator
    progress_map = {
        "Preliminary validation": 20,
        "Scrutiny": 40,
        "Re-scrutiny": 50,
        "EVC scheduling": 65,
        "EVC completed": 80,
        "SAC/SHC review": 90,
        "Authorized disposition": 100
    }
    app.progress = progress_map.get(payload.next_stage, app.progress)

    deficiencies_text = "; ".join(payload.deficiencies) if payload.deficiencies else None
    if payload.deficiencies:
        app.deficiency_count = len(payload.deficiencies)

    stage_log = ApplicationStage(
        id=f"STG-{uuid.uuid4().hex[:6].upper()}",
        application_id=app.id,
        stage_name=payload.next_stage,
        status=payload.status,
        actor=payload.actor,
        remarks=payload.remarks,
        deficiencies=deficiencies_text
    )
    db.add(stage_log)

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=payload.actor,
        role="Scrutiny Officer",
        action="Stage Transition",
        entity_type="Application",
        entity_id=app.id,
        details=f"Advanced {app.id} from '{old_stage}' to '{payload.next_stage}'. Status: '{payload.status}'."
    )
    db.add(audit)
    db.commit()
    return {"message": "Stage transitioned successfully", "current_stage": app.current_stage, "status": app.status}

@router.post("/{id}/return-deficiency")
def return_for_rectification(id: str, actor: str, deficiencies: List[str], remarks: str, db: Session = Depends(get_db)):
    """
    Returns application to institution with a formal deficiency checklist.
    """
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.current_stage = "Re-scrutiny"
    app.status = "Returned for rectification"
    app.deficiency_count = len(deficiencies)
    app.last_action = f"Returned with {len(deficiencies)} deficiencies: {remarks}"
    app.next_action = "Awaiting rectified compliance documents from institution"

    stage_log = ApplicationStage(
        id=f"STG-{uuid.uuid4().hex[:6].upper()}",
        application_id=app.id,
        stage_name="Re-scrutiny",
        status="Returned for rectification",
        actor=actor,
        remarks=remarks,
        deficiencies="; ".join(deficiencies)
    )
    db.add(stage_log)

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=actor,
        role="Scrutiny Committee",
        action="Returned for Deficiencies",
        entity_type="Application",
        entity_id=app.id,
        details=f"Returned with {len(deficiencies)} deficiencies to institution."
    )
    db.add(audit)
    db.commit()
    return {"message": "Application returned with deficiency checklist", "deficiency_count": len(deficiencies)}
