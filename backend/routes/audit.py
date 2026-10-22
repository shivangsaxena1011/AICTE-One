"""
Audit Trail Router: Chronological, Append-Only Logging
Protected with RBAC: Restricted to Super Administrator & Security Officer
"""
import io
import csv
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from backend.database import get_db
from backend.models import AuditLog, User
from backend.auth import (
    get_current_user, require_roles,
    ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER
)

router = APIRouter(prefix="/api/audit", tags=["Audit Trail"])

@router.get("")
@router.get("/logs")
def list_audit_logs(
    q: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER)),
    db: Session = Depends(get_db)
):
    """
    Retrieves chronological, append-only regulatory audit records.
    Restricted to statutory administrators and security oversight officers.
    """
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

def sanitize_csv_cell(val: str) -> str:
    """Neutralizes OWASP CSV/Excel Formula Injection."""
    if val is None:
        return ""
    s = str(val).strip()
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{s}"
    return s

@router.get("/export-csv")
def export_audit_csv(
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER)),
    db: Session = Depends(get_db)
):
    """
    Exports official audit logs in CSV format.
    Requires Super Administrator or Security Officer privilege.
    """
    logs = db.query(AuditLog).order_by(desc(AuditLog.timestamp)).limit(1000).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Log ID", "Timestamp", "Actor", "Role", "Action", "Entity Type", "Record ID", "Details"])
    for a in logs:
        writer.writerow([
            sanitize_csv_cell(a.id),
            sanitize_csv_cell(a.timestamp.strftime("%Y-%m-%d %H:%M:%S")),
            sanitize_csv_cell(a.actor),
            sanitize_csv_cell(a.role),
            sanitize_csv_cell(a.action),
            sanitize_csv_cell(a.entity_type),
            sanitize_csv_cell(a.entity_id),
            sanitize_csv_cell(a.details)
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=aicte_audit_trail.csv"}
    )
