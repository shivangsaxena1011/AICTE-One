"""
Executive Analytics & Operational Indicators Router for AICTE ONE
Implements government-grade KPI metrics and 12 interactive dashboard graphs (A through L)
computed directly from authoritative database records with role-based scoping.
"""
import csv
import io
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc

from backend.database import get_db
from backend.models import (
    Institution, Application, Document, DocumentValidity,
    ComplianceObligation, Undertaking, Complaint, Task,
    EVCSchedule, EscalationEvent, AuditLog, User
)
from backend.schemas import RiskRecommendationActionRequest
from backend.services.risk_service import risk_service
from backend.auth import (
    get_current_user, get_optional_user, require_roles,
    ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER, ROLE_COMPLIANCE_OFFICER,
    ROLE_COMPLAINT_OFFICER, ROLE_ANTI_RAGGING_OFFICER,
    ROLE_INSTITUTE_HEAD, ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR
)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/kpis")
@router.get("/dashboard")
def get_operational_kpis(
    academic_year: Optional[str] = Query("2026-2027"),
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    if not user or user.role in {ROLE_PUBLIC_VISITOR, ROLE_STUDENT_COMPLAINANT}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Operational KPI analytics are restricted to authorized regulatory officers."
        )
    """
    Returns the 15 authoritative KPI metrics defined in Phase 3 specifications.
    Every metric is backed by actual database queries, scoped by user persona.
    """
    if not isinstance(academic_year, str):
        academic_year = getattr(academic_year, "default", "2026-2027")

    today = date.today()
    is_officer = user and user.role in {
        ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER, ROLE_COMPLIANCE_OFFICER,
        ROLE_COMPLAINT_OFFICER, ROLE_ANTI_RAGGING_OFFICER
    }
    is_institute_head = user and user.role == ROLE_INSTITUTE_HEAD
    inst_id = user.institution_id if is_institute_head else None

    # 1. Total Institutions in Master Database
    total_institutions = db.query(Institution).count()

    # 2. Verified Active Approved Institutions
    verified_approved = db.query(Institution).filter(Institution.approval_status == "Approved").count()

    # 3. New Registrations during Academic Year
    new_registrations = db.query(Institution).filter(Institution.approval_period == academic_year).count()

    # Applications base query
    app_q = db.query(Application)
    if is_institute_head and inst_id:
        app_q = app_q.filter(Application.institution_id == inst_id)

    # 4. Applications awaiting approval (non-final)
    apps_awaiting_approval = app_q.filter(
        Application.status.notin_(["Approved", "Rejected", "Disposed", "Closed"])
    ).count()

    # 5. New Approvals
    new_approvals = app_q.filter(Application.status == "Approved").count()

    # 6. Applications currently in active workflow stages
    active_workflow_stages = app_q.filter(
        Application.stage_code.in_(["SCRUTINY", "RE_SCRUTINY", "EVC_SCHEDULING", "EVC_EVALUATION", "SAC_SHC_REVIEW"])
    ).count()

    # Complaints queries
    cplt_q = db.query(Complaint)
    if is_institute_head and inst_id:
        cplt_q = cplt_q.filter(Complaint.institution_id == inst_id, Complaint.is_confidential == False)
    elif not is_officer:
        # Public visitor sees zero internal complaints
        cplt_q = cplt_q.filter(Complaint.id == "NONE")

    total_complaints = cplt_q.count()
    complaints_today = cplt_q.filter(Complaint.received_date == today).count()
    complaints_under_investigation = cplt_q.filter(
        Complaint.status.in_(["Under Investigation", "In review", "Hearing scheduled", "Notice Issued"])
    ).count()
    pending_overdue_complaints = cplt_q.filter(
        Complaint.due_date < today,
        Complaint.status.notin_(["Disposed", "Resolved", "Closed"])
    ).count()
    resolved_complaints = cplt_q.filter(
        Complaint.status.in_(["Disposed", "Resolved", "Closed"])
    ).count()
    high_priority_cases = cplt_q.filter(
        or_(Complaint.ragging_flag == True, Complaint.overlap_score >= 80)
    ).count()

    # Documents query
    doc_q = db.query(Document)
    if is_institute_head and inst_id:
        doc_q = doc_q.filter(Document.institution_id == inst_id)
    docs_awaiting_verification = doc_q.filter(
        or_(Document.status == "Verification pending", Document.confidence == "Not processed")
    ).count()

    # Document validity approaching expiry (within 60 days)
    val_q = db.query(DocumentValidity)
    if is_institute_head and inst_id:
        val_q = val_q.filter(DocumentValidity.institution_id == inst_id)
    documents_approaching_expiry = val_q.filter(DocumentValidity.status == "Expiring Soon").count()

    # Undertakings queries
    und_q = db.query(Undertaking)
    if is_institute_head and inst_id:
        und_q = und_q.filter(Undertaking.institution_id == inst_id)
    undertakings_awaiting_verification = und_q.filter(
        Undertaking.status.in_(["Evidence Submitted", "Pending Submission"])
    ).count()

    # Failed or overdue compliance
    comp_q = db.query(ComplianceObligation)
    if is_institute_head and inst_id:
        comp_q = comp_q.filter(ComplianceObligation.institution_id == inst_id)
    overdue_obligations = comp_q.filter(
        ComplianceObligation.due_date < today,
        ComplianceObligation.status.notin_(["Satisfied by evidence", "Not applicable"])
    ).count()
    overdue_undertakings = und_q.filter(Undertaking.status == "Overdue").count()
    failed_or_overdue_compliance = overdue_obligations + overdue_undertakings

    # EVC schedules
    evc_scheduled = db.query(EVCSchedule).filter(EVCSchedule.status == "Scheduled").count()
    evc_completed = db.query(EVCSchedule).filter(EVCSchedule.status == "Completed").count()

    # Verified institutions
    verified_institutions = db.query(Institution).filter(Institution.verified_status == "Verified").count()

    # Scrutiny completed
    scrutiny_completed = app_q.filter(
        Application.stage_code.in_(["EVC_SCHEDULING", "EVC_EVALUATION", "SAC_SHC_REVIEW", "FINAL_DISPOSITION", "APPROVED"])
    ).count()

    # Processing SLA compliance rate
    total_tracked_apps = app_q.count()
    sla_breached_count = app_q.filter(
        Application.due_date < today,
        Application.status.notin_(["Approved", "Rejected", "Disposed", "Closed"])
    ).count()
    sla_compliance_rate = round(((total_tracked_apps - sla_breached_count) / max(total_tracked_apps, 1)) * 100.0, 1)

    # Active complaints and anti-ragging
    active_complaints = cplt_q.filter(Complaint.status.notin_(["Disposed", "Resolved", "Closed"])).count()
    ragging_complaints = cplt_q.filter(Complaint.ragging_flag == True).count()
    pgrc_resolved = cplt_q.filter(Complaint.bureau == "PGRC", Complaint.status.in_(["Disposed", "Resolved", "Closed"])).count()

    # Escalated cases
    escalated_cases = app_q.filter(Application.is_escalated == True).count()

    # Document validity critical (expiring within 30 days or expired)
    critical_validity = val_q.filter(DocumentValidity.status.in_(["Expiring Soon", "Expired"])).count()

    # Average dwell time across applications
    all_apps = app_q.all()
    total_dwell_days = sum((today - (a.submitted_at or today)).days for a in all_apps)
    avg_processing_days = round(total_dwell_days / max(len(all_apps), 1), 1)

    kpis_payload = {
        # 15 Phase 3 Operational KPIs
        "total_institutions": total_institutions,
        "verified_institutions": verified_institutions,
        "active_applications": apps_awaiting_approval,
        "sla_compliance_rate": sla_compliance_rate,
        "scrutiny_completed": scrutiny_completed,
        "evc_scheduled": evc_scheduled,
        "evc_completed": evc_completed,
        "undertakings_active": undertakings_awaiting_verification,
        "undertakings_breached": overdue_undertakings,
        "document_validity_critical": critical_validity,
        "active_complaints": active_complaints,
        "ragging_complaints": ragging_complaints,
        "pgrc_resolved": pgrc_resolved,
        "avg_processing_days": avg_processing_days,
        "escalated_cases": escalated_cases,

        # Retained Phase 1/2 Keys for backward compatibility
        "verified_active_approved_institutions": verified_approved,
        "new_registrations_period": new_registrations,
        "applications_awaiting_approval": apps_awaiting_approval,
        "new_approvals_period": new_approvals,
        "applications_in_active_stages": active_workflow_stages,
        "total_complaints_received": total_complaints,
        "complaints_received_today": complaints_today,
        "complaints_under_investigation": complaints_under_investigation,
        "pending_and_overdue_complaints": pending_overdue_complaints,
        "resolved_complaints": resolved_complaints,
        "high_priority_and_critical_cases": high_priority_cases,
        "documents_awaiting_verification": docs_awaiting_verification,
        "undertakings_awaiting_verification": undertakings_awaiting_verification,
        "documents_approaching_expiry": documents_approaching_expiry,
        "failed_or_overdue_compliance": failed_or_overdue_compliance
    }

    summary_dict = {
        "institutions": total_institutions,
        "applications": total_tracked_apps,
        "documents": doc_q.count(),
        "compliance": comp_q.count(),
        "complaints": total_complaints,
        "pending_verification": docs_awaiting_verification,
        "compliance_alerts": failed_or_overdue_compliance,
        "overlapping_cases": high_priority_cases
    }

    return {
        "academic_year": academic_year,
        "summary": summary_dict,
        "kpis": kpis_payload,
        **kpis_payload,
        "computed_at": datetime.now(timezone.utc).isoformat()
    }

# -------------------------------------------------------------
# Graph A — Applications by Workflow Stage (Interactive Donut)
# -------------------------------------------------------------
@router.get("/graphs/workflow-stages")
def get_graph_applications_by_stage(
    route_type: Optional[str] = Query(None),
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    query = db.query(Application)
    if user and user.role == ROLE_INSTITUTE_HEAD and user.institution_id:
        query = query.filter(Application.institution_id == user.institution_id)
    if route_type:
        query = query.filter(Application.route_type == route_type)

    apps = query.all()
    total = len(apps)

    stage_counts: Dict[str, int] = {}
    for a in apps:
        stage = a.current_stage or "Preliminary validation"
        stage_counts[stage] = stage_counts.get(stage, 0) + 1

    segments = []
    for stage_name, count in stage_counts.items():
        pct = round((count / total) * 100.0, 1) if total > 0 else 0.0
        segments.append({
            "stage_name": stage_name,
            "count": count,
            "percentage": pct,
            "filter_key": "current_stage",
            "filter_value": stage_name
        })

    return {
        "title": "Applications by Workflow Stage",
        "total": total,
        "segments": segments,
        "unit": "applications"
    }

# -------------------------------------------------------------
# Graph B — Complaints by Category (Bar Chart)
# -------------------------------------------------------------
@router.get("/graphs/complaints-by-category")
def get_graph_complaints_by_category(
    bureau: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    if user and user.role in {ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR}:
        return {"title": "Complaints by Category", "total": 0, "categories": []}

    query = db.query(Complaint)
    if user and user.role == ROLE_INSTITUTE_HEAD and user.institution_id:
        query = query.filter(Complaint.institution_id == user.institution_id, Complaint.is_confidential == False)
    if bureau:
        query = query.filter(Complaint.bureau == bureau)
    if status_filter:
        query = query.filter(Complaint.status == status_filter)

    complaints = query.all()
    counts: Dict[str, int] = {}
    for c in complaints:
        cat = c.category or "General Grievance"
        counts[cat] = counts.get(cat, 0) + 1

    items = [{"category": k, "count": v} for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)]
    return {
        "title": "Complaints by Category",
        "total": len(complaints),
        "categories": items,
        "unit": "complaints"
    }

# -------------------------------------------------------------
# Graph C — Application and Approval Trends (Time Series)
# -------------------------------------------------------------
@router.get("/graphs/application-trends")
def get_graph_application_trends(
    academic_year: Optional[str] = Query("2026-2027"),
    db: Session = Depends(get_db)
):
    apps = db.query(Application).filter(Application.academic_year == academic_year).all()

    # Bucket by month
    monthly_data = {
        "Jun 2026": {"submitted": 0, "approved": 0, "in_progress": 0},
        "Jul 2026": {"submitted": 0, "approved": 0, "in_progress": 0},
        "Aug 2026": {"submitted": 0, "approved": 0, "in_progress": 0},
        "Sep 2026": {"submitted": 0, "approved": 0, "in_progress": 0},
        "Oct 2026": {"submitted": 0, "approved": 0, "in_progress": 0}
    }

    for a in apps:
        if a.submitted_at:
            m_key = a.submitted_at.strftime("%b %Y")
            if m_key not in monthly_data:
                monthly_data[m_key] = {"submitted": 0, "approved": 0, "in_progress": 0}
            monthly_data[m_key]["submitted"] += 1
            if a.status == "Approved":
                monthly_data[m_key]["approved"] += 1
            else:
                monthly_data[m_key]["in_progress"] += 1

    series = [{"month": k, **v} for k, v in monthly_data.items()]
    return {
        "title": f"Application & Approval Trends ({academic_year})",
        "academic_year": academic_year,
        "series": series
    }

# -------------------------------------------------------------
# Graph D — Application Ageing & Stage-Wise Pendency
# -------------------------------------------------------------
@router.get("/graphs/pendency-ageing")
def get_graph_pendency_ageing(user: Optional[User] = Depends(get_optional_user), db: Session = Depends(get_db)):
    if not user or user.role in {ROLE_PUBLIC_VISITOR, ROLE_STUDENT_COMPLAINANT}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: Analytics graphs are restricted to authorized officers.")
    today = date.today()
    apps = db.query(Application).filter(
        Application.status.notin_(["Approved", "Rejected", "Disposed", "Closed"])
    ).all()

    buckets = {
        "0-7 days (Within SLA)": 0,
        "8-15 days (Due Soon)": 0,
        "16-30 days (Overdue)": 0,
        "> 30 days (Critical Breach)": 0
    }

    for a in apps:
        sub_date = a.submitted_at or today
        age = (today - sub_date).days
        if age <= 7:
            buckets["0-7 days (Within SLA)"] += 1
        elif age <= 15:
            buckets["8-15 days (Due Soon)"] += 1
        elif age <= 30:
            buckets["16-30 days (Overdue)"] += 1
        else:
            buckets["> 30 days (Critical Breach)"] += 1

    return {
        "title": "Application Ageing & Stage-Wise Pendency",
        "total_active": len(apps),
        "buckets": [{"age_bracket": k, "count": v} for k, v in buckets.items()]
    }

# -------------------------------------------------------------
# Graph E — Regional and State-Wise Analytics
# -------------------------------------------------------------
@router.get("/graphs/regional-distribution")
def get_graph_regional_distribution(user: Optional[User] = Depends(get_optional_user), db: Session = Depends(get_db)):
    if not user or user.role in {ROLE_PUBLIC_VISITOR, ROLE_STUDENT_COMPLAINANT}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: Analytics graphs are restricted to authorized officers.")
    state_results = db.query(
        Institution.state,
        func.count(Institution.id).label("count")
    ).group_by(Institution.state).order_by(desc("count")).limit(10).all()

    items = [{"state": r[0] or "Unknown", "institutions_count": r[1]} for r in state_results]
    return {
        "title": "State-Wise Institutional Density",
        "top_states": items
    }

# -------------------------------------------------------------
# Graph F — Application Funnel
# -------------------------------------------------------------
@router.get("/graphs/application-funnel")
def get_graph_application_funnel(user: Optional[User] = Depends(get_optional_user), db: Session = Depends(get_db)):
    if not user or user.role in {ROLE_PUBLIC_VISITOR, ROLE_STUDENT_COMPLAINANT}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: Analytics graphs are restricted to authorized officers.")
    apps = db.query(Application).all()
    total = len(apps)

    lodged = total
    passed_scrutiny = sum(1 for a in apps if a.stage_code in ["SCRUTINY", "EVC_SCHEDULING", "EVC_EVALUATION", "SAC_SHC_REVIEW", "FINAL_DISPOSITION"])
    evc_conducted = sum(1 for a in apps if a.stage_code in ["EVC_EVALUATION", "SAC_SHC_REVIEW", "FINAL_DISPOSITION"])
    final_disposition = sum(1 for a in apps if a.stage_code == "FINAL_DISPOSITION" or a.status in ["Approved", "Rejected"])

    funnel_steps = [
        {"step": "Initial Lodgement", "count": lodged, "conversion_rate": 100.0},
        {"step": "Scrutiny Verified", "count": passed_scrutiny, "conversion_rate": round((passed_scrutiny/lodged)*100.0, 1) if lodged else 0},
        {"step": "EVC Inspected", "count": evc_conducted, "conversion_rate": round((evc_conducted/lodged)*100.0, 1) if lodged else 0},
        {"step": "Final Disposition", "count": final_disposition, "conversion_rate": round((final_disposition/lodged)*100.0, 1) if lodged else 0}
    ]

    return {
        "title": "Application Processing Funnel",
        "total_applications": total,
        "funnel": funnel_steps
    }

# -------------------------------------------------------------
# Graph G — EVC Scheduling and Completion
# -------------------------------------------------------------
@router.get("/graphs/evc-status")
def get_graph_evc_status(user: Optional[User] = Depends(get_optional_user), db: Session = Depends(get_db)):
    if not user or user.role in {ROLE_PUBLIC_VISITOR, ROLE_STUDENT_COMPLAINANT}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: Analytics graphs are restricted to authorized officers.")
    schedules = db.query(EVCSchedule).all()
    status_counts = {
        "Scheduled": 0,
        "Completed": 0,
        "Delayed / Overdue": 0,
        "Pending Report Filing": 0
    }
    today = date.today()

    for s in schedules:
        if s.status == "Completed":
            status_counts["Completed"] += 1
        elif s.status == "Scheduled":
            status_counts["Scheduled"] += 1
            if s.scheduled_date < today:
                status_counts["Delayed / Overdue"] += 1
        if not s.report_submitted and s.status != "Completed":
            status_counts["Pending Report Filing"] += 1

    return {
        "title": "Expert Visit Committee (EVC) Operational Status",
        "total_evc_sessions": len(schedules),
        "status_breakdown": [{"status": k, "count": v} for k, v in status_counts.items()]
    }

# -------------------------------------------------------------
# Graph H — Statutory Compliance Index
# -------------------------------------------------------------
@router.get("/graphs/compliance-index")
def get_graph_compliance_index(user: Optional[User] = Depends(get_optional_user), db: Session = Depends(get_db)):
    if not user or user.role in {ROLE_PUBLIC_VISITOR, ROLE_STUDENT_COMPLAINANT}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: Analytics graphs are restricted to authorized officers.")
    obligations = db.query(ComplianceObligation).all()
    undertakings = db.query(Undertaking).all()

    total_assessed = len(obligations) + len(undertakings)
    satisfied_obs = sum(1 for o in obligations if o.status == "Satisfied by evidence")
    verified_und = sum(1 for u in undertakings if u.status == "Verified & Accepted")
    total_satisfied = satisfied_obs + verified_und

    index_pct = round((total_satisfied / total_assessed) * 100.0, 1) if total_assessed > 0 else 100.0

    return {
        "title": "National Statutory Compliance Index",
        "compliance_index_percentage": index_pct,
        "total_requirements_assessed": total_assessed,
        "verified_compliant_count": total_satisfied,
        "overdue_count": sum(1 for o in obligations if "overdue" in o.status.lower()) + sum(1 for u in undertakings if u.status == "Overdue")
    }

# -------------------------------------------------------------
# Graph I — Document Validity and Verification
# -------------------------------------------------------------
@router.get("/graphs/document-validity")
def get_graph_document_validity(user: Optional[User] = Depends(get_optional_user), db: Session = Depends(get_db)):
    if not user or user.role in {ROLE_PUBLIC_VISITOR, ROLE_STUDENT_COMPLAINANT}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: Analytics graphs are restricted to authorized officers.")
    validities = db.query(DocumentValidity).all()
    counts = {
        "Active": sum(1 for v in validities if v.status == "Active"),
        "Expiring Soon": sum(1 for v in validities if v.status == "Expiring Soon"),
        "Expired": sum(1 for v in validities if v.status == "Expired"),
        "Renewed": sum(1 for v in validities if v.status == "Renewed")
    }

    return {
        "title": "Statutory Lease & NOC Validity Monitor",
        "total_tracked_documents": len(validities),
        "breakdown": [{"status": k, "count": v} for k, v in counts.items()]
    }

# -------------------------------------------------------------
# Graph J — Officer Workload Distribution
# -------------------------------------------------------------
@router.get("/graphs/officer-workload")
def get_graph_officer_workload(
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER, ROLE_COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db)
):
    apps = db.query(Application).filter(Application.status != "Approved").all()
    cplts = db.query(Complaint).filter(Complaint.status != "Disposed").all()

    workload: Dict[str, Dict[str, int]] = {}
    for a in apps:
        owner = a.owner or "Unassigned"
        if owner not in workload:
            workload[owner] = {"applications": 0, "complaints": 0, "total": 0}
        workload[owner]["applications"] += 1
        workload[owner]["total"] += 1

    for c in cplts:
        assignee = c.assigned_to or "Unassigned"
        if assignee not in workload:
            workload[assignee] = {"applications": 0, "complaints": 0, "total": 0}
        workload[assignee]["complaints"] += 1
        workload[assignee]["total"] += 1

    items = [{"officer": k, **v} for k, v in sorted(workload.items(), key=lambda x: x[1]["total"], reverse=True)]
    return {
        "title": "Officer & Queue Workload Allocation",
        "officers": items
    }

# -------------------------------------------------------------
# Graph K — Workflow Bottleneck Heatmap
# -------------------------------------------------------------
@router.get("/graphs/bottleneck-heatmap")
def get_graph_bottleneck_heatmap(user: Optional[User] = Depends(get_optional_user), db: Session = Depends(get_db)):
    if not user or user.role in {ROLE_PUBLIC_VISITOR, ROLE_STUDENT_COMPLAINANT}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden: Analytics graphs are restricted to authorized officers.")
    apps = db.query(Application).all()
    today = date.today()

    stage_delay_stats: Dict[str, List[int]] = {}
    for a in apps:
        stage = a.current_stage or "Preliminary validation"
        if stage not in stage_delay_stats:
            stage_delay_stats[stage] = []

        sub_date = a.submitted_at or today
        delay = (today - sub_date).days
        stage_delay_stats[stage].append(delay)

    heatmap_cells = []
    for stage, delays in stage_delay_stats.items():
        avg_delay = round(sum(delays) / len(delays), 1) if delays else 0
        max_delay = max(delays) if delays else 0
        heatmap_cells.append({
            "stage_name": stage,
            "application_count": len(delays),
            "average_dwell_days": avg_delay,
            "max_dwell_days": max_delay,
            "bottleneck_severity": "High" if avg_delay > 14 else ("Medium" if avg_delay > 7 else "Normal")
        })

    return {
        "title": "Workflow Stage Dwell Time & Bottleneck Heatmap",
        "heatmap": heatmap_cells
    }

# -------------------------------------------------------------
# Graph L — AI Anomaly Review Queue
# -------------------------------------------------------------
@router.get("/graphs/anomaly-review-queue")
def get_graph_anomaly_queue(db: Session = Depends(get_db)):
    anomalous_docs = db.query(Document).filter(Document.is_anomaly == True).all()
    overlapping_cplts = db.query(Complaint).filter(Complaint.overlap_score >= 80).all()

    return {
        "title": "AI Cross-Check Anomaly & Conflict Queue",
        "flagged_documents_count": len(anomalous_docs),
        "overlapping_complaints_count": len(overlapping_cplts),
        "status": "Active Queue",
        "items": [
            {"id": d.id, "type": "Document Anomaly", "label": f"{d.document_type} (Mismatch in stamp/reference)", "severity": "High"}
            for d in anomalous_docs[:5]
        ] + [
            {"id": c.id, "type": "Conflict of Jurisdiction", "label": f"Grievance {c.case_number or c.id} cross-bureau overlap", "severity": "Medium"}
            for c in overlapping_cplts[:5]
        ]
    }

# -------------------------------------------------------------
# AI-Supported Risk and Workload Insights
# -------------------------------------------------------------
@router.get("/ai/risk-recommendations")
def get_ai_risk_recommendations(
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER, ROLE_COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db)
):
    """
    Scans authoritative records for SLA breach risks, repeated deficiencies,
    and officer workload imbalances with transparent indicators.
    """
    return risk_service.scan_and_generate_recommendations(db)

@router.post("/ai/risk-recommendations/{id}/action")
def apply_risk_recommendation_action(
    id: str,
    payload: RiskRecommendationActionRequest,
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER, ROLE_COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db)
):
    """
    Allows authorized officers to accept, dismiss, or correct an operational risk recommendation.
    Preserves audit history and reasons.
    """
    return risk_service.apply_user_action(
        rec_id=id,
        action=payload.action,
        notes=payload.notes,
        actor=user.username,
        role=user.role,
        db=db
    )

def sanitize_csv_cell(val: Any) -> str:
    """Neutralizes OWASP CSV/Excel Formula Injection."""
    if val is None:
        return ""
    s = str(val).strip()
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{s}"
    return s

# -------------------------------------------------------------
# Administrative Data Reports & Audit-Logged Exports
# -------------------------------------------------------------
@router.get("/export/institutions-csv")
def export_institutions_csv(
    state: Optional[str] = None,
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER, ROLE_COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db)
):
    query = db.query(Institution)
    if state:
        query = query.filter(Institution.state == state)
    institutions = query.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "permanent_id", "aicte_id", "name", "state", "district", "category", "institution_type", "approval_status", "verified_status", "total_intake", "data_source"])
    for inst in institutions:
        writer.writerow([
            sanitize_csv_cell(inst.id),
            sanitize_csv_cell(inst.permanent_id),
            sanitize_csv_cell(inst.aicte_id),
            sanitize_csv_cell(inst.name),
            sanitize_csv_cell(inst.state),
            sanitize_csv_cell(inst.district),
            sanitize_csv_cell(inst.category),
            sanitize_csv_cell(inst.institution_type),
            sanitize_csv_cell(inst.approval_status),
            sanitize_csv_cell(inst.verified_status),
            sanitize_csv_cell(inst.total_intake or 0),
            sanitize_csv_cell(inst.data_source)
        ])

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
        actor=user.username,
        role=user.role,
        action="EXPORT_INSTITUTIONS_CSV",
        entity_type="Institution",
        entity_id="ALL",
        details=f"Exported {len(institutions)} institutions to CSV (State filter: {state or 'All'})"
    )
    db.add(audit)
    db.commit()

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=aicte_institutions_export_{date.today().isoformat()}.csv"}
    )

