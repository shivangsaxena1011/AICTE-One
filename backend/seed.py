"""
Database Seeder Script for AICTE ONE
"""
import json
import os
from datetime import datetime, date
from backend.database import SessionLocal, engine, Base
from backend.models import (
    Institution, Application, EVCSchedule, Document,
    ComplianceObligation, Complaint, CoordinationLink, Task,
    Notification, AuditLog
)

def seed_database(session=None):
    from backend import database as db_mod
    Base.metadata.create_all(bind=db_mod.engine)
    
    close_when_done = False
    if session is None:
        db = db_mod.SessionLocal()
        close_when_done = True
    else:
        db = session
    
    # Check if already seeded
    if db.query(Institution).count() > 0:
        if close_when_done:
            db.close()
        return

    json_path = os.path.join(os.path.dirname(__file__), "..", "data", "seed_records.json")
    if not os.path.exists(json_path):
        db.close()
        return

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
            is_anomaly=item.get("is_anomaly", False)
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

    # 6. Complaints
    for item in data.get("complaints", []):
        cplt = Complaint(
            id=item["id"],
            institution_id=item["institution_id"],
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
            resolution_notes=item.get("resolution_notes")
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
            confirmed_at=datetime.fromisoformat(item["confirmed_at"].replace("Z", "+00:00")) if item.get("confirmed_at") else datetime.utcnow()
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
            timestamp=datetime.strptime(item["time"], "%Y-%m-%d %H:%M:%S") if " " in item["time"] else datetime.utcnow(),
            actor=item["actor"],
            role=item["role"],
            action=item["action"],
            entity_type=item["entity_type"],
            entity_id=item["record"],
            details=item["detail"]
        )
        db.add(audit)
    db.commit()
    if close_when_done:
        db.close()

if __name__ == "__main__":
    seed_database()
    print("Database seeding completed successfully.")
