"""
Tasks & Action Queue Router
Protected with RBAC & Multi-Institution Tenant Isolation
"""
import uuid
from typing import Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Form, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models import Task, Institution, AuditLog, User
from backend.schemas import TaskCreate, TaskResponse
from backend.auth import (
    get_current_user, require_roles,
    ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER, ROLE_COMPLIANCE_OFFICER,
    ROLE_COMPLAINT_OFFICER, ROLE_ANTI_RAGGING_OFFICER,
    ROLE_INSTITUTE_HEAD, ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR
)

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

@router.get("")
def list_tasks(
    priority: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    assigned_to: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lists action queue tasks scoped by RBAC and tenant isolation:
    - Institute Heads see ONLY tasks for their own institution.
    - Officers see statutory bureau tasks.
    - Students and public visitors are denied access (403 Forbidden).
    """
    if user.role in {ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Internal action queues are restricted to regulatory officers and authorized institutional representatives."
        )

    query = db.query(Task)

    if user.role == ROLE_INSTITUTE_HEAD:
        if not user.institution_id:
            return []
        query = query.filter(Task.institution_id == user.institution_id)

    if priority:
        query = query.filter(Task.priority == priority)
    if status_filter:
        query = query.filter(Task.status == status_filter)
    if assigned_to:
        query = query.filter(Task.assigned_to == assigned_to)

    tasks = query.order_by(Task.due_date).all()
    results = []
    for t in tasks:
        results.append({
            "id": t.id,
            "title": t.title,
            "category": t.category,
            "priority": t.priority,
            "status": t.status,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "assigned_to": t.assigned_to,
            "bureau": t.bureau,
            "institution_id": t.institution_id,
            "institution_name": t.institution.name if t.institution else "General",
            "application_id": t.application_id,
            "complaint_id": t.complaint_id,
            "document_id": t.document_id,
            "obligation_id": t.obligation_id,
            "resolution_notes": t.resolution_notes
        })
    return results

@router.post("")
def create_task(
    payload: TaskCreate,
    user: User = Depends(require_roles(
        ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER, ROLE_COMPLIANCE_OFFICER,
        ROLE_COMPLAINT_OFFICER, ROLE_ANTI_RAGGING_OFFICER
    )),
    db: Session = Depends(get_db)
):
    new_id = f"TSK-2026-{uuid.uuid4().hex[:4].upper()}"
    task = Task(
        id=new_id,
        title=payload.title,
        category=payload.category,
        priority=payload.priority or "Medium",
        status="Pending",
        due_date=payload.due_date,
        assigned_to=payload.assigned_to or user.full_name,
        bureau=payload.bureau or user.department or "Central Bureau",
        institution_id=payload.institution_id,
        application_id=payload.application_id,
        complaint_id=payload.complaint_id,
        document_id=payload.document_id,
        obligation_id=payload.obligation_id,
        resolution_notes=payload.resolution_notes
    )
    db.add(task)

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=user.username,
        role=user.role,
        action="Created Action Task",
        entity_type="Task",
        entity_id=task.id,
        details=f"Created task '{task.title}' assigned to {task.assigned_to} ({task.bureau}). Priority: {task.priority}."
    )
    db.add(audit)
    db.commit()
    db.refresh(task)
    return {"message": "Task created successfully", "task_id": task.id}

@router.post("/{id}/status")
async def update_task_status(
    id: str,
    request: Request,
    status_val: Optional[str] = Form(None, alias="status"),
    notes: Optional[str] = Form(None),
    actor: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if user.role in {ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR}:
        raise HTTPException(status_code=403, detail="Not authorized to update action tasks.")

    if user.role == ROLE_INSTITUTE_HEAD:
        if user.institution_id and user.institution_id != task.institution_id:
            raise HTTPException(status_code=403, detail="Cross-institution task update denied.")

    content_type = request.headers.get("content-type", "")
    req_status = status_val
    req_notes = notes

    if "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict):
                req_status = body.get("status") or req_status
                req_notes = body.get("notes") or body.get("resolution_notes") or req_notes
        except Exception:
            pass

    if not req_status:
        req_status = "Completed"

    old_status = task.status
    task.status = req_status
    if req_notes:
        task.resolution_notes = req_notes

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=user.username,
        role=user.role,
        action="Updated Task Status",
        entity_type="Task",
        entity_id=task.id,
        details=f"Transitioned task '{task.title}' from '{old_status}' to '{req_status}'."
    )
    db.add(audit)
    db.commit()
    return {"message": "Task updated successfully", "status": task.status}
