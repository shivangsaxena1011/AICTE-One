"""
Database Normalization, Security Headers, Constraints & Audit Trail Tests
"""
import pytest
from sqlalchemy.exc import IntegrityError
from backend.models import User, Institution, AuditLog
from backend.auth import hash_password, verify_password

def test_passwords_are_hashed_never_plaintext(db_session):
    users = db_session.query(User).all()
    assert len(users) >= 8
    for u in users:
        # Passwords must start with bcrypt identifier $2a$ or $2b$
        assert u.password_hash.startswith("$2b$") or u.password_hash.startswith("$2a$")
        # Ensure password hash is not the plaintext password
        assert u.password_hash != "AicteOne@2026!"
        # Verify that bcrypt can verify it
        assert verify_password("AicteOne@2026!", u.password_hash) or verify_password("NewSecurePassword@2026!", u.password_hash)

def test_user_unique_constraints(db_session):
    # Duplicate username attempt
    dup_user = User(
        id="USR-DUP-01",
        username="superadmin",  # Already exists
        email="unique.email@aicte-india.org",
        full_name="Duplicate Admin",
        password_hash=hash_password("AicteOne@2026!"),
        role="SUPER_ADMIN"
    )
    db_session.add(dup_user)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_institution_unique_permanent_id(db_session):
    inst1 = db_session.query(Institution).first()
    assert inst1 is not None

    dup_inst = Institution(
        id="INST-DUP-99",
        name="Copycat College",
        permanent_id=inst1.permanent_id,  # Duplicate
        state="Delhi",
        district="Delhi",
        city="Delhi",
        category="Engineering",
        institution_type="Private"
    )
    db_session.add(dup_inst)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_security_headers_present(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    headers = resp.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert "max-age=" in headers.get("Strict-Transport-Security", "")
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

def test_audit_trail_recorded_on_sensitive_action(client, db_session):
    # Perform login which logs security event
    resp = client.post("/api/auth/login", json={
        "username": "superadmin",
        "password": "AicteOne@2026!"
    })
    assert resp.status_code == 200

    # Query audit logs in database
    audit = db_session.query(AuditLog).filter(
        AuditLog.action == "User Login Success",
        AuditLog.actor == "superadmin"
    ).first()
    assert audit is not None
    assert audit.role == "SUPER_ADMIN"

def test_system_health_check(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
