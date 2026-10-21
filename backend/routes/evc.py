"""
EVC Scheduling & Pendency Router
"""
import uuid
from typing import Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Form, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models import EVCSchedule, Application, Institution, AuditLog
from backend.schemas import EVCCreate, EVCResponse

router = APIRouter(prefix="/api/evc", tags=["EVC Scheduling"])

@router.get("")
@router.get("/sessions")
def list_evc_schedules(status: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(EVCSchedule)
    if status:
        query = query.filter(EVCSchedule.status == status)

    schedules = query.order_by(desc(EVCSchedule.scheduled_date)).all()
    results = []
    for s in schedules:
        app = db.query(Application).filter(Application.id == s.application_id).first()
        inst = db.query(Institution).filter(Institution.id == s.institution_id).first()
        results.append({
            "id": s.id,
            "application_id": s.application_id,
            "institution_id": s.institution_id,
            "institution_name": inst.name if inst else "Unknown",
            "permanent_id": inst.permanent_id if inst else "Unknown",
            "application_type": app.type if app else "Unknown",
            "visit_type": s.visit_type,
            "scheduled_date": s.scheduled_date.isoformat(),
            "status": s.status,
            "committee_chair": s.committee_chair,
            "committee_members": s.committee_members,
            "report_submitted": s.report_submitted,
            "observations": s.observations,
            "remarks": s.remarks
        })
    return results

@router.post("/schedule")
def schedule_evc(payload: EVCCreate, db: Session = Depends(get_db)):
    app = db.query(Application).filter(Application.id == payload.application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    new_id = f"EVC-2026-{uuid.uuid4().hex[:4].upper()}"
    evc = EVCSchedule(
        id=new_id,
        application_id=payload.application_id,
        institution_id=payload.institution_id or app.institution_id,
        visit_type=payload.visit_type or "Physical Visit",
        scheduled_date=payload.scheduled_date,
        status="Scheduled",
        committee_chair=payload.committee_chair,
        committee_members=payload.committee_members,
        report_submitted=False,
        observations=payload.observations,
        remarks=payload.remarks
    )
    db.add(evc)

    # Update application stage to EVC scheduled
    app.current_stage = "EVC scheduling"
    app.status = "EVC scheduled"
    app.last_action = f"EVC visit scheduled on {payload.scheduled_date.isoformat()} by {payload.committee_chair}"
    app.next_action = "Conduct on-site inspection and submit visit report"

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=payload.committee_chair,
        role="EVC Coordinator",
        action="Scheduled EVC Visit",
        entity_type="EVC",
        entity_id=evc.id,
        details=f"Scheduled {payload.visit_type} on {payload.scheduled_date.isoformat()} for Application {app.id}."
    )
    db.add(audit)
    db.commit()
    db.refresh(evc)
    return {"message": "EVC scheduled successfully", "evc_id": evc.id}

@router.put("/{id}/reschedule")
@router.post("/{id}/reschedule")
async def reschedule_evc(
    id: str,
    request: Request,
    new_date: Optional[date] = Query(None),
    reason: Optional[str] = Query(None),
    actor: Optional[str] = Query("EVC Coordinator"),
    db: Session = Depends(get_db)
):
    evc = db.query(EVCSchedule).filter(EVCSchedule.id == id).first()
    if not evc:
        raise HTTPException(status_code=404, detail="EVC record not found")

    content_type = request.headers.get("content-type", "")
    req_date = new_date
    req_reason = reason
    req_actor = actor

    if "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict):
                if body.get("new_date"):
                    from datetime import date as dt_date
                    req_date = dt_date.fromisoformat(str(body["new_date"]))
                req_reason = body.get("reason") or req_reason
                req_actor = body.get("actor") or req_actor
        except Exception:
            pass

    if not req_date:
        req_date = date.today()
    if not req_reason:
        req_reason = "Administrative rescheduling"

    old_date = evc.scheduled_date
    evc.scheduled_date = req_date
    evc.remarks = f"Rescheduled from {old_date.isoformat()} to {req_date.isoformat()}. Reason: {req_reason}"

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=req_actor or "EVC Coordinator",
        role="EVC Coordinator",
        action="Rescheduled EVC Visit",
        entity_type="EVC",
        entity_id=evc.id,
        details=f"Rescheduled visit from {old_date.isoformat()} to {req_date.isoformat()} for Application {evc.application_id}. Reason: {req_reason}"
    )
    db.add(audit)
    db.commit()
    return {"message": "EVC rescheduled successfully", "new_date": req_date.isoformat()}

@router.post("/{id}/complete")
async def complete_evc(
    id: str,
    request: Request,
    observations: Optional[str] = Query(None),
    actor: Optional[str] = Query("EVC Chair"),
    db: Session = Depends(get_db)
):
    evc = db.query(EVCSchedule).filter(EVCSchedule.id == id).first()
    if not evc:
        raise HTTPException(status_code=404, detail="EVC record not found")

    content_type = request.headers.get("content-type", "")
    req_obs = observations
    req_actor = actor

    if "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict):
                req_obs = body.get("observations") or body.get("remarks") or req_obs
                req_actor = body.get("actor") or req_actor
        except Exception:
            pass

    if not req_obs:
        req_obs = "EVC inspection completed; infrastructure, laboratories, and faculty cadre verified."

    evc.status = "Completed"
    evc.report_submitted = True
    evc.observations = req_obs

    # Advance application
    app = db.query(Application).filter(Application.id == evc.application_id).first()
    if app:
        app.current_stage = "EVC completed"
        app.status = "In review"
        app.progress = 80
        app.last_action = f"EVC report submitted: {req_obs[:80]}..."
        app.next_action = "Submit to Standing Appellate Committee (SAC) for final appraisal"

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=req_actor or "EVC Chair",
        role="EVC Committee",
        action="Completed EVC Inspection",
        entity_type="EVC",
        entity_id=evc.id,
        details=f"Inspection completed and report filed for Application {evc.application_id}."
    )
    db.add(audit)
    db.commit()
    return {"message": "EVC marked completed and report filed"}
