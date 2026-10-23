"""
AI Copilot Router: Evidence-Grounded Q&A with Record Citations
Secured with RBAC and Persona-Scoped Evidence Retainment
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.schemas import CopilotQuery, CopilotResponse
from backend.services.copilot_service import copilot_service
from backend.auth import (
    get_current_user,
    ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER, ROLE_COMPLIANCE_OFFICER,
    ROLE_COMPLAINT_OFFICER, ROLE_ANTI_RAGGING_OFFICER,
    ROLE_INSTITUTE_HEAD, ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR
)

router = APIRouter(prefix="/api/copilot", tags=["AI Copilot"])

@router.post("/chat", response_model=CopilotResponse)
@router.post("/query", response_model=CopilotResponse)
def copilot_chat(
    payload: CopilotQuery,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Evidence-grounded regulatory copilot with role-scoped institutional context:
    - Institute Heads receive reasoning scoped strictly to their institution.
    - Students receive reasoning scoped to their complaints and general regulations.
    - Central officers receive comprehensive statutory context.
    """
    if user.role == ROLE_PUBLIC_VISITOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: AI Copilot is restricted to authorized regulatory officers and institutional representatives."
        )

    result = copilot_service.answer_query(
        query=payload.query,
        user=user,
        db=db,
        use_gemini=payload.use_gemini or False,
        api_key=payload.api_key
    )
    return result
