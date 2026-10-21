"""
AI Copilot Router: Evidence-Grounded Q&A with Record Citations
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    Institution, Application, Document, ComplianceObligation, Complaint
)
from backend.schemas import CopilotQuery, CopilotResponse
from backend.services.copilot_service import copilot_service

router = APIRouter(prefix="/api/copilot", tags=["AI Copilot"])

@router.post("/chat", response_model=CopilotResponse)
def copilot_chat(payload: CopilotQuery, db: Session = Depends(get_db)):
    # Build complete active context from stored records
    institutions = db.query(Institution).all()
    applications = db.query(Application).all()
    documents = db.query(Document).all()
    compliance = db.query(ComplianceObligation).all()
    complaints = db.query(Complaint).all()

    context = {
        "institutions": [{
            "id": i.id, "name": i.name, "permanent_id": i.permanent_id, "city": i.city,
            "state": i.state, "category": i.category, "approval_status": i.approval_status,
            "approval_period": i.approval_period, "affiliation": i.affiliation,
            "total_intake": i.total_intake, "programmes_count": i.programmes_count
        } for i in institutions],
        "applications": [{
            "id": a.id, "institution_id": a.institution_id, "institution_name": a.institution.name if a.institution else "",
            "type": a.type, "current_stage": a.current_stage, "status": a.status,
            "owner": a.owner, "progress": a.progress, "due_date": a.due_date.isoformat() if a.due_date else ""
        } for a in applications],
        "documents": [{
            "id": d.id, "institution_id": d.institution_id, "application_id": d.application_id,
            "name": d.name, "document_type": d.document_type, "status": d.status,
            "confidence": d.confidence, "findings": d.findings or ""
        } for d in documents],
        "compliance": [{
            "id": c.id, "institution_id": c.institution_id, "institution_name": c.institution.name if c.institution else "",
            "title": c.title, "due_date": c.due_date.isoformat(), "status": c.status
        } for c in compliance],
        "complaints": [{
            "id": c.id, "institution_id": c.institution_id, "bureau": c.bureau,
            "category": c.category, "summary": c.summary, "status": c.status,
            "related_case_id": c.related_case_id
        } for c in complaints]
    }

    result = copilot_service.answer_query(
        query=payload.query,
        context_data=context,
        use_gemini=payload.use_gemini or False,
        api_key=payload.api_key
    )
    return result
