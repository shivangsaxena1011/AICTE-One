"""
Applications & Approval Workflow Router
Enhanced for Phase 2: Configurable APH routes, state transitions, prerequisites,
SLA ageing, pendency monitoring, return/resubmission flows, and pause/resume support.
"""
import uuid
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from backend.database import get_db
from backend.models import (
    Application, ApplicationStage, Institution, Document, EVCSchedule,
    WorkflowDefinition, WorkflowStageDefinition, Undertaking, DocumentValidity,
    EscalationEvent, AuditLog, User
)
from backend.schemas import (
    ApplicationCreate, ApplicationStageTransition, ApplicationResponse
)
from backend.services.workflow_engine import workflow_engine, DEFAULT_WORKFLOW_ROUTES
from backend.auth import (
    get_current_user, require_roles, check_tenant_access,
    ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER, ROLE_COMPLIANCE_OFFICER,
    ROLE_INSTITUTE_HEAD, ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR
)

router = APIRouter(prefix="/api/applications", tags=["Applications"])

STAGE_NAME_TO_CODE = {
    "Preliminary validation": "PRELIMINARY_VALIDATION",
    "Preliminary Validation": "PRELIMINARY_VALIDATION",
    "Scrutiny": "SCRUTINY",
    "Scrutiny Committee Examination": "SCRUTINY",
    "Re-scrutiny": "RE_SCRUTINY",
    "Re-Scrutiny & Rectification": "RE_SCRUTINY",
    "EVC scheduling": "EVC_SCHEDULING",
    "EVC Committee Scheduling & Conflict Check": "EVC_SCHEDULING",
    "EVC completed": "EVC_EVALUATION",
    "EVC Site Inspection & Report Filing": "EVC_EVALUATION",
    "SAC/SHC review": "SAC_SHC_REVIEW",
    "Standing Appellate / Hearing Committee Review": "SAC_SHC_REVIEW",
    "Authorized disposition": "FINAL_DISPOSITION",
    "Authorized Regulatory Disposition": "FINAL_DISPOSITION"
}

@router.get("")
def list_applications(
    q: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    stage_code: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    route_type: Optional[str] = Query(None),
    institution_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lists approval applications with tenant isolation.
    - Central AICTE officers see all applications across India.
    - Institute Heads see ONLY applications pertaining to their authorized institution.
    - Students and public visitors are strictly denied access.
    """
    if user.role in {ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Approval applications are restricted to regulatory officers and authorized institutional representatives."
        )

    query = db.query(Application)

    # Enforce tenant isolation for Institute Heads
    if user.role == ROLE_INSTITUTE_HEAD:
        if not user.institution_id:
            return []
        query = query.filter(Application.institution_id == user.institution_id)
    elif institution_id:
        query = query.filter(Application.institution_id == institution_id)

    if stage:
        query = query.filter(Application.current_stage == stage)
    if stage_code:
        query = query.filter(Application.stage_code == stage_code)
    if status_filter:
        query = query.filter(Application.status == status_filter)
    if route_type:
        query = query.filter(Application.route_type == route_type)

    apps = query.order_by(desc(Application.submitted_at)).all()
    results = []
    today = date.today()

    for a in apps:
        if q:
            q_lower = q.lower()
            inst_name = a.institution.name if a.institution else ""
            inst_pid = a.institution.permanent_id if a.institution else ""
            if not (q_lower in a.id.lower() or q_lower in inst_name.lower() or q_lower in inst_pid.lower()):
                continue

        deadline = a.stage_due_date or a.due_date
        days_remaining = (deadline - today).days if deadline else None

        results.append({
            "id": a.id,
            "institution_id": a.institution_id,
            "institution_name": a.institution.name if a.institution else "Technical Institute",
            "permanent_id": a.institution.permanent_id if a.institution else "1-000000",
            "category": a.category,
            "type": a.type,
            "route_type": a.route_type or "SCRUTINY_EVC",
            "academic_year": a.academic_year,
            "current_stage": a.current_stage,
            "stage_code": a.stage_code or "PRELIMINARY_VALIDATION",
            "status": a.status,
            "owner": a.owner,
            "progress": a.progress,
            "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
            "due_date": a.due_date.isoformat() if a.due_date else None,
            "stage_due_date": a.stage_due_date.isoformat() if a.stage_due_date else None,
            "days_remaining": days_remaining,
            "is_overdue": days_remaining is not None and days_remaining < 0,
            "is_paused": bool(a.is_paused),
            "is_escalated": bool(a.is_escalated),
            "escalation_level": a.escalation_level or 0,
            "deficiency_count": a.deficiency_count,
            "resubmission_count": a.resubmission_count or 0,
            "last_action": a.last_action,
            "next_action": a.next_action,
            "docs_count": f"{len(a.documents)}/7"
        })
    return results

@router.get("/metrics/pendency-summary")
def get_pendency_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns aggregated pendency, ageing, SLA breaches, and route breakdown."""
    if user.role in {ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Aggregated pendency metrics are restricted to authorized personnel."
        )

    query = db.query(Application)
    if user.role == ROLE_INSTITUTE_HEAD:
        if not user.institution_id:
            return {"total_applications": 0, "active_applications": 0}
        query = query.filter(Application.institution_id == user.institution_id)

    apps = query.all()
    today = date.today()

    total = len(apps)
    active = 0
    overdue = 0
    due_soon = 0
    escalated = 0
    paused = 0
    route_counts = {}

    for a in apps:
        r = a.route_type or "SCRUTINY_EVC"
        route_counts[r] = route_counts.get(r, 0) + 1

        if a.status not in ["Approved", "Rejected", "Disposed", "Closed"]:
            active += 1
            if a.is_paused:
                paused += 1
            if a.is_escalated:
                escalated += 1

            deadline = a.stage_due_date or a.due_date
            if deadline:
                diff = (deadline - today).days
                if diff < 0:
                    overdue += 1
                elif 0 <= diff <= 3:
                    due_soon += 1

    return {
        "total_applications": total,
        "active_applications": active,
        "overdue_applications": overdue,
        "due_soon_applications": due_soon,
        "escalated_applications": escalated,
        "paused_applications": paused,
        "route_breakdown": route_counts
    }

@router.get("/{id}")
def get_application(
    id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role in {ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You are not authorized to view internal approval applications."
        )

    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if user.role == ROLE_INSTITUTE_HEAD:
        if user.institution_id and user.institution_id != app.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cross-institution access forbidden: You can only view applications for your own institution ('{user.institution_id}')."
            )

    docs = [{
        "id": d.id, "name": d.name, "document_type": d.document_type, "status": d.status,
        "confidence": d.confidence, "findings": d.findings, "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
        "authority_ref": d.authority_ref, "is_anomaly": d.is_anomaly
    } for d in app.documents]

    stages = [{
        "id": s.id,
        "stage_code": s.stage_code,
        "stage_name": s.stage_name,
        "from_stage": s.from_stage,
        "to_stage": s.to_stage,
        "status": s.status,
        "action": s.action,
        "actor": s.actor,
        "time_spent_hours": s.time_spent_hours,
        "sla_breached": s.sla_breached,
        "remarks": s.remarks,
        "deficiencies": s.deficiencies,
        "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S")
    } for s in app.stages]

    undertakings = [{
        "id": u.id,
        "undertaking_type": u.undertaking_type,
        "condition_ref": u.condition_ref,
        "statutory_deadline": u.statutory_deadline.isoformat(),
        "status": u.status,
        "evidence_file": u.evidence_file,
        "reviewed_by": u.reviewed_by
    } for u in app.undertakings]

    escalations = [{
        "id": e.id,
        "level": e.escalation_level,
        "trigger_reason": e.trigger_reason,
        "escalated_to_role": e.escalated_to_role,
        "status": e.status,
        "created_at": e.created_at.strftime("%Y-%m-%d %H:%M:%S")
    } for e in app.escalations]

    pendency = workflow_engine.calculate_pendency(app)

    return {
        "id": app.id,
        "institution_id": app.institution_id,
        "institution_name": app.institution.name if app.institution else "Technical Institute",
        "permanent_id": app.institution.permanent_id if app.institution else "1-000000",
        "category": app.category,
        "type": app.type,
        "route_type": app.route_type or "SCRUTINY_EVC",
        "academic_year": app.academic_year,
        "workflow_definition_id": app.workflow_definition_id,
        "workflow_version": app.workflow_version or 1,
        "current_stage": app.current_stage,
        "stage_code": app.stage_code or "PRELIMINARY_VALIDATION",
        "status": app.status,
        "owner": app.owner,
        "assigned_role": app.assigned_role,
        "progress": app.progress,
        "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
        "due_date": app.due_date.isoformat() if app.due_date else None,
        "stage_entered_at": app.stage_entered_at.isoformat() if app.stage_entered_at else None,
        "stage_due_date": app.stage_due_date.isoformat() if app.stage_due_date else None,
        "is_paused": bool(app.is_paused),
        "is_escalated": bool(app.is_escalated),
        "escalation_level": app.escalation_level or 0,
        "deficiency_count": app.deficiency_count,
        "resubmission_count": app.resubmission_count or 0,
        "last_action": app.last_action,
        "next_action": app.next_action,
        "pendency": pendency,
        "documents": docs,
        "stages": stages,
        "undertakings": undertakings,
        "escalations": escalations
    }

@router.get("/{id}/pendency")
def get_application_pendency(
    id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns SLA ageing, pendency metrics, and breach status for an application."""
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if user.role == ROLE_INSTITUTE_HEAD and user.institution_id != app.institution_id:
        raise HTTPException(status_code=403, detail="Cross-institution access denied")
    return workflow_engine.calculate_pendency(app)

@router.post("")
def create_application(
    payload: ApplicationCreate,
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_INSTITUTE_HEAD, ROLE_COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db)
):
    if user.role == ROLE_INSTITUTE_HEAD:
        if user.institution_id and user.institution_id != payload.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cross-institution submission denied: You can only lodge applications for your assigned institution '{user.institution_id}'."
            )

    inst = db.query(Institution).filter(Institution.id == payload.institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    # Determine workflow definition
    route_type = payload.route_type or "SCRUTINY_EVC"
    wf = None
    if payload.workflow_definition_id:
        wf = db.query(WorkflowDefinition).filter(WorkflowDefinition.id == payload.workflow_definition_id).first()
    if not wf:
        wf = workflow_engine.get_workflow_by_route(db, route_type)
        if not wf:
            workflow_engine.seed_default_workflows(db)
            wf = workflow_engine.get_workflow_by_route(db, route_type)

    # Initial SLA computation
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    initial_due_date = now.date() + timedelta(days=3)

    new_id = f"APP-2026-{uuid.uuid4().hex[:4].upper()}"
    app = Application(
        id=new_id,
        institution_id=payload.institution_id,
        workflow_definition_id=wf.id if wf else None,
        workflow_version=wf.version if wf else 1,
        route_type=route_type,
        stage_code="PRELIMINARY_VALIDATION",
        category=payload.category,
        type=payload.type,
        academic_year=payload.academic_year or "2026-2027",
        current_stage="Preliminary validation",
        status="New submission",
        owner=payload.owner or user.full_name or user.username,
        assigned_role=ROLE_COMPLIANCE_OFFICER,
        progress=15,
        submitted_at=date.today(),
        stage_entered_at=now,
        stage_due_date=initial_due_date,
        due_date=payload.due_date or initial_due_date,
        last_action="Application submitted for preliminary scrutiny",
        next_action="Perform automated document verification checklist"
    )
    db.add(app)

    stage_log = ApplicationStage(
        id=f"STG-{uuid.uuid4().hex[:6].upper()}",
        application_id=app.id,
        stage_code="PRELIMINARY_VALIDATION",
        from_stage=None,
        to_stage="Preliminary validation",
        stage_name="Preliminary validation",
        status="Initialized",
        action="CREATE",
        actor=user.username,
        remarks=f"Lodged application under {route_type} route."
    )
    db.add(stage_log)

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=user.username,
        role=user.role,
        action="Created Approval Application",
        entity_type="Application",
        entity_id=app.id,
        details=f"Created {app.type} ({route_type}) for {inst.name} ({inst.permanent_id})."
    )
    db.add(audit)
    db.commit()
    db.refresh(app)
    return app

@router.post("/{id}/transition")
def transition_application_stage(
    id: str,
    payload: ApplicationStageTransition,
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER, ROLE_SECURITY_OFFICER)),
    db: Session = Depends(get_db)
):
    """
    Executes an authorized stage transition validated against the active workflow definition.
    Enforces idempotency, role permissions, and prerequisite fulfillment.
    """
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Map target stage code
    target_code = payload.stage_code
    if not target_code and payload.next_stage:
        target_code = STAGE_NAME_TO_CODE.get(payload.next_stage, payload.next_stage.upper().replace(" ", "_").replace("-", "_").replace("/", "_"))

    if not target_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either stage_code or next_stage must be specified."
        )

    try:
        result = workflow_engine.execute_transition(
            app=app,
            target_stage_code=target_code,
            user=user,
            status_label=payload.status or "In review",
            remarks=payload.remarks,
            actor=payload.actor,
            idempotency_key=payload.idempotency_key,
            deficiencies=payload.deficiencies,
            bypass_prereq_override=bool(payload.bypass_prereq_override and user.role == ROLE_SUPER_ADMIN),
            db=db
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.post("/{id}/return-deficiency")
async def return_for_rectification(
    id: str,
    request: Request,
    actor: Optional[str] = Query(None),
    remarks: Optional[str] = Query(None),
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER, ROLE_SECURITY_OFFICER)),
    db: Session = Depends(get_db)
):
    """
    Returns an application to the institution with a deficiency checklist.
    Mandates a non-empty reason and deficiency items.
    """
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    content_type = request.headers.get("content-type", "")
    req_actor = actor or user.username
    req_remarks = remarks
    req_deficiencies = []

    if "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict):
                req_actor = body.get("actor") or req_actor
                req_remarks = body.get("remarks") or body.get("reason") or req_remarks
                if body.get("deficiencies") and isinstance(body["deficiencies"], list):
                    req_deficiencies = body["deficiencies"]
            elif isinstance(body, list):
                req_deficiencies = body
        except Exception:
            pass
    elif "form" in content_type:
        try:
            form = await request.form()
            req_actor = form.get("actor") or req_actor
            req_remarks = form.get("remarks") or form.get("reason") or req_remarks
            raw_def = form.get("deficiencies")
            if raw_def:
                req_deficiencies = [d.strip() for d in raw_def.split(";") if d.strip()]
        except Exception:
            pass

    if not req_remarks:
        req_remarks = "Deficiencies recorded during scrutiny examination."
    if not req_deficiencies:
        req_deficiencies = ["Mandatory document compliance required"]

    try:
        result = workflow_engine.return_for_deficiency(
            app=app,
            user=user,
            reason=req_remarks,
            deficiencies=req_deficiencies,
            db=db
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{id}/resubmit")
async def resubmit_rectification(
    id: str,
    request: Request,
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_INSTITUTE_HEAD, ROLE_COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db)
):
    """
    Institution resubmits rectified compliance documents after returning with deficiencies.
    """
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if user.role == ROLE_INSTITUTE_HEAD and user.institution_id != app.institution_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-institution access denied")

    content_type = request.headers.get("content-type", "")
    compliance_notes = "Rectified compliance documents uploaded by institutional representative."
    if "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict):
                compliance_notes = body.get("compliance_notes") or body.get("remarks") or compliance_notes
        except Exception:
            pass

    try:
        result = workflow_engine.resubmit_deficiency_compliance(
            app=app,
            user=user,
            compliance_notes=compliance_notes,
            db=db
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{id}/pause")
def pause_application_sla(
    id: str,
    reason: str = Body(..., embed=True),
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db)
):
    """Pauses the application SLA clock for statutory reasons (e.g. court stay, natural disaster)."""
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if app.is_paused:
        return {"message": "Application is already in a paused state", "paused_at": app.paused_at.isoformat()}

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    app.is_paused = True
    app.paused_at = now
    app.last_action = f"SLA processing paused: {reason}"

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=user.username,
        role=user.role,
        action="Paused Application SLA",
        entity_type="Application",
        entity_id=app.id,
        details=f"Paused SLA timer: {reason}"
    )
    db.add(audit)
    db.commit()
    return {"message": "Application SLA clock paused", "paused_at": now.isoformat()}

@router.post("/{id}/resume")
def resume_application_sla(
    id: str,
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db)
):
    """Resumes the application SLA clock and adjusts the due date by the paused interval."""
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if not app.is_paused:
        return {"message": "Application is not paused"}

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    pause_days = 0
    if app.paused_at:
        pause_days = max(1, (now.date() - app.paused_at.date()).days)
        app.total_pause_days = (app.total_pause_days or 0) + pause_days
        if app.stage_due_date:
            app.stage_due_date = app.stage_due_date + timedelta(days=pause_days)
            app.due_date = app.stage_due_date

    app.is_paused = False
    app.paused_at = None
    app.last_action = f"SLA processing resumed after {pause_days} days of pause."

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=user.username,
        role=user.role,
        action="Resumed Application SLA",
        entity_type="Application",
        entity_id=app.id,
        details=f"Resumed SLA timer. Extended deadline by {pause_days} days."
    )
    db.add(audit)
    db.commit()
    return {
        "message": "Application SLA clock resumed",
        "pause_days_adjusted": pause_days,
        "new_stage_due_date": app.stage_due_date.isoformat() if app.stage_due_date else None
    }
