"""
Role-Based Access Control (RBAC) & Authentication Dependency for AICTE ONE
"""
from typing import List, Optional
from fastapi import Header, HTTPException, status

# Recognized administrative & institutional roles
ROLE_ADMIN = "ADMIN"
ROLE_SCRUTINY = "SCRUTINY_OFFICER"
ROLE_EVC = "EVC_COORDINATOR"
ROLE_COMPLIANCE = "COMPLIANCE_OFFICER"
ROLE_VIGILANCE = "VIGILANCE_OFFICER"
ROLE_INSTITUTION = "INSTITUTION_USER"

ALL_ROLES = [
    ROLE_ADMIN,
    ROLE_SCRUTINY,
    ROLE_EVC,
    ROLE_COMPLIANCE,
    ROLE_VIGILANCE,
    ROLE_INSTITUTION
]

def get_current_user(
    x_role: Optional[str] = Header(default=ROLE_ADMIN),
    x_actor: Optional[str] = Header(default="admin@aicte-india.org")
):
    """
    Extracts the authenticated actor persona and simulated role.
    Defaults to system administrator if no specific header is provided.
    """
    role = (x_role or ROLE_ADMIN).upper()
    return {
        "role": role,
        "actor": x_actor or "admin@aicte-india.org"
    }

def require_roles(*allowed_roles: str):
    """
    FastAPI dependency enforcing RBAC permission verification.
    System Administrators always bypass bureau-specific restrictions.
    """
    def dependency(
        x_role: Optional[str] = Header(default=ROLE_ADMIN),
        x_actor: Optional[str] = Header(default="admin@aicte-india.org")
    ):
        role = (x_role or ROLE_ADMIN).upper()
        if role == ROLE_ADMIN:
            return {"role": role, "actor": x_actor}

        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Role '{role}' is not authorized to execute this regulatory operation. Required permissions: {', '.join(allowed_roles)}"
            )
        return {"role": role, "actor": x_actor}
    return dependency
