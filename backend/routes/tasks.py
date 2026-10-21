"""
Tasks & Action Queue Router
"""
import uuid
from typing import Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Form
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models import Task, Institution, AuditLog
from backend.schemas import TaskCreate, TaskResponse

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

@router.get("")
def list_tasks(
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Task)
    if priority:
        query = query.filter(Task.priority == priority)
    if status:
        query = query.filter(Task.status == status)
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
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    new_id = f"TSK-2026-{uuid.uuid4().hex[:4].upper()}"
    task = Task(
        id=new_id,
        title=payload.title,
        category=payload.category,
        priority=payload.priority or "Medium",
        status="Pending",
        due_date=payload.due_date,
        assigned_to=payload.assigned_to,
        bureau=payload.bureau,
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
        actor="Task Engine",
        role="Workflow Orchestrator",
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
def update_task_status(id: str, status: str = Form(...), notes: Optional[str] = Form(None), actor: str = Form("Officer"), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    old_status = task.status
    task.status = status
    if notes:
        task.resolution_notes = f"{task.resolution_notes or ''}\n[{status}: {notes}]"

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=actor,
        role="Assigned Officer",
        action="Updated Task Status",
        entity_type="Task",
        entity_id=task.id,
        details=f"Updated status from '{old_status}' to '{status}'."
    )
    db.add(audit)
    db.commit()
    return {"message": f"Task status updated to {status}"}

@router.post("/{id}/escalate")
def escalate_task(id: str, reason: str = Form(...), escalated_to: str = Form("Bureau Head"), actor: str = Form("Officer"), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.priority = "Critical"
    task.status = "Escalated"
    task.assigned_to = escalated_to
    task.resolution_notes = f"{task.resolution_notes or ''}\n[Escalated to {escalated_to}: {reason}]"

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=actor,
        role="Escalation Authority",
        action="Escalated Action Task",
        entity_type="Task",
        entity_id=task.id,
        details=f"Escalated task {task.id} to {escalated_to}. Reason: {reason}."
    )
    db.add(audit)
    db.commit()
    return {"message": f"Task escalated to {escalated_to}"}
