"""
Workflow Configuration & Management Router for AICTE ONE
Provides CRUD operations for Approval Process Handbook (APH) routes and stages.
Restricted to Super Administrators for administrative governance.
"""
import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models import WorkflowDefinition, WorkflowStageDefinition, AuditLog, User
from backend.schemas import (
    WorkflowDefinitionCreate, WorkflowDefinitionResponse
)
from backend.services.workflow_engine import workflow_engine
from backend.auth import (
    get_current_user, require_roles,
    ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER, ROLE_SECURITY_OFFICER
)

router = APIRouter(prefix="/api/workflows", tags=["Workflows"])

@router.get("", response_model=List[WorkflowDefinitionResponse])
def list_workflows(
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER, ROLE_SECURITY_OFFICER)),
    db: Session = Depends(get_db)
):
    """Lists all active and configured Approval Process Handbook (APH) workflows."""
    # Ensure default APH workflows are seeded
    wfs = db.query(WorkflowDefinition).order_by(WorkflowDefinition.created_at).all()
    if not wfs:
        workflow_engine.seed_default_workflows(db)
        wfs = db.query(WorkflowDefinition).order_by(WorkflowDefinition.created_at).all()
    return wfs

@router.get("/{id}")
def get_workflow(
    id: str,
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER, ROLE_SECURITY_OFFICER)),
    db: Session = Depends(get_db)
):
    """Retrieves full workflow definition with stage sequence, prerequisites, and SLAs."""
    wf = db.query(WorkflowDefinition).filter(WorkflowDefinition.id == id).first()
    if not wf:
        wf = db.query(WorkflowDefinition).filter(WorkflowDefinition.code == id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow definition not found")

    stages = db.query(WorkflowStageDefinition).filter(
        WorkflowStageDefinition.workflow_id == wf.id
    ).order_by(WorkflowStageDefinition.sequence_order).all()

    stages_data = []
    for s in stages:
        stages_data.append({
            "id": s.id,
            "stage_code": s.stage_code,
            "stage_name": s.stage_name,
            "sequence_order": s.sequence_order,
            "allowed_transitions": json.loads(s.allowed_transitions_json or "[]"),
            "required_roles": json.loads(s.required_roles_json or "[]"),
            "prerequisites": json.loads(s.prerequisites_json or "[]"),
            "sla_days": s.sla_days,
            "escalation_policy": json.loads(s.escalation_policy_json or "{}"),
            "is_terminal": s.is_terminal
        })

    return {
        "id": wf.id,
        "name": wf.name,
        "code": wf.code,
        "category": wf.category,
        "academic_year": wf.academic_year,
        "route_type": wf.route_type,
        "version": wf.version,
        "is_active": wf.is_active,
        "stages": stages_data,
        "created_at": wf.created_at.isoformat() if wf.created_at else None
    }

@router.post("", response_model=WorkflowDefinitionResponse)
def create_workflow(
    payload: WorkflowDefinitionCreate,
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """Creates a custom or updated workflow route (Super Administrator only)."""
    existing = db.query(WorkflowDefinition).filter(WorkflowDefinition.code == payload.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Workflow with code '{payload.code}' already exists."
        )

    wf_id = f"WF-DEF-{uuid.uuid4().hex[:6].upper()}"
    stages_raw = [s.model_dump() for s in payload.stages]

    wf = WorkflowDefinition(
        id=wf_id,
        name=payload.name,
        code=payload.code,
        category=payload.category or "Technical",
        academic_year=payload.academic_year or "2026-2027",
        route_type=payload.route_type,
        version=1,
        is_active=True,
        stages_config=json.dumps(stages_raw),
        rules_config=json.dumps({"description": payload.description})
    )
    db.add(wf)
    db.flush()

    for s in payload.stages:
        stage_def = WorkflowStageDefinition(
            id=f"WSD-{uuid.uuid4().hex[:6].upper()}",
            workflow_id=wf.id,
            stage_code=s.stage_code,
            stage_name=s.stage_name,
            sequence_order=s.sequence_order,
            allowed_transitions_json=json.dumps(s.allowed_transitions),
            required_roles_json=json.dumps(s.required_roles),
            prerequisites_json=json.dumps(s.prerequisites or []),
            sla_days=s.sla_days or 7,
            escalation_policy_json=json.dumps({
                "level_1_days": (s.sla_days or 7) + 1,
                "level_1_role": "REGIONAL_OFFICER",
                "level_2_days": (s.sla_days or 7) + 3,
                "level_2_role": "BUREAU_HEAD"
            }),
            is_terminal=s.is_terminal or False
        )
        db.add(stage_def)

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=user.username,
        role=user.role,
        action="Created Workflow Route",
        entity_type="WorkflowDefinition",
        entity_id=wf.id,
        details=f"Defined route '{wf.name}' ({wf.code}) with {len(payload.stages)} stages."
    )
    db.add(audit)
    db.commit()
    db.refresh(wf)
    return wf

@router.put("/{id}/toggle-active")
def toggle_workflow_active(
    id: str,
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """Activates or deactivates a workflow route."""
    wf = db.query(WorkflowDefinition).filter(WorkflowDefinition.id == id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    wf.is_active = not wf.is_active
    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=user.username,
        role=user.role,
        action="Toggled Workflow Status",
        entity_type="WorkflowDefinition",
        entity_id=wf.id,
        details=f"Set workflow '{wf.name}' is_active to {wf.is_active}."
    )
    db.add(audit)
    db.commit()
    return {"message": f"Workflow {wf.id} is_active set to {wf.is_active}", "is_active": wf.is_active}
