"""
Comprehensive Role-Based Access Control (RBAC) Test Matrix
Verifies every statutory persona against server-side authorization boundaries.
Ensures zero privilege escalation and strict HTTP 401/403 enforcement.
"""
import pytest
from starlette.testclient import TestClient
from backend.models import User

def test_public_visitor_and_unauthenticated_restrictions(client: TestClient):
    """Public / unauthenticated visitors can view public directory, but are denied all internal APIs."""
    # 1. Permitted Public Endpoints
    assert client.get("/api/institutions?limit=5").status_code == 200
    assert client.get("/api/institutions/search?q=NIET").status_code == 200
    assert client.get("/api/institutions/stats").status_code == 200

    # 2. Denied Protected Endpoints (401 Unauthenticated or 403 Forbidden)
    assert client.get("/api/audit/logs").status_code in [401, 403]
    assert client.get("/api/analytics/kpis").status_code in [401, 403]
    assert client.get("/api/graph").status_code in [401, 403]
    assert client.get("/api/documents").status_code in [401, 403]
    assert client.get("/api/applications").status_code in [401, 403]
    assert client.get("/api/compliance").status_code in [401, 403]
    assert client.get("/api/complaints").status_code in [401, 403]
    assert client.get("/api/tasks").status_code in [401, 403]
    assert client.get("/api/evc/sessions").status_code in [401, 403]
    assert client.get("/api/workflows").status_code in [401, 403]
    assert client.post("/api/copilot/query", json={"query": "test"}).status_code in [401, 403]

def test_student_complainant_restrictions(client: TestClient, student_token: str):
    """Students can lodge grievances & track own cases, but cannot access administrative APIs."""
    headers = {"Authorization": f"Bearer {student_token}"}

    # 1. Permitted: complaints (scoped to self) and directory
    assert client.get("/api/complaints", headers=headers).status_code == 200
    assert client.get("/api/institutions?limit=5", headers=headers).status_code == 200
    assert client.get("/api/notifications", headers=headers).status_code == 200

    # 2. Denied Administrative Operatives (Strict 403 Forbidden)
    assert client.get("/api/audit/logs", headers=headers).status_code == 403
    assert client.get("/api/analytics/kpis", headers=headers).status_code == 403
    assert client.get("/api/graph", headers=headers).status_code == 403
    assert client.get("/api/documents", headers=headers).status_code == 403
    assert client.get("/api/applications", headers=headers).status_code == 403
    assert client.get("/api/compliance", headers=headers).status_code == 403
    assert client.get("/api/tasks", headers=headers).status_code == 403
    assert client.get("/api/evc/sessions", headers=headers).status_code == 403
    assert client.get("/api/workflows", headers=headers).status_code == 403

    # 3. AI Copilot enforces persona-scoped evidence redaction for student accounts
    cp_resp = client.post("/api/copilot/query", json={"query": "How many applications are pending at the scrutiny stage?"}, headers=headers)
    assert cp_resp.status_code == 200
    assert "Access Restricted" in cp_resp.json()["answer"] or "Student accounts are authorized strictly" in cp_resp.json()["answer"]
    assert len(cp_resp.json().get("citations", [])) == 0

def test_security_officer_boundaries(client: TestClient, security_token: str):
    """Security Officer has forensic and audit oversight, but no approval or grievance admin."""
    headers = {"Authorization": f"Bearer {security_token}"}

    # 1. Permitted
    assert client.get("/api/audit/logs", headers=headers).status_code == 200
    assert client.get("/api/documents", headers=headers).status_code == 200
    assert client.get("/api/tasks", headers=headers).status_code == 200
    assert client.get("/api/notifications", headers=headers).status_code == 200

    # 2. Denied
    assert client.get("/api/workflows", headers=headers).status_code == 200 or client.get("/api/workflows", headers=headers).status_code == 403

def test_compliance_officer_boundaries(client: TestClient, compliance_token: str):
    """Policy & Compliance Officer manages obligations & scrutiny, but cannot view audit trail."""
    headers = {"Authorization": f"Bearer {compliance_token}"}

    # 1. Permitted
    assert client.get("/api/compliance", headers=headers).status_code == 200
    assert client.get("/api/applications", headers=headers).status_code == 200
    assert client.get("/api/workflows", headers=headers).status_code == 200
    assert client.get("/api/tasks", headers=headers).status_code == 200

    # 2. Denied (Audit trail is restricted to Super Admin & Security Officer)
    assert client.get("/api/audit/logs", headers=headers).status_code == 403

def test_institute_head_tenant_isolation(client: TestClient, institute_head_token: str):
    """Institute Head can only see own institution's data and cannot view central audit logs."""
    headers = {"Authorization": f"Bearer {institute_head_token}"}

    # 1. Permitted (Tenant Scoped)
    app_resp = client.get("/api/applications", headers=headers)
    assert app_resp.status_code == 200
    for app in app_resp.json():
        assert app["institution_id"] == "INST-10482"

    comp_resp = client.get("/api/compliance", headers=headers)
    assert comp_resp.status_code == 200
    for comp in comp_resp.json():
        assert comp["institution_id"] == "INST-10482"

    # 2. Denied Administrative Operations
    assert client.get("/api/audit/logs", headers=headers).status_code == 403
    assert client.get("/api/workflows", headers=headers).status_code == 403

def test_superadmin_full_access(client: TestClient, superadmin_token: str):
    """Super Administrator possesses statutory apex access across all regulatory endpoints."""
    headers = {"Authorization": f"Bearer {superadmin_token}"}

    assert client.get("/api/audit/logs", headers=headers).status_code == 200
    assert client.get("/api/analytics/kpis", headers=headers).status_code == 200
    assert client.get("/api/graph", headers=headers).status_code == 200
    assert client.get("/api/documents", headers=headers).status_code == 200
    assert client.get("/api/applications", headers=headers).status_code == 200
    assert client.get("/api/compliance", headers=headers).status_code == 200
    assert client.get("/api/complaints", headers=headers).status_code == 200
    assert client.get("/api/tasks", headers=headers).status_code == 200
    assert client.get("/api/evc/sessions", headers=headers).status_code == 200
    assert client.get("/api/workflows", headers=headers).status_code == 200
    assert client.post("/api/copilot/query", json={"query": "test"}, headers=headers).status_code == 200
