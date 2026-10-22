"""
Role-Based Access Control (RBAC), Privilege Escalation Defense & Tenant Isolation Tests
Covers all 8 statutory persona categories and strict multi-institution data isolation.
"""
import pytest
from backend.models import Institution, Application, Complaint, ComplianceObligation, Document

def get_token_for(client, username, password="AicteOne@2026!"):
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    if resp.status_code != 200:
        alt_pwd = "AicteOne@2026!" if password != "AicteOne@2026!" else "NewSecurePassword@2026!"
        alt_resp = client.post("/api/auth/login", json={"username": username, "password": alt_pwd})
        if alt_resp.status_code == 200:
            return alt_resp.json()["access_token"]
    assert resp.status_code == 200, f"Login failed for {username}: {resp.text}"
    return resp.json()["access_token"]

# ---------------------------------------------------------------------------
# 1. Public Visitor Capabilities & Restrictions
# ---------------------------------------------------------------------------
def test_public_visitor_can_search_institutions(client):
    # Unauthenticated / Public visitor can query public directory
    resp = client.get("/api/institutions?q=Technology")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data or "items" in data

def test_public_visitor_denied_internal_applications(client):
    resp = client.get("/api/applications")
    assert resp.status_code == 401

def test_public_visitor_denied_audit_logs(client):
    resp = client.get("/api/audit/logs")
    assert resp.status_code == 401

def test_public_visitor_denied_complaint_registry(client):
    resp = client.get("/api/complaints")
    assert resp.status_code == 401

# ---------------------------------------------------------------------------
# 2. Student Complainant Isolation & Whistleblower Protections
# ---------------------------------------------------------------------------
def test_student_can_lodge_and_view_own_complaint_only(client, db_session):
    token = get_token_for(client, "student.aarav", "NewSecurePassword@2026!")

    # Find an institution to file against
    inst = db_session.query(Institution).first()
    assert inst is not None

    # Lodge complaint
    lodge_resp = client.post(
        "/api/complaints",
        json={
            "institution_id": inst.id,
            "bureau": "PGRC",
            "category": "Curriculum and Laboratory Deficiencies",
            "summary": "Laboratories lack modern oscilloscopes and software licenses.",
            "details": "Submitted by student under grievance cell.",
            "channel": "Online Portal"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert lodge_resp.status_code == 200
    case_id = lodge_resp.json()["id"]

    # Student queries complaints -> must see own complaint
    list_resp = client.get("/api/complaints", headers={"Authorization": f"Bearer {token}"})
    assert list_resp.status_code == 200
    complaints = list_resp.json()
    assert any(c["id"] == case_id for c in complaints)

    # All complaints returned must have complainant_id matching student
    for c in complaints:
        db_c = db_session.query(Complaint).filter(Complaint.id == c["id"]).first()
        assert db_c.complainant_id == "USR-STUD-01"

def test_student_cannot_access_internal_officer_dashboards(client):
    token = get_token_for(client, "student.aarav", "NewSecurePassword@2026!")
    headers = {"Authorization": f"Bearer {token}"}

    # Applications list -> 403
    app_resp = client.get("/api/applications", headers=headers)
    assert app_resp.status_code == 403

    # Audit logs -> 403
    audit_resp = client.get("/api/audit/logs", headers=headers)
    assert audit_resp.status_code == 403

    # Tasks queue -> 403
    task_resp = client.get("/api/tasks", headers=headers)
    assert task_resp.status_code == 403

    # Compliance list -> 403
    comp_resp = client.get("/api/compliance", headers=headers)
    assert comp_resp.status_code == 403

# ---------------------------------------------------------------------------
# 3. Institute Head Multi-Tenant Isolation (Anti-IDOR)
# ---------------------------------------------------------------------------
def test_institute_head_can_access_own_institution(client, db_session):
    token = get_token_for(client, "principal.gitm")
    headers = {"Authorization": f"Bearer {token}"}

    # Query own digital twin
    resp = client.get("/api/institutions/INST-10482/twin", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["institution"]["id"] == "INST-10482"
    # Should see own applications
    assert "applications" in data

def test_institute_head_cross_tenant_access_denied(client, db_session):
    token = get_token_for(client, "principal.gitm")
    headers = {"Authorization": f"Bearer {token}"}

    # Ensure a second distinct institution exists
    inst_b = db_session.query(Institution).filter(Institution.id != "INST-10482").first()
    if not inst_b:
        inst_b = Institution(
            id="INST-99999",
            permanent_id="1-99999999",
            name="Other Technical Institute",
            state="Maharashtra",
            district="Pune",
            city="Pune",
            category="Engineering and Technology",
            institution_type="Government"
        )
        db_session.add(inst_b)
        db_session.commit()

    # Attempt to access Institution B's Digital Twin -> 403 Forbidden
    resp = client.get(f"/api/institutions/{inst_b.id}/twin", headers=headers)
    assert resp.status_code == 403
    assert "Cross-institution access forbidden" in resp.json()["detail"]

def test_institute_head_cannot_access_other_institutions_applications(client, db_session):
    token = get_token_for(client, "principal.gitm")
    headers = {"Authorization": f"Bearer {token}"}

    # Query applications list -> must only return own institution's applications
    resp = client.get("/api/applications", headers=headers)
    assert resp.status_code == 200
    apps = resp.json()
    for a in apps:
        assert a["institution_id"] == "INST-10482"

def test_institute_head_cannot_create_institution_or_access_audit(client):
    token = get_token_for(client, "principal.gitm")
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to create institution -> 403 Forbidden
    create_resp = client.post("/api/institutions", json={
        "name": "Malicious New College",
        "permanent_id": "1-MALICIOUS",
        "state": "Delhi",
        "district": "New Delhi",
        "city": "New Delhi",
        "category": "Management",
        "institution_type": "Private"
    }, headers=headers)
    assert create_resp.status_code == 403

    # Attempt to read audit trail -> 403 Forbidden
    audit_resp = client.get("/api/audit/logs", headers=headers)
    assert audit_resp.status_code == 403

# ---------------------------------------------------------------------------
# 4. Anti-Ragging Officer Scoped Oversight
# ---------------------------------------------------------------------------
def test_anti_ragging_officer_ragging_cases(client, db_session):
    token = get_token_for(client, "antiragging.officer")
    headers = {"Authorization": f"Bearer {token}"}

    # Create one ragging and one non-ragging complaint
    c_ragging = Complaint(
        id="CASE-RAG-01",
        institution_id="INST-10482",
        bureau="National Anti-Ragging Cell",
        category="Hostel Ragging and Intimidation",
        summary="Senior students intimidating first-year scholars in hostel block C.",
        ragging_flag=True,
        status="Received"
    )
    c_fee = Complaint(
        id="CASE-FEE-01",
        institution_id="INST-10482",
        bureau="Approval Bureau",
        category="Capitation Fee Demand",
        summary="Excess admission fee demanded.",
        ragging_flag=False,
        status="Received"
    )
    db_session.add(c_ragging)
    db_session.add(c_fee)
    db_session.commit()

    # Query complaints as anti-ragging officer
    resp = client.get("/api/complaints", headers=headers)
    assert resp.status_code == 200
    cases = resp.json()
    case_ids = [c["id"] for c in cases]
    assert "CASE-RAG-01" in case_ids
    # Fee complaint should NOT appear in anti-ragging officer queue
    assert "CASE-FEE-01" not in case_ids

# ---------------------------------------------------------------------------
# 5. Complaint Officer Cross-Bureau Coordination & Disposal
# ---------------------------------------------------------------------------
def test_complaint_officer_can_transfer_and_dispose(client, db_session):
    token = get_token_for(client, "complaint.officer")
    headers = {"Authorization": f"Bearer {token}"}

    comp = db_session.query(Complaint).first()
    assert comp is not None

    # Transfer case to Vigilance
    trans_resp = client.post(
        f"/api/complaints/{comp.id}/transfer",
        json={"new_bureau": "Vigilance Bureau", "reason": "Conflict of interest identified"},
        headers=headers
    )
    assert trans_resp.status_code == 200

    # Dispose case
    disp_resp = client.post(
        f"/api/complaints/{comp.id}/dispose",
        json={"resolution_notes": "Statutory inquiry completed. Rectification directive issued."},
        headers=headers
    )
    assert disp_resp.status_code == 200

# ---------------------------------------------------------------------------
# 6. Policy & Compliance Officer Workflow
# ---------------------------------------------------------------------------
def test_compliance_officer_create_and_review(client, db_session):
    token = get_token_for(client, "compliance.officer")
    headers = {"Authorization": f"Bearer {token}"}

    inst = db_session.query(Institution).first()
    assert inst is not None

    # Create compliance obligation
    create_resp = client.post(
        "/api/compliance",
        json={
            "institution_id": inst.id,
            "title": "Annual Fire Safety NOC Submission",
            "category": "Safety & Infrastructure",
            "due_date": "2026-12-31"
        },
        headers=headers
    )
    assert create_resp.status_code == 200
    comp_id = create_resp.json()["id"]

    # Review compliance obligation
    review_resp = client.post(
        f"/api/compliance/{comp_id}/review",
        json={
            "decision": "Satisfied by evidence",
            "notes": "State Fire Directorate certificate verified and matched with municipality."
        },
        headers=headers
    )
    assert review_resp.status_code == 200

# ---------------------------------------------------------------------------
# 7. Super Administrator Complete Statutory Oversight
# ---------------------------------------------------------------------------
def test_superadmin_full_access(client):
    token = get_token_for(client, "superadmin")
    headers = {"Authorization": f"Bearer {token}"}

    # Audit Logs
    audit_resp = client.get("/api/audit/logs", headers=headers)
    assert audit_resp.status_code == 200

    # Audit Export CSV
    export_resp = client.get("/api/audit/export-csv", headers=headers)
    assert export_resp.status_code == 200
    assert "text/csv" in export_resp.headers["content-type"]

    # Applications
    app_resp = client.get("/api/applications", headers=headers)
    assert app_resp.status_code == 200
