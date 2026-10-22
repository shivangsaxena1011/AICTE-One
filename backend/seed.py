"""
Database Seeder Script for AICTE ONE (SHANKH)
Initializes normalized schema, statutory roles, permissions, and 8 individual user accounts
"""
import json
import os
import sys
import uuid
from datetime import datetime, date, timezone

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.database import SessionLocal, engine, Base, init_db
from backend.models import (
    User, Role, Permission, RolePermission,
    Institution, Application, EVCSchedule, Document,
    ComplianceObligation, Complaint, CoordinationLink, Task,
    Notification, AuditLog
)
from backend.auth import (
    hash_password,
    ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER, ROLE_COMPLIANCE_OFFICER,
    ROLE_COMPLAINT_OFFICER, ROLE_ANTI_RAGGING_OFFICER, ROLE_INSTITUTE_HEAD,
    ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR,
    ROLE_PERMISSIONS_MAP
)

DEFAULT_SEED_PASSWORD = "AicteOne@2026!"

SEED_ROLES = [
    {
        "id": "ROL-SUPER_AD",
        "code": ROLE_SUPER_ADMIN,
        "name": "Super Administrator",
        "description": "Full statutory and administrative oversight across all bureaus, institutions, workflows, and audit records."
    },
    {
        "id": "ROL-SECURITY",
        "code": ROLE_SECURITY_OFFICER,
        "name": "Security Officer",
        "description": "Access to security incidents, document anomalies, audit logs, and infrastructure safety monitoring."
    },
    {
        "id": "ROL-POLICY_C",
        "code": ROLE_COMPLIANCE_OFFICER,
        "name": "Policy & Compliance Officer",
        "description": "Regulatory compliance oversight, undertakings verification, FDR tracking, and land/fire NOC reviews."
    },
    {
        "id": "ROL-COMPLAIN",
        "code": ROLE_COMPLAINT_OFFICER,
        "name": "Complaint & Vigilance Officer",
        "description": "Grievance intake, investigation assignment, cross-bureau conflict linking, and hearing disposition."
    },
    {
        "id": "ROL-ANTI_RAG",
        "code": ROLE_ANTI_RAGGING_OFFICER,
        "name": "Anti-Ragging Officer / Committee",
        "description": "Specialized jurisdiction over student harassment, ragging complaints, rapid-response escalations, and hearings."
    },
    {
        "id": "ROL-INSTITUT",
        "code": ROLE_INSTITUTE_HEAD,
        "name": "Institute Principal / Head",
        "description": "Tenant-isolated access strictly limited to authorized institution's Digital Twin, EoA applications, and compliance filings."
    },
    {
        "id": "ROL-STUDENT_",
        "code": ROLE_STUDENT_COMPLAINANT,
        "name": "Student / Complainant",
        "description": "Submission of grievances and evidence, personal complaint status tracking. Zero access to confidential officer notes."
    },
    {
        "id": "ROL-PUBLIC_V",
        "code": ROLE_PUBLIC_VISITOR,
        "name": "Public Visitor",
        "description": "Search public institutional directory, verify approval records, and view open public reports without login."
    }
]

SEED_USERS = [
    {
        "id": "USR-ADMIN-01",
        "username": "superadmin",
        "email": "admin@aicte-india.org",
        "full_name": "Dr. V. K. Adhikari (Member Secretary & Chief Admin)",
        "role": ROLE_SUPER_ADMIN,
        "department": "Central Administration",
        "institution_id": None,
        "phone": "+91-11-29581000",
        "is_active": True,
        "is_mfa_enabled": False
    },
    {
        "id": "USR-SEC-01",
        "username": "security.officer",
        "email": "security@aicte-india.org",
        "full_name": "Col. Rajeshwar Singh (Chief Information Security Officer)",
        "role": ROLE_SECURITY_OFFICER,
        "department": "Information Security & Vigilance",
        "institution_id": None,
        "phone": "+91-11-29581002",
        "is_active": True,
        "is_mfa_enabled": False
    },
    {
        "id": "USR-COMPL-01",
        "username": "compliance.officer",
        "email": "compliance.officer@aicte-india.org",
        "full_name": "Dr. Meenakshi Sundaram (Director - Policy & Compliance)",
        "role": ROLE_COMPLIANCE_OFFICER,
        "department": "Policy & Academic Bureau",
        "institution_id": None,
        "phone": "+91-11-29581003",
        "is_active": True,
        "is_mfa_enabled": False
    },
    {
        "id": "USR-GRIEV-01",
        "username": "complaint.officer",
        "email": "vigilance.officer@aicte-india.org",
        "full_name": "Shri Arvind Deshmukh (Chief Grievance Officer)",
        "role": ROLE_COMPLAINT_OFFICER,
        "department": "Public Grievance Cell",
        "institution_id": None,
        "phone": "+91-11-29581004",
        "is_active": True,
        "is_mfa_enabled": False
    },
    {
        "id": "USR-RAGG-01",
        "username": "antiragging.officer",
        "email": "antiragging@aicte-india.org",
        "full_name": "Prof. Sunita Narain (Chairperson, Anti-Ragging Cell)",
        "role": ROLE_ANTI_RAGGING_OFFICER,
        "department": "National Anti-Ragging Committee",
        "institution_id": None,
        "phone": "+91-11-29581005",
        "is_active": True,
        "is_mfa_enabled": False
    },
    {
        "id": "USR-INST-01",
        "username": "principal.gitm",
        "email": "principal@gitm.ac.in",
        "full_name": "Dr. Anand K. Patwardhan (Principal / Director - GITM)",
        "role": ROLE_INSTITUTE_HEAD,
        "department": "Institution Administration",
        "institution_id": "INST-10482",
        "phone": "+91-120-2328000",
        "is_active": True,
        "is_mfa_enabled": False
    },
    {
        "id": "USR-STUD-01",
        "username": "student.aarav",
        "email": "aarav.student@gmail.com",
        "full_name": "Aarav Sharma (B.Tech Scholar & Complainant)",
        "role": ROLE_STUDENT_COMPLAINANT,
        "department": "Student Body",
        "institution_id": None,
        "phone": "+91-9876543210",
        "is_active": True,
        "is_mfa_enabled": False
    },
    {
        "id": "USR-PUB-01",
        "username": "public.visitor",
        "email": "citizen@bharat.in",
        "full_name": "Citizen / Prospective Student (Public Visitor)",
        "role": ROLE_PUBLIC_VISITOR,
        "department": "Public Access",
        "institution_id": None,
        "phone": None,
        "is_active": True,
        "is_mfa_enabled": False
    }
]

def seed_database(session=None):
    init_db()

    # Production Safeguard (Section 5): Never overwrite existing production records or inject synthetic demo data
    from backend.config import settings
    is_production = (getattr(settings, "ENVIRONMENT", "").lower() == "production" or 
                     os.getenv("ENVIRONMENT", "").lower() == "production")

    close_when_done = False
    if session is None:
        db = SessionLocal()
        close_when_done = True
    else:
        db = session

    try:
        # If in production and records already exist, abort synthetic seeding safely
        if is_production and db.query(Institution).count() > 0:
            print("[SECURITY NOTICE] Production environment active with existing records. Skipping synthetic seed injection.")
            return
        # A. Seed or update Statutory Roles
        existing_roles = {r.code: r for r in db.query(Role).all()}
        for r_data in SEED_ROLES:
            if r_data["code"] not in existing_roles:
                role_obj = Role(
                    id=r_data["id"],
                    code=r_data["code"],
                    name=r_data["name"],
                    description=r_data["description"],
                    is_system_role=True
                )
                db.add(role_obj)
        db.commit()

        # B. Seed Granular Permissions & Role Mappings
        existing_perms = {p.code: p for p in db.query(Permission).all()}
        all_perm_codes = set()
        for perms in ROLE_PERMISSIONS_MAP.values():
            all_perm_codes.update(perms)

        for p_code in all_perm_codes:
            if p_code not in existing_perms:
                parts = p_code.split(":")
                mod = parts[0] if len(parts) > 1 else "general"
                act = parts[1] if len(parts) > 1 else parts[0]
                perm_obj = Permission(
                    id=f"PRM-{uuid.uuid4().hex[:6].upper()}",
                    code=p_code,
                    name=f"{act.capitalize()} {mod.capitalize()}",
                    module=mod,
                    action=act,
                    description=f"Statutory permission: {p_code}"
                )
                db.add(perm_obj)
                existing_perms[p_code] = perm_obj
        db.commit()

        # C. Seed or update Users with Bcrypt Password Hashes
        password_hash = hash_password(DEFAULT_SEED_PASSWORD)
        for u_data in SEED_USERS:
            existing_user = db.query(User).filter(
                (User.id == u_data["id"]) | (User.username == u_data["username"]) | (User.email == u_data["email"])
            ).first()

            if existing_user:
                existing_user.password_hash = password_hash
                existing_user.role = u_data["role"]
                existing_user.is_active = True
                existing_user.failed_login_attempts = 0
                existing_user.locked_until = None
                if u_data.get("institution_id"):
                    existing_user.institution_id = u_data["institution_id"]
            else:
                new_user = User(
                    id=u_data["id"],
                    username=u_data["username"],
                    email=u_data["email"],
                    full_name=u_data["full_name"],
                    password_hash=password_hash,
                    role=u_data["role"],
                    department=u_data.get("department", "AICTE"),
                    institution_id=u_data.get("institution_id"),
                    phone=u_data.get("phone"),
                    is_active=True,
                    is_mfa_enabled=u_data.get("is_mfa_enabled", False),
                    failed_login_attempts=0
                )
                db.add(new_user)
        db.commit()

        # D. Seed Domain Entities from seed_records.json if not present
        if db.query(Institution).count() == 0:
            json_path = os.path.join(os.path.dirname(__file__), "..", "data", "seed_records.json")
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 1. Institutions
                for item in data.get("institutions", []):
                    inst = Institution(
                        id=item["id"],
                        permanent_id=item["permanent_id"],
                        name=item["name"],
                        state=item["state"],
                        district=item["district"],
                        city=item["city"],
                        address=item.get("address"),
                        category=item["category"],
                        institution_type=item["institution_type"],
                        affiliation=item.get("affiliation"),
                        website=item.get("website"),
                        approval_status=item.get("approval_status", "Approved"),
                        approval_period=item.get("approval_period", "2026-2027"),
                        programmes_count=item.get("programmes_count", 0),
                        total_intake=item.get("total_intake", 0),
                        data_source=item.get("data_source", "AICTE Official Directory 2026"),
                        verified_status=item.get("verified_status", "Verified"),
                        last_verified=date.fromisoformat(item["last_verified"]) if item.get("last_verified") else date.today()
                    )
                    db.add(inst)
                db.commit()

                # 2. Applications
                for item in data.get("applications", []):
                    app = Application(
                        id=item["id"],
                        institution_id=item["institution_id"],
                        category=item["category"],
                        type=item["type"],
                        academic_year=item.get("academic_year", "2026-2027"),
                        current_stage=item.get("current_stage", "Preliminary validation"),
                        status=item.get("status", "New submission"),
                        owner=item.get("owner", "Unassigned"),
                        progress=item.get("progress", 10),
                        submitted_at=date.fromisoformat(item["submitted_at"]) if item.get("submitted_at") else date.today(),
                        due_date=date.fromisoformat(item["due_date"]) if item.get("due_date") else None,
                        deficiency_count=item.get("deficiency_count", 0),
                        last_action=item.get("last_action"),
                        next_action=item.get("next_action")
                    )
                    db.add(app)
                db.commit()

                # 3. EVC Schedules
                for item in data.get("evc_schedules", []):
                    evc = EVCSchedule(
                        id=item["id"],
                        application_id=item["application_id"],
                        institution_id=item["institution_id"],
                        visit_type=item.get("visit_type", "Physical Inspection"),
                        scheduled_date=date.fromisoformat(item["scheduled_date"]),
                        status=item.get("status", "Scheduled"),
                        committee_chair=item["committee_chair"],
                        committee_members=item.get("committee_members"),
                        report_submitted=item.get("report_submitted", False),
                        observations=item.get("observations"),
                        remarks=item.get("remarks")
                    )
                    db.add(evc)
                db.commit()

                # 4. Documents
                for item in data.get("documents", []):
                    doc = Document(
                        id=item["id"],
                        institution_id=item["institution_id"],
                        application_id=item.get("application_id"),
                        name=item["name"],
                        document_type=item["document_type"],
                        uploaded_at=date.fromisoformat(item["uploaded_at"]) if item.get("uploaded_at") else date.today(),
                        status=item.get("status", "Verification pending"),
                        confidence=item.get("confidence", "Not processed"),
                        extracted_fields=json.dumps(item.get("extracted_fields", {})),
                        findings=item.get("findings"),
                        issuing_authority=item.get("issuing_authority"),
                        authority_ref=item.get("authority_ref"),
                        verification_source=item.get("verification_source", "Not verified"),
                        verification_response=item.get("verification_response"),
                        is_anomaly=item.get("is_anomaly", False),
                        confidentiality_level="Internal"
                    )
                    db.add(doc)
                db.commit()

                # 5. Compliance Obligations
                for item in data.get("compliance", []):
                    comp = ComplianceObligation(
                        id=item["id"],
                        institution_id=item["institution_id"],
                        title=item["title"],
                        category=item["category"],
                        due_date=date.fromisoformat(item["due_date"]),
                        status=item.get("status", "Upcoming"),
                        responsible_party=item.get("responsible_party", "Institution"),
                        evidence_file=item.get("evidence_file"),
                        review_notes=item.get("review_notes")
                    )
                    db.add(comp)
                db.commit()

                # 6. Complaints (with complainant_id and ragging_flag set)
                for item in data.get("complaints", []):
                    is_ragging = "ragging" in (item.get("category", "") + item.get("summary", "")).lower()
                    cplt = Complaint(
                        id=item["id"],
                        institution_id=item["institution_id"],
                        complainant_id="USR-STUD-01",  # Link to Aarav Sharma for student test scenario
                        case_number=item.get("case_number"),
                        bureau=item["bureau"],
                        category=item["category"],
                        summary=item["summary"],
                        details=item.get("details"),
                        channel=item.get("channel", "Online Portal"),
                        status=item.get("status", "Received"),
                        assigned_to=item.get("assigned_to", "Unassigned"),
                        received_date=date.fromisoformat(item["received_date"]) if item.get("received_date") else date.today(),
                        due_date=date.fromisoformat(item["due_date"]) if item.get("due_date") else None,
                        related_case_id=item.get("related_case_id"),
                        overlap_score=item.get("overlap_score", 0),
                        overlap_reason=item.get("overlap_reason"),
                        resolution_notes=item.get("resolution_notes"),
                        is_confidential=False,
                        ragging_flag=is_ragging
                    )
                    db.add(cplt)
                db.commit()

                # 7. Coordination Links
                for item in data.get("coordination_links", []):
                    link = CoordinationLink(
                        id=item["id"],
                        case_a_id=item["case_a_id"],
                        case_b_id=item["case_b_id"],
                        status=item.get("status", "Confirmed"),
                        confidence_score=item.get("confidence_score", 85),
                        matching_factors=item.get("matching_factors"),
                        rationale=item.get("rationale"),
                        coordinating_bureau=item.get("coordinating_bureau"),
                        coordinating_officer=item.get("coordinating_officer"),
                        confirmed_by=item.get("confirmed_by"),
                        confirmed_at=datetime.fromisoformat(item["confirmed_at"].replace("Z", "+00:00")) if item.get("confirmed_at") else datetime.now(timezone.utc)
                    )
                    db.add(link)
                db.commit()

                # 8. Tasks
                for item in data.get("tasks", []):
                    task = Task(
                        id=item["id"],
                        title=item["title"],
                        category=item["category"],
                        priority=item.get("priority", "Medium"),
                        status=item.get("status", "Pending"),
                        due_date=date.fromisoformat(item["due_date"]) if item.get("due_date") else None,
                        assigned_to=item["assigned_to"],
                        bureau=item["bureau"],
                        institution_id=item.get("institution_id"),
                        application_id=item.get("application_id"),
                        complaint_id=item.get("complaint_id"),
                        document_id=item.get("document_id"),
                        obligation_id=item.get("obligation_id"),
                        resolution_notes=item.get("resolution_notes")
                    )
                    db.add(task)
                db.commit()

                # 9. Notifications
                for item in data.get("notifications", []):
                    notif = Notification(
                        id=item["id"],
                        title=item["title"],
                        message=item["message"],
                        category=item.get("category", "System"),
                        urgency=item.get("urgency", "Info"),
                        link_type=item.get("link_type"),
                        link_id=item.get("link_id"),
                        is_read=item.get("is_read", False)
                    )
                    db.add(notif)
                db.commit()

                # 10. Audit Logs
                for item in data.get("audit", []):
                    audit = AuditLog(
                        id=item["id"],
                        timestamp=datetime.strptime(item["time"], "%Y-%m-%d %H:%M:%S") if " " in item["time"] else datetime.now(timezone.utc),
                        actor=item["actor"],
                        role=item["role"],
                        action=item["action"],
                        entity_type=item["entity_type"],
                        entity_id=item["record"],
                        details=item["detail"]
                    )
                    db.add(audit)
                db.commit()

        # Seed statutory workflow definitions
        from backend.services.workflow_engine import workflow_engine
        workflow_engine.seed_default_workflows(db)

        # Ensure sample undertakings and document validities exist if empty
        from backend.models import Undertaking, DocumentValidity
        if db.query(Undertaking).count() == 0:
            sample_u = Undertaking(
                id="UND-2026-001",
                institution_id="INST-001",
                application_id="APP-2026-001",
                undertaking_type="Faculty Cadre Compliance",
                condition_ref="APH-2026-Clause-4.2",
                description="Recruitment of 3 Professor cadre faculty in Computer Science & Engineering within statutory window.",
                statutory_deadline=date(2026, 11, 30),
                status="Pending Submission"
            )
            db.add(sample_u)
            db.commit()

        if db.query(DocumentValidity).count() == 0:
            sample_val = DocumentValidity(
                id="VAL-LEASE-001",
                institution_id="INST-001",
                document_type="Land Lease Agreement",
                document_ref_number="REG/MH/2015/88219",
                issuing_authority="Department of Revenue, Govt. of Maharashtra",
                issue_date=date(2015, 6, 1),
                expiry_date=date(2045, 5, 31),
                advance_warning_days=90,
                status="Active"
            )
            sample_val2 = DocumentValidity(
                id="VAL-FIRE-001",
                institution_id="INST-001",
                document_type="Fire Safety NOC",
                document_ref_number="FIRE/NOC/2025/1102",
                issuing_authority="State Fire & Emergency Services",
                issue_date=date(2025, 4, 15),
                expiry_date=date(2026, 4, 14),
                advance_warning_days=60,
                status="Active"
            )
            db.add(sample_val)
            db.add(sample_val2)
            db.commit()

        # Ensure existing complaints have complainant_id populated if null
        db.query(Complaint).filter(Complaint.complainant_id == None).update({"complainant_id": "USR-STUD-01"})
        db.commit()

    finally:
        if close_when_done:
            db.close()

if __name__ == "__main__":
    seed_database()
    print("AICTE ONE statutory database seeding completed successfully.")
