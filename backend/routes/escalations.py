"""
Escalation & SLA Monitoring Router for AICTE ONE
Provides visibility, scanning triggers, and resolution workflows for statutory SLA breaches.
"""
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models import EscalationEvent, Application, Institution, AuditLog, User
from backend.schemas import EscalationResponse
from backend.services.escalation_service import escalation_service
from backend.auth import (
    get_current_user, require_roles,
    ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER, ROLE_COMPLIANCE_OFFICER,
    ROLE_INSTITUTE_HEAD, ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR
)

router = APIRouter(prefix="/api/escalations", tags=["Escalations"])

@router.get("", response_model=List[EscalationResponse])
def list_escalations(
    status_filter: Optional[str] = Query(None, alias="status"),
    level: Optional[int] = Query(None),
    institution_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lists escalation events scoped by tenant and role:
    - Central AICTE officers and admins see all escalations across India.
    - Institute Heads see ONLY escalations concerning their institution.
    - Students and public visitors are forbidden.
    """
    if user.role in {ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Escalation logs are confidential."
        )

    query = db.query(EscalationEvent)
    if user.role == ROLE_INSTITUTE_HEAD:
        if not user.institution_id:
            return []
        query = query.filter(EscalationEvent.institution_id == user.institution_id)
    elif institution_id:
        query = query.filter(EscalationEvent.institution_id == institution_id)

    if status_filter:
        query = query.filter(EscalationEvent.status == status_filter)
    if level is not None:
        query = query.filter(EscalationEvent.escalation_level == level)

    return query.order_by(desc(EscalationEvent.created_at)).all()

@router.post("/trigger-scan")
def trigger_sla_scan(
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER, ROLE_SECURITY_OFFICER)),
    db: Session = Depends(get_db)
):
    """
    Triggers automated system-wide SLA breach scanning.
    Evaluates pendency, applies multi-tier escalation policies, and dispatches in-app alerts.
    """
    app_scan = escalation_service.check_sla_and_escalate(db)
    undertaking_scan = escalation_service.check_undertakings_compliance(db)
    doc_scan = escalation_service.check_document_and_lease_validities(db)

    return {
        "message": "Comprehensive SLA and statutory compliance scan completed",
        "applications": app_scan,
        "undertakings": undertaking_scan,
        "document_validities": doc_scan
    }

@router.post("/{id}/resolve")
def resolve_escalation(
    id: str,
    resolution_notes: str = Body(..., embed=True),
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER, ROLE_SECURITY_OFFICER)),
    db: Session = Depends(get_db)
):
    """Resolves an escalation event with explanatory audit notes."""
    esc = db.query(EscalationEvent).filter(EscalationEvent.id == id).first()
    if not esc:
        raise HTTPException(status_code=404, detail="Escalation record not found")

    esc.status = "Resolved"
    esc.resolution_notes = resolution_notes
    esc.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)

    # Check if application has remaining active escalations
    if esc.application_id:
        remaining = db.query(EscalationEvent).filter(
            EscalationEvent.application_id == esc.application_id,
            EscalationEvent.status == "Active"
        ).count()
        if remaining == 0:
            app = db.query(Application).filter(Application.id == esc.application_id).first()
            if app:
                app.is_escalated = False
                app.escalation_level = 0

    audit = AuditLog(
        id=f"AUD-{id}",
        actor=user.username,
        role=user.role,
        action="Resolved Escalation",
        entity_type="EscalationEvent",
        entity_id=esc.id,
        details=f"Resolved level {esc.escalation_level} escalation on {esc.entity_type} {esc.entity_id}: {resolution_notes}"
    )
    db.add(audit)
    db.commit()
    return {"message": "Escalation resolved successfully", "status": esc.status}
