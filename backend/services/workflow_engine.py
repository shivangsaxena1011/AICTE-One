"""
Configurable Workflow Engine Service for AICTE ONE (SHANKH)
Supports statutory Approval Process Handbook (APH) routes, stage validation,
prerequisites enforcement, idempotency, SLA tracking, and audit-logged transitions.
"""
import json
import uuid
from datetime import datetime, date, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.models import (
    Application, ApplicationStage, WorkflowDefinition, WorkflowStageDefinition,
    Institution, Document, DocumentValidity, EVCSchedule, Notification, AuditLog, User
)
from backend.auth import (
    ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER, ROLE_COMPLIANCE_OFFICER,
    ROLE_INSTITUTE_HEAD, ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR
)

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

# Standard statutory routes from AICTE Approval Process Handbook (APH)
DEFAULT_WORKFLOW_ROUTES = {
    "SCRUTINY_ONLY": {
        "name": "AICTE Approval — Scrutiny Only Route",
        "category": "Technical",
        "description": "Standard route for existing institutions, minor alterations, course closures, and accredited programmes without physical site inspection.",
        "stages": [
            {
                "stage_code": "PRELIMINARY_VALIDATION",
                "stage_name": "Preliminary Validation",
                "sequence_order": 1,
                "allowed_transitions": ["SCRUTINY", "RE_SCRUTINY"],
                "required_roles": [ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER],
                "prerequisites": ["mandatory_documents_present"],
                "sla_days": 3,
                "is_terminal": False
            },
            {
                "stage_code": "SCRUTINY",
                "stage_name": "Scrutiny Committee Examination",
                "sequence_order": 2,
                "allowed_transitions": ["FINAL_DISPOSITION", "RE_SCRUTINY"],
                "required_roles": [ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER],
                "prerequisites": ["scrutiny_checklist_verified", "valid_land_lease", "valid_safety_nocs"],
                "sla_days": 7,
                "is_terminal": False
            },
            {
                "stage_code": "RE_SCRUTINY",
                "stage_name": "Re-Scrutiny & Rectification",
                "sequence_order": 2,
                "allowed_transitions": ["SCRUTINY", "FINAL_DISPOSITION"],
                "required_roles": [ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER, ROLE_INSTITUTE_HEAD],
                "prerequisites": ["deficiency_rectification_filed"],
                "sla_days": 5,
                "is_terminal": False
            },
            {
                "stage_code": "FINAL_DISPOSITION",
                "stage_name": "Authorized Regulatory Disposition",
                "sequence_order": 3,
                "allowed_transitions": [],
                "required_roles": [ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER],
                "prerequisites": ["human_competent_authority_order"],
                "sla_days": 3,
                "is_terminal": True
            }
        ]
    },
    "SCRUTINY_EVC": {
        "name": "AICTE Approval — Scrutiny + Expert Visit Committee (EVC) Route",
        "category": "Technical",
        "description": "Standard statutory route for new institution setup, intake expansion, infrastructure shifts requiring on-site EVC inspection.",
        "stages": [
            {
                "stage_code": "PRELIMINARY_VALIDATION",
                "stage_name": "Preliminary Validation",
                "sequence_order": 1,
                "allowed_transitions": ["SCRUTINY", "RE_SCRUTINY"],
                "required_roles": [ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER],
                "prerequisites": ["mandatory_documents_present"],
                "sla_days": 3,
                "is_terminal": False
            },
            {
                "stage_code": "SCRUTINY",
                "stage_name": "Scrutiny Committee Examination",
                "sequence_order": 2,
                "allowed_transitions": ["EVC_SCHEDULING", "RE_SCRUTINY", "FINAL_DISPOSITION"],
                "required_roles": [ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER],
                "prerequisites": ["scrutiny_checklist_verified", "valid_land_lease", "valid_safety_nocs"],
                "sla_days": 7,
                "is_terminal": False
            },
            {
                "stage_code": "RE_SCRUTINY",
                "stage_name": "Re-Scrutiny & Rectification",
                "sequence_order": 2,
                "allowed_transitions": ["SCRUTINY", "EVC_SCHEDULING", "FINAL_DISPOSITION"],
                "required_roles": [ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER, ROLE_INSTITUTE_HEAD],
                "prerequisites": ["deficiency_rectification_filed"],
                "sla_days": 5,
                "is_terminal": False
            },
            {
                "stage_code": "EVC_SCHEDULING",
                "stage_name": "EVC Committee Scheduling & Conflict Check",
                "sequence_order": 3,
                "allowed_transitions": ["EVC_EVALUATION", "RE_SCRUTINY"],
                "required_roles": [ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER, ROLE_SECURITY_OFFICER],
                "prerequisites": ["scrutiny_passed", "no_expert_conflict_of_interest", "committee_quorum_met"],
                "sla_days": 5,
                "is_terminal": False
            },
            {
                "stage_code": "EVC_EVALUATION",
                "stage_name": "EVC Site Inspection & Report Filing",
                "sequence_order": 4,
                "allowed_transitions": ["FINAL_DISPOSITION", "SAC_SHC_REVIEW"],
                "required_roles": [ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER, ROLE_SECURITY_OFFICER],
                "prerequisites": ["evc_inspection_report_submitted", "geo_tagged_evidence_verified"],
                "sla_days": 7,
                "is_terminal": False
            },
            {
                "stage_code": "FINAL_DISPOSITION",
                "stage_name": "Authorized Regulatory Disposition",
                "sequence_order": 5,
                "allowed_transitions": [],
                "required_roles": [ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER],
                "prerequisites": ["human_competent_authority_order"],
                "sla_days": 3,
                "is_terminal": True
            }
        ]
    },
    "EVC_SAC_SHC": {
        "name": "AICTE Approval — EVC with Standing Appellate Committee (SAC/SHC) Route",
        "category": "Technical",
        "description": "Appellate route for applications with contested EVC findings or major non-compliances referred to SAC or SHC for personal hearing.",
        "stages": [
            {
                "stage_code": "PRELIMINARY_VALIDATION",
                "stage_name": "Preliminary Validation",
                "sequence_order": 1,
                "allowed_transitions": ["SCRUTINY"],
                "required_roles": [ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER],
                "prerequisites": ["mandatory_documents_present"],
                "sla_days": 3,
                "is_terminal": False
            },
            {
                "stage_code": "SCRUTINY",
                "stage_name": "Scrutiny Committee Examination",
                "sequence_order": 2,
                "allowed_transitions": ["EVC_SCHEDULING", "RE_SCRUTINY"],
                "required_roles": [ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER],
                "prerequisites": ["scrutiny_checklist_verified"],
                "sla_days": 7,
                "is_terminal": False
            },
            {
                "stage_code": "EVC_SCHEDULING",
                "stage_name": "EVC Committee Scheduling & Conflict Check",
                "sequence_order": 3,
                "allowed_transitions": ["EVC_EVALUATION"],
                "required_roles": [ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER],
                "prerequisites": ["scrutiny_passed", "no_expert_conflict_of_interest"],
                "sla_days": 5,
                "is_terminal": False
            },
            {
                "stage_code": "EVC_EVALUATION",
                "stage_name": "EVC Site Inspection & Report Filing",
                "sequence_order": 4,
                "allowed_transitions": ["SAC_SHC_REVIEW"],
                "required_roles": [ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER],
                "prerequisites": ["evc_inspection_report_submitted"],
                "sla_days": 7,
                "is_terminal": False
            },
            {
                "stage_code": "SAC_SHC_REVIEW",
                "stage_name": "Standing Appellate / Hearing Committee Review",
                "sequence_order": 5,
                "allowed_transitions": ["FINAL_DISPOSITION", "RE_SCRUTINY"],
                "required_roles": [ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER],
                "prerequisites": ["hearing_minutes_recorded", "committee_quorum_met"],
                "sla_days": 10,
                "is_terminal": False
            },
            {
                "stage_code": "FINAL_DISPOSITION",
                "stage_name": "Authorized Regulatory Disposition",
                "sequence_order": 6,
                "allowed_transitions": [],
                "required_roles": [ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER],
                "prerequisites": ["human_competent_authority_order"],
                "sla_days": 3,
                "is_terminal": True
            }
        ]
    },
    "EVC_ONLY": {
        "name": "AICTE Approval — Standalone Inspection (EVC Only)",
        "category": "Technical",
        "description": "Surprise inspection, compliance re-verification, or complaint investigation site visit.",
        "stages": [
            {
                "stage_code": "EVC_SCHEDULING",
                "stage_name": "EVC Committee Scheduling & Conflict Check",
                "sequence_order": 1,
                "allowed_transitions": ["EVC_EVALUATION"],
                "required_roles": [ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER, ROLE_SECURITY_OFFICER],
                "prerequisites": ["no_expert_conflict_of_interest", "committee_quorum_met"],
                "sla_days": 3,
                "is_terminal": False
            },
            {
                "stage_code": "EVC_EVALUATION",
                "stage_name": "EVC Site Inspection & Report Filing",
                "sequence_order": 2,
                "allowed_transitions": ["FINAL_DISPOSITION"],
                "required_roles": [ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER, ROLE_SECURITY_OFFICER],
                "prerequisites": ["evc_inspection_report_submitted"],
                "sla_days": 5,
                "is_terminal": False
            },
            {
                "stage_code": "FINAL_DISPOSITION",
                "stage_name": "Authorized Regulatory Disposition",
                "sequence_order": 3,
                "allowed_transitions": [],
                "required_roles": [ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER],
                "prerequisites": ["human_competent_authority_order"],
                "sla_days": 3,
                "is_terminal": True
            }
        ]
    }
}

class WorkflowEngineService:
    """Core Workflow Automation Engine for AICTE ONE Approval Processing"""

    @staticmethod
    def seed_default_workflows(db: Session) -> List[WorkflowDefinition]:
        """Ensures all standard APH workflow routes are registered and up to date."""
        created_or_updated = []
        for route_code, def_data in DEFAULT_WORKFLOW_ROUTES.items():
            existing = db.query(WorkflowDefinition).filter(WorkflowDefinition.code == route_code).first()
            if not existing:
                wf_id = f"WF-DEF-{route_code}"
                wf = WorkflowDefinition(
                    id=wf_id,
                    name=def_data["name"],
                    code=route_code,
                    category=def_data["category"],
                    academic_year="2026-2027",
                    route_type=route_code,
                    version=1,
                    is_active=True,
                    stages_config=json.dumps(def_data["stages"]),
                    rules_config=json.dumps({"description": def_data["description"]})
                )
                db.add(wf)
                db.flush()

                for s in def_data["stages"]:
                    stage_def = WorkflowStageDefinition(
                        id=f"WSD-{route_code}-{s['stage_code']}",
                        workflow_id=wf.id,
                        stage_code=s["stage_code"],
                        stage_name=s["stage_name"],
                        sequence_order=s["sequence_order"],
                        allowed_transitions_json=json.dumps(s["allowed_transitions"]),
                        required_roles_json=json.dumps(s["required_roles"]),
                        prerequisites_json=json.dumps(s.get("prerequisites", [])),
                        sla_days=s.get("sla_days", 7),
                        escalation_policy_json=json.dumps({
                            "level_1_days": s.get("sla_days", 7) + 1,
                            "level_1_role": "REGIONAL_OFFICER",
                            "level_2_days": s.get("sla_days", 7) + 3,
                            "level_2_role": "BUREAU_HEAD"
                        }),
                        is_terminal=s.get("is_terminal", False)
                    )
                    db.add(stage_def)
                created_or_updated.append(wf)
            else:
                created_or_updated.append(existing)
        db.commit()
        return created_or_updated

    @staticmethod
    def get_workflow_by_route(db: Session, route_type: str) -> Optional[WorkflowDefinition]:
        """Fetches the active workflow definition for a given route."""
        return db.query(WorkflowDefinition).filter(
            WorkflowDefinition.route_type == route_type,
            WorkflowDefinition.is_active == True
        ).first()

    @staticmethod
    def get_stage_definition(db: Session, workflow_id: str, stage_code: str) -> Optional[WorkflowStageDefinition]:
        """Fetches the stage definition within a specific workflow."""
        return db.query(WorkflowStageDefinition).filter(
            WorkflowStageDefinition.workflow_id == workflow_id,
            WorkflowStageDefinition.stage_code == stage_code
        ).first()

    @staticmethod
    def validate_prerequisites(
        app: Application,
        stage_code: str,
        db: Session
    ) -> Tuple[bool, List[str]]:
        """
        Validates prerequisite criteria before entering or advancing past a stage.
        Returns (is_valid, list_of_deficiencies).
        """
        deficiencies = []

        # 1. Mandatory documents check
        if stage_code in ["SCRUTINY", "EVC_SCHEDULING"]:
            docs = db.query(Document).filter(Document.application_id == app.id).all()
            if not docs:
                # Also check institution docs
                docs = db.query(Document).filter(Document.institution_id == app.institution_id).all()
            if len(docs) < 1:
                deficiencies.append("Mandatory statutory documents must be uploaded before scrutiny examination.")

        # 2. Document Validity Engine: Check Land Lease & Safety NOCs
        if stage_code in ["EVC_SCHEDULING", "FINAL_DISPOSITION"]:
            expired_docs = db.query(DocumentValidity).filter(
                DocumentValidity.institution_id == app.institution_id,
                DocumentValidity.status == "Expired"
            ).all()
            for exp in expired_docs:
                deficiencies.append(f"Expired statutory document: {exp.document_type} (Ref: {exp.document_ref_number}) expired on {exp.expiry_date.isoformat()}. Active renewal required.")

        # 3. EVC completion check
        if stage_code == "FINAL_DISPOSITION" and app.route_type in ["SCRUTINY_EVC", "EVC_SAC_SHC", "EVC_ONLY"]:
            evc = db.query(EVCSchedule).filter(
                EVCSchedule.application_id == app.id,
                EVCSchedule.status == "Completed",
                EVCSchedule.report_submitted == True
            ).first()
            if not evc:
                deficiencies.append("Expert Visit Committee (EVC) site inspection report has not been submitted or verified.")

        # 4. SAC/SHC review check
        if stage_code == "FINAL_DISPOSITION" and app.route_type == "EVC_SAC_SHC":
            # Must have visited SAC_SHC_REVIEW stage
            sac_stage = db.query(ApplicationStage).filter(
                ApplicationStage.application_id == app.id,
                ApplicationStage.stage_code == "SAC_SHC_REVIEW"
            ).first()
            if not sac_stage and app.stage_code != "SAC_SHC_REVIEW":
                deficiencies.append("Application requires Standing Appellate Committee (SAC/SHC) hearing appraisal prior to disposition.")

        return (len(deficiencies) == 0, deficiencies)

    @classmethod
    def execute_transition(
        cls,
        app: Application,
        target_stage_code: str,
        user: User,
        status_label: str,
        remarks: Optional[str],
        actor: Optional[str],
        idempotency_key: Optional[str],
        db: Session,
        deficiencies: Optional[List[str]] = None,
        bypass_prereq_override: bool = False
    ) -> Dict[str, Any]:
        """
        Executes a validated workflow stage transition transactionally.
        Enforces idempotency, role authorization, state transition validity,
        prerequisite validation, and SLA recalculation.
        """
        # 1. Idempotency control: Prevent duplicate execution
        if idempotency_key and app.last_idempotency_key == idempotency_key:
            return {
                "message": "Duplicate transition request skipped (idempotent result preserved)",
                "application_id": app.id,
                "current_stage": app.current_stage,
                "stage_code": app.stage_code,
                "status": app.status,
                "is_idempotent": True
            }

        # 2. Retrieve active workflow definition
        wf = None
        if app.workflow_definition_id:
            wf = db.query(WorkflowDefinition).filter(WorkflowDefinition.id == app.workflow_definition_id).first()
        if not wf:
            wf = cls.get_workflow_by_route(db, app.route_type or "SCRUTINY_EVC")
            if not wf:
                cls.seed_default_workflows(db)
                wf = cls.get_workflow_by_route(db, app.route_type or "SCRUTINY_EVC")

        if not wf:
            raise ValueError(f"No active workflow found for route {app.route_type}")

        # 3. Retrieve current and target stage definitions
        curr_stage_code = app.stage_code or "PRELIMINARY_VALIDATION"
        curr_stage_def = cls.get_stage_definition(db, wf.id, curr_stage_code)
        target_stage_def = cls.get_stage_definition(db, wf.id, target_stage_code)

        if not target_stage_def:
            raise ValueError(f"Target stage code '{target_stage_code}' is not defined in workflow '{wf.name}'")

        # 4. Validate transition permissions (Unless Super Admin override or initial setup)
        if curr_stage_def and user.role != ROLE_SUPER_ADMIN:
            allowed_transitions = json.loads(curr_stage_def.allowed_transitions_json or "[]")
            if target_stage_code not in allowed_transitions:
                raise ValueError(
                    f"Invalid stage transition: Cannot transition from '{curr_stage_def.stage_name}' ({curr_stage_code}) "
                    f"to '{target_stage_def.stage_name}' ({target_stage_code}). "
                    f"Permitted next stages: {', '.join(allowed_transitions) if allowed_transitions else 'None (Terminal stage)'}."
                )

            # Check role permissions for target stage
            allowed_roles = json.loads(target_stage_def.required_roles_json or "[]")
            if user.role not in allowed_roles:
                raise PermissionError(
                    f"Role '{user.role}' is not authorized to transition application to '{target_stage_def.stage_name}'. "
                    f"Required roles: {', '.join(allowed_roles)}."
                )

        # 5. Validate prerequisites
        if not bypass_prereq_override:
            is_valid, prereq_deficiencies = cls.validate_prerequisites(app, target_stage_code, db)
            if not is_valid:
                raise ValueError(
                    f"Cannot advance to '{target_stage_def.stage_name}': Unmet prerequisites: " +
                    "; ".join(prereq_deficiencies)
                )

        # 6. Calculate time spent in previous stage
        now = utc_now()
        time_spent_hours = 0.0
        sla_breached = False

        if app.stage_entered_at:
            delta = now - app.stage_entered_at
            time_spent_hours = round(delta.total_seconds() / 3600.0, 2)
            if app.stage_due_date and now.date() > app.stage_due_date:
                sla_breached = True

        # 7. Update application model
        old_stage_name = app.current_stage
        old_stage_code = app.stage_code

        app.workflow_definition_id = wf.id
        app.workflow_version = wf.version
        app.stage_code = target_stage_code
        app.current_stage = target_stage_def.stage_name
        app.status = status_label
        app.owner = actor or user.full_name or user.username
        app.stage_entered_at = now
        app.last_idempotency_key = idempotency_key

        # Calculate new SLA deadline for the target stage
        sla_days = target_stage_def.sla_days or 7
        app.stage_due_date = now.date() + timedelta(days=sla_days)
        app.due_date = app.stage_due_date

        # Update progress percentage
        progress_map = {
            "PRELIMINARY_VALIDATION": 15,
            "SCRUTINY": 35,
            "RE_SCRUTINY": 40,
            "EVC_SCHEDULING": 60,
            "EVC_EVALUATION": 75,
            "SAC_SHC_REVIEW": 85,
            "FINAL_DISPOSITION": 100
        }
        app.progress = progress_map.get(target_stage_code, app.progress)

        if deficiencies:
            app.deficiency_count = len(deficiencies)

        app.last_action = remarks or f"Transitioned from {old_stage_name} to {target_stage_def.stage_name}"
        app.next_action = f"Pending action at {target_stage_def.stage_name} stage (SLA: {sla_days} days)"

        # 8. Record immutable ApplicationStage log
        stage_log = ApplicationStage(
            id=f"STG-{uuid.uuid4().hex[:6].upper()}",
            application_id=app.id,
            stage_code=target_stage_code,
            from_stage=old_stage_name,
            to_stage=target_stage_def.stage_name,
            stage_name=target_stage_def.stage_name,
            status=status_label,
            action="TRANSITION",
            actor=user.username,
            time_spent_hours=time_spent_hours,
            sla_breached=sla_breached,
            remarks=remarks,
            deficiencies="; ".join(deficiencies) if deficiencies else None,
            idempotency_key=idempotency_key,
            completed_at=now if target_stage_def.is_terminal else None
        )
        db.add(stage_log)

        # 9. Record statutory AuditLog
        audit = AuditLog(
            id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
            actor=user.username,
            role=user.role,
            action="Workflow Stage Transition",
            entity_type="Application",
            entity_id=app.id,
            details=f"Transitioned {app.id} from '{old_stage_name}' to '{target_stage_def.stage_name}'. Status: '{status_label}'. SLA: {sla_days} days."
        )
        db.add(audit)

        # 10. Generate in-app notification
        notification = Notification(
            id=f"NOTIF-{uuid.uuid4().hex[:6].upper()}",
            title=f"Application {app.id} Advanced",
            message=f"Application has reached stage: {target_stage_def.stage_name} ({status_label}).",
            category="Workflow",
            urgency="Important" if sla_breached else "Info",
            link_type="application",
            link_id=app.id,
            user_id="all"
        )
        db.add(notification)

        db.commit()
        db.refresh(app)

        return {
            "message": "Transition completed successfully",
            "application_id": app.id,
            "route_type": app.route_type,
            "stage_code": app.stage_code,
            "current_stage": app.current_stage,
            "status": app.status,
            "stage_due_date": app.stage_due_date.isoformat() if app.stage_due_date else None,
            "sla_breached_in_previous_stage": sla_breached,
            "is_idempotent": False
        }

    @classmethod
    def return_for_deficiency(
        cls,
        app: Application,
        user: User,
        reason: str,
        deficiencies: List[str],
        db: Session
    ) -> Dict[str, Any]:
        """
        Returns application to institution with deficiency checklist for rectification.
        Requires explicit reason and deficiency details.
        """
        if not reason or not reason.strip():
            raise ValueError("An explicit reason is mandatory when returning an application for deficiencies.")
        if not deficiencies:
            raise ValueError("At least one deficiency item must be specified when returning an application.")

        old_stage = app.current_stage
        app.stage_code = "RE_SCRUTINY"
        app.current_stage = "Re-Scrutiny & Rectification"
        app.status = "Returned for rectification"
        app.deficiency_count = len(deficiencies)
        app.last_action = f"Returned for rectification: {reason}"
        app.next_action = "Awaiting rectified compliance documents from institution"

        # SLA for rectification (e.g. 10 days for institute to respond)
        now = utc_now()
        app.stage_entered_at = now
        app.stage_due_date = now.date() + timedelta(days=10)
        app.due_date = app.stage_due_date

        stage_log = ApplicationStage(
            id=f"STG-{uuid.uuid4().hex[:6].upper()}",
            application_id=app.id,
            stage_code="RE_SCRUTINY",
            from_stage=old_stage,
            to_stage="Re-Scrutiny & Rectification",
            stage_name="Re-Scrutiny & Rectification",
            status="Returned for rectification",
            action="RETURN_FOR_DEFICIENCY",
            actor=user.username,
            remarks=reason,
            deficiencies="; ".join(deficiencies)
        )
        db.add(stage_log)

        audit = AuditLog(
            id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
            actor=user.username,
            role=user.role,
            action="Returned Application with Deficiencies",
            entity_type="Application",
            entity_id=app.id,
            details=f"Returned with {len(deficiencies)} deficiencies: {reason}"
        )
        db.add(audit)

        notif = Notification(
            id=f"NOTIF-{uuid.uuid4().hex[:6].upper()}",
            title=f"Deficiencies Raised on {app.id}",
            message=f"Application {app.id} returned for rectification with {len(deficiencies)} deficiencies: {reason}",
            category="Deficiency",
            urgency="Critical",
            link_type="application",
            link_id=app.id,
            user_id="all"
        )
        db.add(notif)

        db.commit()
        db.refresh(app)
        return {
            "message": "Application returned for deficiency rectification",
            "current_stage": app.current_stage,
            "status": app.status,
            "deficiency_count": app.deficiency_count
        }

    @classmethod
    def resubmit_deficiency_compliance(
        cls,
        app: Application,
        user: User,
        compliance_notes: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Institution resubmits rectified compliance documents.
        Transitions status from 'Returned for rectification' to 'Resubmitted for scrutiny'.
        """
        if app.status != "Returned for rectification" and app.stage_code != "RE_SCRUTINY":
            raise ValueError(f"Application {app.id} is not in a return/deficiency state (current: '{app.status}')")

        app.resubmission_count = (app.resubmission_count or 0) + 1
        app.status = "Resubmitted for scrutiny"
        app.last_action = f"Resubmitted by institution (Round {app.resubmission_count}): {compliance_notes}"
        app.next_action = "Scrutiny committee re-examination of compliance submissions"

        now = utc_now()
        stage_log = ApplicationStage(
            id=f"STG-{uuid.uuid4().hex[:6].upper()}",
            application_id=app.id,
            stage_code="RE_SCRUTINY",
            stage_name="Re-Scrutiny & Rectification",
            status="Resubmitted for scrutiny",
            action="RESUBMIT",
            actor=user.username,
            remarks=compliance_notes
        )
        db.add(stage_log)

        audit = AuditLog(
            id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
            actor=user.username,
            role=user.role,
            action="Resubmitted Compliance Evidence",
            entity_type="Application",
            entity_id=app.id,
            details=f"Institution resubmitted rectification for {app.id} (Round {app.resubmission_count})."
        )
        db.add(audit)
        db.commit()
        db.refresh(app)
        return {
            "message": "Rectification resubmitted successfully for re-scrutiny",
            "resubmission_count": app.resubmission_count,
            "status": app.status
        }

    @staticmethod
    def calculate_pendency(app: Application) -> Dict[str, Any]:
        """Calculates SLA ageing, time remaining, breach status, and pause adjustments."""
        now = utc_now()
        today = now.date()
        sub_date = app.submitted_at if isinstance(app.submitted_at, date) else today
        total_age_days = (today - sub_date).days

        stage_entered = app.stage_entered_at.date() if app.stage_entered_at else today
        stage_age_days = (today - stage_entered).days

        deadline = app.stage_due_date or app.due_date or (stage_entered + timedelta(days=7))
        days_remaining = (deadline - today).days

        is_overdue = days_remaining < 0
        is_due_soon = 0 <= days_remaining <= 3

        return {
            "application_id": app.id,
            "category": app.category,
            "route_type": app.route_type,
            "current_stage": app.current_stage,
            "stage_code": app.stage_code,
            "total_age_days": total_age_days,
            "stage_age_days": stage_age_days,
            "stage_deadline": deadline.isoformat(),
            "days_remaining": days_remaining,
            "is_overdue": is_overdue,
            "is_due_soon": is_due_soon,
            "is_paused": bool(app.is_paused),
            "is_escalated": bool(app.is_escalated),
            "escalation_level": app.escalation_level or 0
        }

workflow_engine = WorkflowEngineService()
