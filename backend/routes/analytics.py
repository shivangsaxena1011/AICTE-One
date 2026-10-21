"""
Executive Analytics & Operational Indicators Router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models import (
    Institution, Application, Document, ComplianceObligation, Complaint, Task, EVCSchedule
)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/dashboard")
@router.get("")
def get_executive_overview_metrics(db: Session = Depends(get_db)):
    total_institutions = db.query(Institution).count()
    total_applications = db.query(Application).count()
    total_documents = db.query(Document).count()
    total_compliance = db.query(ComplianceObligation).count()
    total_complaints = db.query(Complaint).count()
    total_tasks = db.query(Task).count()

    # Stage distribution
    stage_counts = {}
    apps = db.query(Application).all()
    for a in apps:
        stage_counts[a.current_stage] = stage_counts.get(a.current_stage, 0) + 1

    # Document outcomes
    docs = db.query(Document).all()
    doc_outcomes = {
        "verified": sum(1 for d in docs if "verified" in d.status.lower()),
        "pending": sum(1 for d in docs if "pending" in d.status.lower()),
        "mismatch": sum(1 for d in docs if "mismatch" in d.status.lower()),
        "expiry": sum(1 for d in docs if "expir" in d.status.lower()),
        "anomalies": sum(1 for d in docs if d.is_anomaly)
    }

    # Compliance health
    comps = db.query(ComplianceObligation).all()
    compliance_health = {
        "on_track": sum(1 for c in comps if "on track" in c.status.lower() or "satisfied" in c.status.lower()),
        "due_soon": sum(1 for c in comps if "due soon" in c.status.lower() or "action" in c.status.lower()),
        "overdue": sum(1 for c in comps if "overdue" in c.status.lower()),
        "review_pending": sum(1 for c in comps if "pending" in c.status.lower() or "submitted" in c.status.lower())
    }

    # Complaints by bureau
    cplts = db.query(Complaint).all()
    bureau_counts = {}
    for c in cplts:
        bureau_counts[c.bureau] = bureau_counts.get(c.bureau, 0) + 1

    overlapping_cases_count = sum(1 for c in cplts if c.related_case_id) // 2

    # EVC
    evcs = db.query(EVCSchedule).all()
    evc_counts = {
        "scheduled": sum(1 for e in evcs if e.status == "Scheduled"),
        "completed": sum(1 for e in evcs if e.status == "Completed"),
        "pending_reports": sum(1 for e in evcs if not e.report_submitted)
    }

    # Task priority breakdown
    tasks = db.query(Task).all()
    task_counts = {
        "critical": sum(1 for t in tasks if t.priority == "Critical" and t.status != "Completed"),
        "high": sum(1 for t in tasks if t.priority == "High" and t.status != "Completed"),
        "in_progress": sum(1 for t in tasks if t.status == "In Progress"),
        "pending": sum(1 for t in tasks if t.status == "Pending")
    }

    return {
        "summary": {
            "institutions": total_institutions,
            "applications": total_applications,
            "documents": total_documents,
            "compliance": total_compliance,
            "complaints": total_complaints,
            "tasks": total_tasks,
            "overlapping_cases": overlapping_cases_count
        },
        "stage_distribution": stage_counts,
        "document_outcomes": doc_outcomes,
        "compliance_health": compliance_health,
        "bureau_workload": bureau_counts,
        "evc_metrics": evc_counts,
        "task_metrics": task_counts
    }
