"""
Escalation & Document Validity Engine Service for AICTE ONE (SHANKH)
Monitors SLA compliance, time-bound statutory undertakings, and document/lease expiration.
Generates multi-tier escalations and notification events.
"""
import uuid
from datetime import datetime, date, timedelta, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from backend.models import (
    Application, ApplicationStage, Undertaking, DocumentValidity,
    EscalationEvent, Notification, AuditLog, Institution
)
from backend.auth import (
    ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER, ROLE_SECURITY_OFFICER
)

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class EscalationService:
    """Automated SLA, Undertaking, and Lease Expiry Monitoring Service"""

    @classmethod
    def check_sla_and_escalate(cls, db: Session) -> Dict[str, Any]:
        """
        Scans all active applications for SLA breaches.
        Applies multi-tier escalation policy:
          - Level 1 (Overdue 1-2 days): Escalated to Regional Officer
          - Level 2 (Overdue 3-5 days): Escalated to Bureau Head
          - Level 3 (Overdue > 5 days): Escalated to Member Secretary (Super Admin)
        """
        today = date.today()
        active_apps = db.query(Application).filter(
            Application.status.notin_(["Approved", "Rejected", "Disposed", "Closed"]),
            Application.is_paused == False
        ).all()

        escalations_created = []
        for app in active_apps:
            deadline = app.stage_due_date or app.due_date
            if not deadline:
                continue

            days_overdue = (today - deadline).days
            if days_overdue <= 0:
                continue

            # Determine escalation level
            target_level = 1
            target_role = "REGIONAL_OFFICER"
            if days_overdue >= 5:
                target_level = 3
                target_role = ROLE_SUPER_ADMIN
            elif days_overdue >= 3:
                target_level = 2
                target_role = "BUREAU_HEAD"

            # Check if this escalation level is already triggered
            existing_esc = db.query(EscalationEvent).filter(
                EscalationEvent.application_id == app.id,
                EscalationEvent.escalation_level == target_level,
                EscalationEvent.status == "Active"
            ).first()

            if not existing_esc:
                esc_id = f"ESC-{uuid.uuid4().hex[:6].upper()}"
                reason = (
                    f"Application {app.id} at stage '{app.current_stage}' is overdue by {days_overdue} days "
                    f"(Deadline was {deadline.isoformat()}). Escalated to Level {target_level}."
                )
                esc = EscalationEvent(
                    id=esc_id,
                    application_id=app.id,
                    institution_id=app.institution_id,
                    entity_type="Application",
                    entity_id=app.id,
                    escalation_level=target_level,
                    trigger_reason=reason,
                    escalated_to_role=target_role,
                    status="Active"
                )
                db.add(esc)

                app.is_escalated = True
                app.escalation_level = target_level

                # In-app alert
                notif = Notification(
                    id=f"NOTIF-{uuid.uuid4().hex[:6].upper()}",
                    title=f"SLA Breach Escalation: {app.id} (Level {target_level})",
                    message=reason,
                    category="Escalation",
                    urgency="Critical",
                    link_type="application",
                    link_id=app.id,
                    user_id="all"
                )
                db.add(notif)
                escalations_created.append({
                    "application_id": app.id,
                    "level": target_level,
                    "role": target_role,
                    "days_overdue": days_overdue
                })

        db.commit()
        return {
            "scanned_applications": len(active_apps),
            "new_escalations_count": len(escalations_created),
            "escalations": escalations_created
        }

    @classmethod
    def check_undertakings_compliance(cls, db: Session) -> Dict[str, Any]:
        """
        Scans time-bound undertakings for approaching deadlines and overdue breaches.
        Updates status to 'Overdue' if statutory deadline elapsed without accepted evidence.
        """
        today = date.today()
        undertakings = db.query(Undertaking).filter(
            Undertaking.status.in_(["Pending Submission", "Evidence Submitted", "Upcoming", "Active"])
        ).all()

        updated_count = 0
        overdue_list = []
        for u in undertakings:
            if u.statutory_deadline < today and u.status != "Verified & Accepted":
                u.status = "Overdue"
                updated_count += 1
                overdue_list.append(u.id)

                # Check if escalation logged
                existing_esc = db.query(EscalationEvent).filter(
                    EscalationEvent.entity_type == "Undertaking",
                    EscalationEvent.entity_id == u.id,
                    EscalationEvent.status == "Active"
                ).first()

                if not existing_esc:
                    esc = EscalationEvent(
                        id=f"ESC-{uuid.uuid4().hex[:6].upper()}",
                        application_id=u.application_id,
                        institution_id=u.institution_id,
                        entity_type="Undertaking",
                        entity_id=u.id,
                        escalation_level=2,
                        trigger_reason=f"Time-bound undertaking '{u.undertaking_type}' (Condition: {u.condition_ref}) is overdue since {u.statutory_deadline.isoformat()}.",
                        escalated_to_role=ROLE_COMPLIANCE_OFFICER,
                        status="Active"
                    )
                    db.add(esc)

                    notif = Notification(
                        id=f"NOTIF-{uuid.uuid4().hex[:6].upper()}",
                        title=f"Statutory Undertaking Overdue: {u.condition_ref}",
                        message=f"Undertaking for condition {u.condition_ref} ({u.undertaking_type}) expired on {u.statutory_deadline.isoformat()}.",
                        category="Compliance",
                        urgency="Critical",
                        link_type="undertaking",
                        link_id=u.id,
                        user_id="all"
                    )
                    db.add(notif)

        db.commit()
        return {
            "total_undertakings_scanned": len(undertakings),
            "marked_overdue": updated_count,
            "overdue_ids": overdue_list
        }

    @classmethod
    def check_document_and_lease_validities(cls, db: Session) -> Dict[str, Any]:
        """
        Evaluates document validities (Land Lease, Building Safety, Fire Safety NOC).
        Updates status to 'Expiring Soon' (within advance_warning_days) or 'Expired'.
        Blocks or raises regulatory non-compliance alerts.
        """
        today = date.today()
        docs = db.query(DocumentValidity).all()

        expiring_soon = []
        expired = []

        for d in docs:
            warning_window = d.advance_warning_days or 60
            days_until_expiry = (d.expiry_date - today).days

            if days_until_expiry < 0:
                if d.status != "Expired":
                    d.status = "Expired"
                    expired.append(d.id)
                    notif = Notification(
                        id=f"NOTIF-{uuid.uuid4().hex[:6].upper()}",
                        title=f"Critical Document Expired: {d.document_type}",
                        message=f"{d.document_type} (Ref: {d.document_ref_number}) expired on {d.expiry_date.isoformat()}. Regulatory operations blocked pending renewal.",
                        category="Document",
                        urgency="Critical",
                        link_type="document",
                        link_id=d.id,
                        user_id="all"
                    )
                    db.add(notif)
            elif days_until_expiry <= warning_window:
                if d.status != "Expiring Soon":
                    d.status = "Expiring Soon"
                    expiring_soon.append(d.id)
                    notif = Notification(
                        id=f"NOTIF-{uuid.uuid4().hex[:6].upper()}",
                        title=f"Document Expiring Soon: {d.document_type}",
                        message=f"{d.document_type} (Ref: {d.document_ref_number}) will expire in {days_until_expiry} days on {d.expiry_date.isoformat()}. Renewal required.",
                        category="Document",
                        urgency="Important",
                        link_type="document",
                        link_id=d.id,
                        user_id="all"
                    )
                    db.add(notif)

        db.commit()
        return {
            "total_documents_scanned": len(docs),
            "marked_expired": len(expired),
            "marked_expiring_soon": len(expiring_soon)
        }

escalation_service = EscalationService()
