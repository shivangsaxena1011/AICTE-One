"""
In-App Notifications Router
Secured with Individual Account and Role-Scoped Delivery
"""
import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from backend.database import get_db
from backend.models import Notification, User
from backend.auth import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("")
def list_notifications(
    unread_only: bool = Query(False),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Notification).filter(
        or_(
            Notification.user_id == "all",
            Notification.user_id == user.id,
            Notification.user_id == user.role
        )
    )
    if unread_only:
        query = query.filter(Notification.is_read == False)
    notifs = query.order_by(desc(Notification.created_at)).all()
    results = []
    for n in notifs:
        results.append({
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "category": n.category,
            "urgency": n.urgency,
            "link_type": n.link_type,
            "link_id": n.link_id,
            "is_read": n.is_read,
            "created_at": n.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    return results

@router.post("/{id}/read")
def mark_read(
    id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    n = db.query(Notification).filter(Notification.id == id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.is_read = True
    db.commit()
    return {"message": "Notification marked as read"}

@router.post("/mark-all-read")
def mark_all_read(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(Notification).filter(
        or_(
            Notification.user_id == "all",
            Notification.user_id == user.id,
            Notification.user_id == user.role
        )
    ).update({Notification.is_read: True}, synchronize_session=False)
    db.commit()
    return {"message": "All notifications marked as read"}
