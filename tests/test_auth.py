"""
Authentication, Password Verification, Session Revocation & Throttling Tests
"""
import pytest
from backend.models import User, UserSession, LoginHistory
from backend.auth import hash_password

def test_login_success(client):
    response = client.post("/api/auth/login", json={
        "username": "superadmin",
        "password": "AicteOne@2026!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "superadmin"
    assert data["user"]["role"] == "SUPER_ADMIN"
    assert "*" in data["user"]["permissions"]
    # Check session cookie set
    assert "aicte_session" in response.cookies

def test_login_failure_invalid_credentials(client):
    response = client.post("/api/auth/login", json={
        "username": "superadmin",
        "password": "WrongPassword123!"
    })
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]

def test_login_failure_nonexistent_user(client):
    response = client.post("/api/auth/login", json={
        "username": "unknown.user.999",
        "password": "SomePassword123!"
    })
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]

def test_account_lockout_protection(client, db_session):
    # Create isolated user for lockout test
    test_user = User(
        id="USR-LOCKOUT-TEST",
        username="lockout.test",
        email="lockout.test@aicte-india.org",
        full_name="Lockout Test User",
        password_hash=hash_password("AicteOne@2026!"),
        role="STUDENT_COMPLAINANT",
        is_active=True,
        failed_login_attempts=0
    )
    db_session.add(test_user)
    db_session.commit()

    # Fail 5 times
    for i in range(5):
        resp = client.post("/api/auth/login", json={
            "username": "lockout.test",
            "password": "WrongPassword!"
        })
        assert resp.status_code == 401

    # 6th attempt should be locked out
    resp_locked = client.post("/api/auth/login", json={
        "username": "lockout.test",
        "password": "WrongPassword!"
    })
    assert resp_locked.status_code == 423
    assert "locked" in resp_locked.json()["detail"].lower()

def test_authenticated_profile_endpoint(client):
    # 1. Login
    login_resp = client.post("/api/auth/login", json={
        "username": "compliance.officer",
        "password": "AicteOne@2026!"
    })
    token = login_resp.json()["access_token"]

    # 2. Call /api/auth/me with Bearer token
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["username"] == "compliance.officer"
    assert me_data["role"] == "POLICY_COMPLIANCE_OFFICER"
    assert "compliance:view_all" in me_data["permissions"]

def test_unauthenticated_request_rejected(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401
    assert "Authentication required" in resp.json()["detail"]

def test_spoofed_headers_rejected(client):
    # Calling protected endpoint with spoofed X-Role/X-Actor headers but no token
    resp = client.get("/api/auth/me", headers={
        "X-Role": "SUPER_ADMIN",
        "X-Actor": "admin@aicte-india.org"
    })
    assert resp.status_code == 401

def test_logout_session_invalidation(client):
    # 1. Login
    login_resp = client.post("/api/auth/login", json={
        "username": "security.officer",
        "password": "AicteOne@2026!"
    })
    token = login_resp.json()["access_token"]

    # 2. Verify token works
    valid_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert valid_resp.status_code == 200

    # 3. Call Logout
    logout_resp = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_resp.status_code == 200
    assert "Session invalidated" in logout_resp.json()["message"]

    # 4. Verify token is now rejected
    after_logout_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert after_logout_resp.status_code == 401
    assert "revoked" in after_logout_resp.json()["detail"].lower()

def test_password_recovery_flow(client, db_session):
    # 1. Request password reset
    req_resp = client.post("/api/auth/password-reset-request", json={
        "account": "student.aarav"
    })
    assert req_resp.status_code == 200
    data = req_resp.json()
    token = data["token"]
    assert token is not None

    # 2. Confirm password reset with new password
    confirm_resp = client.post("/api/auth/password-reset-confirm", json={
        "token": token,
        "new_password": "NewSecurePassword@2026!"
    })
    assert confirm_resp.status_code == 200
    assert "Password updated successfully" in confirm_resp.json()["message"]

    # 3. Verify old password no longer works
    old_login = client.post("/api/auth/login", json={
        "username": "student.aarav",
        "password": "AicteOne@2026!"
    })
    assert old_login.status_code == 401

    # 4. Verify new password works
    new_login = client.post("/api/auth/login", json={
        "username": "student.aarav",
        "password": "NewSecurePassword@2026!"
    })
    assert new_login.status_code == 200

    # 5. Verify single-use token cannot be replayed
    replay_resp = client.post("/api/auth/password-reset-confirm", json={
        "token": token,
        "new_password": "AnotherNewPassword@2026!"
    })
    assert replay_resp.status_code == 400
    assert "Invalid or previously utilized" in replay_resp.json()["detail"]

def test_privileged_mfa_verification(client, db_session):
    # Enable MFA for a test user
    mfa_user = User(
        id="USR-MFA-TEST",
        username="mfa.admin",
        email="mfa.admin@aicte-india.org",
        full_name="MFA Admin",
        password_hash=hash_password("AicteOne@2026!"),
        role="SUPER_ADMIN",
        is_active=True,
        is_mfa_enabled=True,
        mfa_secret="987654"
    )
    db_session.add(mfa_user)
    db_session.commit()

    # Login without MFA code -> 403 Forbidden
    no_mfa_resp = client.post("/api/auth/login", json={
        "username": "mfa.admin",
        "password": "AicteOne@2026!"
    })
    assert no_mfa_resp.status_code == 403
    assert "MFA code required" in no_mfa_resp.json()["detail"]

    # Login with wrong MFA code -> 401 Unauthorized
    bad_mfa_resp = client.post("/api/auth/login", json={
        "username": "mfa.admin",
        "password": "AicteOne@2026!",
        "mfa_code": "000000"
    })
    assert bad_mfa_resp.status_code == 401
    assert "Invalid MFA verification code" in bad_mfa_resp.json()["detail"]

    # Login with valid MFA code -> 200 OK
    good_mfa_resp = client.post("/api/auth/login", json={
        "username": "mfa.admin",
        "password": "AicteOne@2026!",
        "mfa_code": "987654"
    })
    assert good_mfa_resp.status_code == 200
    assert "access_token" in good_mfa_resp.json()
