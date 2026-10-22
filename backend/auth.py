"""
Role-Based Access Control (RBAC), Session Verification & Cryptographic Authentication for AICTE ONE
"""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Set

import bcrypt
from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models import AuditLog, LoginHistory, Role, RolePermission, User, UserSession

# ---------------------------------------------------------------------------
# Standard 8 Statutory Role Categories
# ---------------------------------------------------------------------------
ROLE_SUPER_ADMIN = "SUPER_ADMIN"
ROLE_SECURITY_OFFICER = "SECURITY_OFFICER"
ROLE_COMPLIANCE_OFFICER = "POLICY_COMPLIANCE_OFFICER"
ROLE_COMPLAINT_OFFICER = "COMPLAINT_OFFICER"
ROLE_ANTI_RAGGING_OFFICER = "ANTI_RAGGING_OFFICER"
ROLE_INSTITUTE_HEAD = "INSTITUTE_HEAD"
ROLE_STUDENT_COMPLAINANT = "STUDENT_COMPLAINANT"
ROLE_PUBLIC_VISITOR = "PUBLIC_VISITOR"

# Legacy & Alias Compatibility
ROLE_ADMIN = ROLE_SUPER_ADMIN
ROLE_SCRUTINY = ROLE_SUPER_ADMIN
ROLE_EVC = ROLE_SUPER_ADMIN
ROLE_COMPLIANCE = ROLE_COMPLIANCE_OFFICER
ROLE_VIGILANCE = ROLE_COMPLAINT_OFFICER
ROLE_INSTITUTION = ROLE_INSTITUTE_HEAD

ALL_ROLES = [
    ROLE_SUPER_ADMIN,
    ROLE_SECURITY_OFFICER,
    ROLE_COMPLIANCE_OFFICER,
    ROLE_COMPLAINT_OFFICER,
    ROLE_ANTI_RAGGING_OFFICER,
    ROLE_INSTITUTE_HEAD,
    ROLE_STUDENT_COMPLAINANT,
    ROLE_PUBLIC_VISITOR
]

# Standard Permission Sets by Role
ROLE_PERMISSIONS_MAP: dict[str, Set[str]] = {
    ROLE_SUPER_ADMIN: {"*"},  # Full system-wide statutory access
    ROLE_SECURITY_OFFICER: {
        "security:view", "security:manage", "audit:view", "audit:export",
        "document:view_all", "document:verify", "institution:view_all",
        "complaint:view_all", "task:view", "task:manage"
    },
    ROLE_COMPLIANCE_OFFICER: {
        "compliance:view_all", "compliance:review", "compliance:manage",
        "institution:view_all", "application:view_all", "document:view_all",
        "task:view", "task:manage", "audit:view"
    },
    ROLE_COMPLAINT_OFFICER: {
        "complaint:view_all", "complaint:manage", "complaint:transfer",
        "complaint:dispose", "complaint:link", "institution:view_all",
        "task:view", "task:manage", "audit:view"
    },
    ROLE_ANTI_RAGGING_OFFICER: {
        "complaint:view_ragging", "complaint:manage_ragging", "complaint:hearing",
        "institution:view_all", "task:view", "task:manage", "audit:view"
    },
    ROLE_INSTITUTE_HEAD: {
        "institution:view_own", "institution:edit_own", "application:view_own",
        "application:submit", "compliance:view_own", "compliance:submit",
        "document:view_own", "document:upload", "complaint:view_own",
        "task:view"
    },
    ROLE_STUDENT_COMPLAINANT: {
        "complaint:submit", "complaint:view_own", "document:upload",
        "institution:view_public"
    },
    ROLE_PUBLIC_VISITOR: {
        "institution:view_public", "report:view_public", "health:view"
    }
}

security_bearer = HTTPBearer(auto_error=False)

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

# ---------------------------------------------------------------------------
# Cryptographic Password Operations (Bcrypt)
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt with standard cost factor."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a bcrypt hash."""
    if not hashed_password or not plain_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

# ---------------------------------------------------------------------------
# JWT & Session Token Operations
# ---------------------------------------------------------------------------
def hash_token(token: str) -> str:
    """Generates SHA-256 hash of token string for session index tracking."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = utc_now() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": utc_now()})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = utc_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": utc_now(), "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

# ---------------------------------------------------------------------------
# Security Event Logger Helper
# ---------------------------------------------------------------------------
def log_security_event(
    db: Session,
    actor: str,
    role: str,
    action: str,
    entity_type: str,
    entity_id: str,
    details: str,
    ip_address: Optional[str] = None,
    user_id: Optional[str] = None
):
    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
        actor=actor,
        role=role,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip_address,
        user_id=user_id,
        timestamp=utc_now()
    )
    db.add(audit)
    try:
        db.commit()
    except Exception:
        db.rollback()

# ---------------------------------------------------------------------------
# Authentication Dependencies
# ---------------------------------------------------------------------------
def get_current_user(
    request: Request,
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    aicte_session: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Extracts and cryptographically verifies the authenticated individual user.
    Tokens are accepted via 'Authorization: Bearer <token>' or 'aicte_session' cookie.
    Rejects spoofed X-Role/X-Actor headers and invalid/revoked sessions.
    """
    raw_token = None
    if auth_header and auth_header.credentials:
        raw_token = auth_header.credentials
    elif aicte_session:
        raw_token = aicte_session

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: No bearer token or active session cookie provided.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    payload = decode_token(raw_token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id = payload["sub"]
    token_digest = hash_token(raw_token)

    # Check session revocation table
    session_rec = db.query(UserSession).filter(
        UserSession.token_hash == token_digest,
        UserSession.user_id == user_id
    ).first()

    if not session_rec or session_rec.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked or expired.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account associated with this token does not exist.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive or suspended. Please contact the AICTE Administrator."
        )

    # Check account lockout status
    if user.locked_until:
        locked_time = user.locked_until.replace(tzinfo=None) if user.locked_until.tzinfo else user.locked_until
        now_time = utc_now().replace(tzinfo=None) if utc_now().tzinfo else utc_now()
        if locked_time > now_time:
            remaining = int((locked_time - now_time).total_seconds() / 60)
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account is temporarily locked due to multiple failed login attempts. Retry in {remaining} minute(s)."
            )

    return user

def get_optional_user(
    request: Request,
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    aicte_session: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Returns authenticated user if a valid token is present; otherwise returns None (for public access).
    """
    try:
        return get_current_user(request=request, auth_header=auth_header, aicte_session=aicte_session, db=db)
    except HTTPException:
        return None

# ---------------------------------------------------------------------------
# Authorization & RBAC Guard Dependencies
# ---------------------------------------------------------------------------
def require_roles(*allowed_roles: str):
    """
    FastAPI dependency enforcing server-side Role-Based Access Control.
    SUPER_ADMIN always possesses unrestricted statutory oversight.
    """
    normalized_allowed = {r.upper() for r in allowed_roles}
    # Map legacy aliases
    if "ADMIN" in normalized_allowed:
        normalized_allowed.add(ROLE_SUPER_ADMIN)
    if "SCRUTINY_OFFICER" in normalized_allowed or "EVC_COORDINATOR" in normalized_allowed:
        normalized_allowed.add(ROLE_SUPER_ADMIN)
    if "VIGILANCE_OFFICER" in normalized_allowed:
        normalized_allowed.add(ROLE_COMPLAINT_OFFICER)
    if "COMPLIANCE_OFFICER" in normalized_allowed:
        normalized_allowed.add(ROLE_COMPLIANCE_OFFICER)
    if "INSTITUTION_USER" in normalized_allowed:
        normalized_allowed.add(ROLE_INSTITUTE_HEAD)

    def role_dependency(user: User = Depends(get_current_user)) -> User:
        user_role = (user.role or "").upper()
        if user_role == ROLE_SUPER_ADMIN:
            return user

        if user_role not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Role '{user.role}' is not authorized to execute this regulatory operation. Required permissions: {', '.join(allowed_roles)}"
            )
        return user

    return role_dependency

def require_permission(permission_code: str):
    """
    FastAPI dependency verifying that the user has a specific granular permission.
    """
    def permission_dependency(user: User = Depends(get_current_user)) -> User:
        user_role = (user.role or "").upper()
        if user_role == ROLE_SUPER_ADMIN:
            return user

        user_perms = ROLE_PERMISSIONS_MAP.get(user_role, set())
        if "*" in user_perms or permission_code in user_perms:
            return user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access forbidden: User lack required permission '{permission_code}'."
        )

    return permission_dependency

# ---------------------------------------------------------------------------
# Tenant & Data Isolation Guards
# ---------------------------------------------------------------------------
def check_tenant_access(user: User, institution_id: Optional[str]) -> bool:
    """
    Enforces multi-institution data isolation:
    - Central AICTE officers and Super Admins can access all institutions.
    - Institute Heads can ONLY access their own institution.
    """
    if not institution_id:
        return True

    user_role = (user.role or "").upper()
    if user_role in {ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER, ROLE_COMPLIANCE_OFFICER, ROLE_COMPLAINT_OFFICER, ROLE_ANTI_RAGGING_OFFICER}:
        return True

    if user_role == ROLE_INSTITUTE_HEAD:
        if user.institution_id and user.institution_id != institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cross-institution access denied: Your account is restricted to institution '{user.institution_id}'."
            )
        return True

    # Complainants and public visitors have no direct administrative institution scope
    return True
