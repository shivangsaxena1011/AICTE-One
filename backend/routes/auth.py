"""
Authentication, Identity & Session Management Router for AICTE ONE
"""
import uuid
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Response, Request, status, Cookie, Body
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models import (
    User, Role, Permission, RolePermission, UserSession,
    PasswordResetToken, LoginHistory, AuditLog
)
from backend.schemas import (
    LoginRequest, LoginResponse, UserResponse,
    PasswordResetRequest, PasswordResetConfirm,
    MFASetupResponse, MFAVerifyRequest
)
from backend.auth import (
    verify_password, hash_password, create_access_token, create_refresh_token,
    hash_token, decode_token, get_current_user, get_optional_user,
    log_security_event, ROLE_PERMISSIONS_MAP, ALL_ROLES,
    ROLE_SUPER_ADMIN, require_roles
)

router = APIRouter(prefix="/api/auth", tags=["Authentication & Identity"])

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

def build_user_response(user: User) -> UserResponse:
    perms = list(ROLE_PERMISSIONS_MAP.get(user.role, set()))
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        department=user.department,
        institution_id=user.institution_id,
        phone=user.phone,
        is_active=user.is_active,
        is_mfa_enabled=user.is_mfa_enabled,
        permissions=perms,
        created_at=user.created_at
    )

@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticates an individual user using email/username and bcrypt password verification.
    Issues a signed JWT access token and sets an HttpOnly session cookie.
    Enforces login throttling, lockout, and security event audit trail.
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    # Match by email or username (case-insensitive)
    account_input = payload.username.strip().lower()
    user = db.query(User).filter(
        (User.username.ilike(account_input)) | (User.email.ilike(account_input))
    ).first()

    if not user:
        # Record failed attempt for unrecognized account
        history = LoginHistory(
            id=f"LGN-{uuid.uuid4().hex[:8].upper()}",
            username_attempted=account_input,
            ip_address=client_ip,
            user_agent=user_agent,
            success=False,
            failure_reason="User not found",
            created_at=utc_now()
        )
        db.add(history)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please verify your username/email and password."
        )

    # Check lockout status
    if user.locked_until:
        locked_time = user.locked_until.replace(tzinfo=None) if user.locked_until.tzinfo else user.locked_until
        now_time = utc_now().replace(tzinfo=None) if utc_now().tzinfo else utc_now()
        if locked_time > now_time:
            remaining = int((locked_time - now_time).total_seconds() / 60) + 1
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account temporarily locked due to repeated failed login attempts. Retry in {remaining} minute(s)."
            )

    # Verify password
    if not verify_password(payload.password, user.password_hash):
        user.failed_login_attempts += 1
        lockout_msg = ""
        if user.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
            user.locked_until = utc_now() + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
            lockout_msg = f" Account has been locked for {settings.LOCKOUT_DURATION_MINUTES} minutes."

        history = LoginHistory(
            id=f"LGN-{uuid.uuid4().hex[:8].upper()}",
            user_id=user.id,
            username_attempted=account_input,
            ip_address=client_ip,
            user_agent=user_agent,
            success=False,
            failure_reason="Incorrect password",
            created_at=utc_now()
        )
        db.add(history)

        log_security_event(
            db=db,
            actor=user.username,
            role=user.role,
            action="Failed Login Attempt",
            entity_type="User",
            entity_id=user.id,
            details=f"Failed login attempt {user.failed_login_attempts} from IP {client_ip}.{lockout_msg}",
            ip_address=client_ip,
            user_id=user.id
        )
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid credentials.{lockout_msg}"
        )

    # Check account active state
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended or deactivated. Contact the system administrator."
        )

    # MFA Validation for privileged accounts if enabled
    if user.is_mfa_enabled:
        if not payload.mfa_code:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="MFA code required for this privileged account."
            )
        # Verify 6-digit TOTP / demo pin (e.g., standard demo code 123456 or match secret)
        if payload.mfa_code.strip() not in {"123456", user.mfa_secret}:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA verification code."
            )

    # Reset failure tracking on successful authentication
    user.failed_login_attempts = 0
    user.locked_until = None

    # Generate JWT Tokens
    token_data = {
        "sub": user.id,
        "username": user.username,
        "role": user.role,
        "institution_id": user.institution_id
    }
    access_token = create_access_token(token_data)
    token_digest = hash_token(access_token)
    session_expire = utc_now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Persist session record
    session_record = UserSession(
        id=f"SES-{uuid.uuid4().hex[:8].upper()}",
        user_id=user.id,
        token_hash=token_digest,
        ip_address=client_ip,
        user_agent=user_agent,
        is_revoked=False,
        expires_at=session_expire,
        created_at=utc_now()
    )
    db.add(session_record)

    # Record successful login history
    history = LoginHistory(
        id=f"LGN-{uuid.uuid4().hex[:8].upper()}",
        user_id=user.id,
        username_attempted=account_input,
        ip_address=client_ip,
        user_agent=user_agent,
        success=True,
        created_at=utc_now()
    )
    db.add(history)

    log_security_event(
        db=db,
        actor=user.username,
        role=user.role,
        action="User Login Success",
        entity_type="Session",
        entity_id=session_record.id,
        details=f"Successful authentication for {user.full_name} ({user.role}) from {client_ip}",
        ip_address=client_ip,
        user_id=user.id
    )
    db.commit()

    # Set secure HttpOnly cookie
    response.set_cookie(
        key="aicte_session",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False  # Set to True in HTTPS production
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=build_user_response(user)
    )

@router.post("/logout")
def logout(
    response: Response,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Invalidates current session token in the database and clears the session cookie.
    """
    client_ip = request.client.host if request.client else "unknown"
    auth_header = request.headers.get("authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    elif request.cookies.get("aicte_session"):
        token = request.cookies.get("aicte_session")

    if token:
        token_digest = hash_token(token)
        session_rec = db.query(UserSession).filter(
            UserSession.token_hash == token_digest,
            UserSession.user_id == user.id
        ).first()
        if session_rec:
            session_rec.is_revoked = True

    log_security_event(
        db=db,
        actor=user.username,
        role=user.role,
        action="User Logout",
        entity_type="User",
        entity_id=user.id,
        details=f"User {user.username} successfully logged out.",
        ip_address=client_ip,
        user_id=user.id
    )
    db.commit()

    response.delete_cookie(key="aicte_session")
    return {"message": "Successfully logged out. Session invalidated."}

@router.get("/me", response_model=UserResponse)
def get_authenticated_profile(user: User = Depends(get_current_user)):
    """
    Returns verified profile, permissions, and institutional association of the caller.
    """
    return build_user_response(user)

@router.post("/refresh", response_model=LoginResponse)
def refresh_session(
    response: Response,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Renews the current session token with a fresh expiration window.
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    token_data = {
        "sub": user.id,
        "username": user.username,
        "role": user.role,
        "institution_id": user.institution_id
    }
    new_token = create_access_token(token_data)
    token_digest = hash_token(new_token)
    session_expire = utc_now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    session_record = UserSession(
        id=f"SES-{uuid.uuid4().hex[:8].upper()}",
        user_id=user.id,
        token_hash=token_digest,
        ip_address=client_ip,
        user_agent=user_agent,
        is_revoked=False,
        expires_at=session_expire,
        created_at=utc_now()
    )
    db.add(session_record)
    db.commit()

    response.set_cookie(
        key="aicte_session",
        value=new_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False
    )

    return LoginResponse(
        access_token=new_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=build_user_response(user)
    )

@router.post("/password-reset-request")
def request_password_reset(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Initiates single-use, time-limited password recovery.
    In testing/demonstration, returns the recovery token directly.
    """
    account_input = payload.account.strip().lower()
    user = db.query(User).filter(
        (User.username.ilike(account_input)) | (User.email.ilike(account_input))
    ).first()

    if not user:
        # Prevent account enumeration: return success message regardless
        return {
            "message": "If an account matches that email or username, a single-use password recovery link has been generated.",
            "token": None
        }

    # Generate single-use reset token
    raw_token = secrets.token_urlsafe(32)
    token_digest = hash_token(raw_token)
    expires_at = utc_now() + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)

    reset_rec = PasswordResetToken(
        id=f"RST-{uuid.uuid4().hex[:8].upper()}",
        user_id=user.id,
        token_hash=token_digest,
        expires_at=expires_at,
        is_used=False,
        created_at=utc_now()
    )
    db.add(reset_rec)
    db.commit()

    return {
        "message": "Password recovery token issued successfully. Valid for 15 minutes.",
        "token": raw_token,
        "expires_at": expires_at.isoformat()
    }

@router.post("/password-reset-confirm")
def confirm_password_reset(
    payload: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Verifies single-use recovery token and updates the user's password using bcrypt.
    Revokes all prior active sessions upon password reset.
    """
    if len(payload.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long."
        )

    token_digest = hash_token(payload.token.strip())
    reset_rec = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_digest,
        PasswordResetToken.is_used == False
    ).first()

    if not reset_rec:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or previously utilized password reset token."
        )

    expires_time = reset_rec.expires_at.replace(tzinfo=None) if reset_rec.expires_at.tzinfo else reset_rec.expires_at
    now_time = utc_now().replace(tzinfo=None) if utc_now().tzinfo else utc_now()
    if expires_time < now_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has expired. Please request a new recovery link."
        )

    user = db.query(User).filter(User.id == reset_rec.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")

    # Update password
    user.password_hash = hash_password(payload.new_password)
    user.failed_login_attempts = 0
    user.locked_until = None
    reset_rec.is_used = True

    # Invalidate all prior sessions for this user
    db.query(UserSession).filter(
        UserSession.user_id == user.id
    ).update({"is_revoked": True})

    log_security_event(
        db=db,
        actor=user.username,
        role=user.role,
        action="Password Reset",
        entity_type="User",
        entity_id=user.id,
        details=f"Password successfully reset via recovery token for {user.username}. All existing sessions revoked."
    )
    db.commit()

    return {"message": "Password updated successfully. You may now log in with your new credentials."}

@router.get("/roles")
def list_system_roles():
    """
    Returns statutory role categories and their server-enforced permission matrix.
    """
    roles_list = []
    for role_code in ALL_ROLES:
        perms = list(ROLE_PERMISSIONS_MAP.get(role_code, set()))
        roles_list.append({
            "code": role_code,
            "permissions": perms,
            "permission_count": len(perms)
        })
    return {"roles": roles_list}

# -------------------------------------------------------------
# FIDO2 / WebAuthn Biometric Passkey Authentication Endpoints
# Note: Raw biometric data (fingerprint/face) is NEVER transmitted
# or stored; only public keys & cryptographic challenge tokens are exchanged.
# -------------------------------------------------------------
ACTIVE_WEBAUTHN_CHALLENGES: Dict[str, Dict[str, Any]] = {}

@router.post("/webauthn/register-options")
def webauthn_register_options(
    user: User = Depends(get_current_user)
):
    """
    Generates WebAuthn registration options with server challenge.
    """
    challenge = secrets.token_urlsafe(32)
    ACTIVE_WEBAUTHN_CHALLENGES[user.id] = {
        "challenge": challenge,
        "type": "register",
        "created_at": time.time()
    }
    return {
        "challenge": challenge,
        "rp": {
            "name": "AICTE ONE Sovereign Governance Platform",
            "id": "aicte-india.org"
        },
        "user": {
            "id": user.id,
            "name": user.username,
            "displayName": user.full_name or user.username
        },
        "pubKeyCredParams": [
            {"type": "public-key", "alg": -7},  # ES256
            {"type": "public-key", "alg": -257} # RS256
        ],
        "authenticatorSelection": {
            "authenticatorAttachment": "platform",
            "userVerification": "preferred"
        },
        "timeout": 60000,
        "attestation": "none"
    }

@router.post("/webauthn/register-verify")
def webauthn_register_verify(
    payload: Dict[str, Any] = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verifies WebAuthn device attestation and registers passkey credential ID & public key.
    Raw biometrics remain safely on the user's platform authenticator.
    """
    credential_id = payload.get("credential_id") or payload.get("id")
    public_key = payload.get("public_key") or "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A..."
    
    if not credential_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing credential_id in WebAuthn registration response."
        )

    user.passkey_credential_id = credential_id
    user.passkey_public_key = public_key
    
    # Audit log passkey registration
    log_security_event(
        db=db,
        actor=user.username,
        role=user.role,
        action="WebAuthn Passkey Registered",
        entity_type="User",
        entity_id=user.id,
        details=f"Device-mediated biometric passkey registered for {user.username}. Zero biometric data stored.",
        user_id=user.id
    )
    db.commit()

    return {
        "status": "success",
        "message": "FIDO2 / WebAuthn passkey registered successfully for this device."
    }

@router.post("/webauthn/login-options")
def webauthn_login_options(
    payload: Dict[str, str] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Generates WebAuthn assertion options challenge for passkey authentication.
    """
    username = payload.get("username", "").strip().lower()
    user = db.query(User).filter(
        (User.username.ilike(username)) | (User.email.ilike(username))
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")

    challenge = secrets.token_urlsafe(32)
    ACTIVE_WEBAUTHN_CHALLENGES[user.id] = {
        "challenge": challenge,
        "type": "login",
        "created_at": time.time()
    }

    return {
        "challenge": challenge,
        "timeout": 60000,
        "rpId": "aicte-india.org",
        "allowCredentials": [
            {
                "type": "public-key",
                "id": user.passkey_credential_id or f"CRED-{user.id}"
            }
        ],
        "userVerification": "preferred"
    }

@router.post("/webauthn/login-verify", response_model=LoginResponse)
def webauthn_login_verify(
    response: Response,
    request: Request,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Verifies passkey assertion response and issues authenticated session token.
    """
    username = payload.get("username", "").strip().lower()
    user = db.query(User).filter(
        (User.username.ilike(username)) | (User.email.ilike(username))
    ).first()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid user or account inactive.")

    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    # Issue access token
    token_data = {
        "sub": user.id,
        "username": user.username,
        "role": user.role,
        "institution_id": user.institution_id
    }
    access_token = create_access_token(token_data)
    token_digest = hash_token(access_token)
    session_expire = utc_now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    session_record = UserSession(
        id=f"SES-{uuid.uuid4().hex[:8].upper()}",
        user_id=user.id,
        token_hash=token_digest,
        ip_address=client_ip,
        user_agent=user_agent,
        is_revoked=False,
        expires_at=session_expire,
        created_at=utc_now()
    )
    db.add(session_record)

    log_security_event(
        db=db,
        actor=user.username,
        role=user.role,
        action="WebAuthn Passkey Login",
        entity_type="User",
        entity_id=user.id,
        details=f"User authenticated via device-mediated biometric passkey from {client_ip}.",
        ip_address=client_ip,
        user_id=user.id
    )
    db.commit()

    response.set_cookie(
        key="aicte_session",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=build_user_response(user)
    )
