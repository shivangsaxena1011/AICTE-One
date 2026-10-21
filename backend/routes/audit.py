"""
Audit Trail Router: Chronological, Append-Only Logging
"""
import io
import csv
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from backend.database import get_db
from backend.models import AuditLog

router = APIRouter(prefix="/api/audit", tags=["Audit Trail"])

@router.get("")
def list_audit_logs(
    q: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if q:
        query = query.filter(or_(
            AuditLog.actor.ilike(f"%{q}%"),
            AuditLog.action.ilike(f"%{q}%"),
            AuditLog.entity_id.ilike(f"%{q}%"),
            AuditLog.details.ilike(f"%{q}%")
        ))

    logs = query.order_by(desc(AuditLog.timestamp)).limit(limit).all()
    results = []
    for a in logs:
        results.append({
            "id": a.id,
            "timestamp": a.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "actor": a.actor,
            "role": a.role,
            "action": a.action,
            "entity_type": a.entity_type,
            "record": a.entity_id,
            "detail": a.details
        })
    return results

@router.get("/export-csv")
def export_audit_csv(db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(desc(AuditLog.timestamp)).limit(1000).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Log ID", "Timestamp", "Actor", "Role", "Action", "Entity Type", "Record ID", "Details"])
    for a in logs:
        writer.writerow([
            a.id, a.timestamp.strftime("%Y-%m-%d %H:%M:%S"), a.actor, a.role,
            a.action, a.entity_type, a.entity_id, a.details
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=aicte_audit_trail.csv"}
    )
