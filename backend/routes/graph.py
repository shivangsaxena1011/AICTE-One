"""
Regulatory Intelligence Graph Router
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    Institution, Application, Document, ComplianceObligation, Complaint, Task, EVCSchedule
)

router = APIRouter(prefix="/api/graph", tags=["Regulatory Intelligence Graph"])

@router.get("")
@router.get("/summary")
def get_graph_data(institution_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """
    Builds the complete Regulatory Intelligence Graph connecting Institutions,
    Applications, Documents, Complaints, Compliance, and Officials.
    """
    nodes = []
    edges = []
    node_ids = set()

    def add_node(nid, label, ntype, status, details=""):
        if nid not in node_ids:
            node_ids.add(nid)
            color_map = {
                "institution": "#1a365d",  # Deep Navy
                "application": "#2563eb",  # Blue
                "document": "#0d9488",     # Teal
                "compliance": "#d97706",   # Amber
                "complaint": "#dc2626",    # Red
                "evc": "#7c3aed",          # Purple
                "task": "#4f46e5"          # Indigo
            }
            nodes.append({
                "id": nid,
                "label": label,
                "type": ntype,
                "status": status,
                "color": color_map.get(ntype, "#64748b"),
                "details": details
            })

    def add_edge(src, tgt, label):
        if src in node_ids and tgt in node_ids:
            edges.append({
                "source": src,
                "target": tgt,
                "label": label
            })

    # Query entities
    inst_query = db.query(Institution)
    if institution_id:
        inst_query = inst_query.filter(Institution.id == institution_id)
    institutions = inst_query.limit(10).all()

    for inst in institutions:
        add_node(inst.id, inst.name, "institution", inst.approval_status, f"Permanent ID: {inst.permanent_id} | {inst.city}")

        # Applications
        for a in inst.applications:
            add_node(a.id, f"{a.type} ({a.current_stage})", "application", a.status, f"Progress: {a.progress}% | Owner: {a.owner}")
            add_edge(inst.id, a.id, "SUBMITTED")

            # EVC
            for evc in a.evc_schedules:
                add_node(evc.id, f"EVC: {evc.scheduled_date}", "evc", evc.status, f"Chair: {evc.committee_chair}")
                add_edge(a.id, evc.id, "SCHEDULED_EVC")

            # Documents attached to application
            for d in a.documents:
                add_node(d.id, d.name, "document", d.status, f"Type: {d.document_type} | Confidence: {d.confidence}")
                add_edge(a.id, d.id, "REQUIRES_DOCUMENT")

        # Documents attached directly to institution
        for d in inst.documents:
            if d.id not in node_ids:
                add_node(d.id, d.name, "document", d.status, f"Type: {d.document_type}")
                add_edge(inst.id, d.id, "HAS_DOCUMENT")

        # Compliance Obligations
        for c in inst.compliance_obligations:
            add_node(c.id, c.title, "compliance", c.status, f"Due: {c.due_date} | Party: {c.responsible_party}")
            add_edge(inst.id, c.id, "OBLIGATED_TO")

        # Complaints
        for cplt in inst.complaints:
            add_node(cplt.id, f"{cplt.bureau}: {cplt.category}", "complaint", cplt.status, cplt.summary[:60])
            add_edge(inst.id, cplt.id, "SUBJECT_OF_COMPLAINT")

            if cplt.related_case_id and cplt.related_case_id in node_ids:
                add_edge(cplt.id, cplt.related_case_id, "POTENTIAL_OVERLAP")

        # Tasks
        for t in inst.tasks:
            add_node(t.id, t.title, "task", t.status, f"Assigned: {t.assigned_to} | Priority: {t.priority}")
            add_edge(inst.id, t.id, "ACTION_REQUIRED")

    return {
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges)
    }
