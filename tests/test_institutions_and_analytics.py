"""
Phase 3 Test Suite: Official Institutional Data, Search & Matching,
Approval Verification Gateway, 15 KPIs, Graphs A-L, and Import Pipeline.
"""
import pytest
from datetime import date
from backend.models import Institution, Application, Complaint, User, AuditLog, InstitutionCorrectionRequest

def get_auth_token(client, username="superadmin", password="AicteOne@2026!"):
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, f"Login failed for {username}: {resp.text}"
    return resp.json()["access_token"]

# ---------------------------------------------------------------------------
# 1. Institution Advanced Search & Acronym Matching Engine
# ---------------------------------------------------------------------------
def test_institution_exact_permanent_id_search(client, db_session):
    resp = client.get("/api/institutions/search/advanced?q=1-10482931")
    assert resp.status_code == 200
    data = resp.json()
    assert data["match_type"] == "EXACT_IDENTIFIER"
    assert data["confirmed_match"] is not None
    assert data["confirmed_match"]["permanent_id"] == "1-10482931"
    assert "Noida Institute" in data["confirmed_match"]["name"]

def test_institution_acronym_expansion_search(client, db_session):
    # 'NIET' should expand to Noida Institute of Engineering & Technology
    resp = client.get("/api/institutions/search/advanced?q=NIET")
    assert resp.status_code == 200
    data = resp.json()
    all_matches = ([data["confirmed_match"]] if data.get("confirmed_match") else []) + data.get("possible_matches", [])
    assert len(all_matches) >= 1
    assert any("Noida Institute of Engineering" in m["name"] for m in all_matches)

def test_institution_search_with_state_filter(client, db_session):
    resp = client.get("/api/institutions/search/advanced?q=Engineering&state=Uttar Pradesh")
    assert resp.status_code == 200
    data = resp.json()
    all_matches = ([data["confirmed_match"]] if data.get("confirmed_match") else []) + data.get("possible_matches", [])
    assert len(all_matches) >= 1
    for inst in all_matches:
        assert inst["state"] == "Uttar Pradesh"

def test_institution_search_no_results(client):
    resp = client.get("/api/institutions/search/advanced?q=NonExistentUniversityXYZ99999")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["match_type"] == "NONE"

# ---------------------------------------------------------------------------
# 2. Official Approval Verification Gateway
# ---------------------------------------------------------------------------
def test_verify_approved_institution(client, db_session):
    resp = client.get("/api/institutions/verify?q=1-10482931")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "Approved"
    assert data["institution"] is not None
    assert data["institution"]["id"] == "INST-10482"
    assert data["is_found"] is True
    assert "authoritative_link" in data
    assert "data_freshness" in data

def test_verify_institution_by_id_endpoint(client, db_session):
    resp = client.get("/api/institutions/INST-10482/approval-verification")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["Approved", "Approval Expired", "Pending", "Needs Verification"]
    assert data["institution"]["permanent_id"] == "1-10482931"

def test_verify_nonexistent_institution_returns_needs_verification(client):
    resp = client.get("/api/institutions/verify?q=NonExistentCollege404")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "Needs Verification"
    assert data["is_found"] is False
    assert "authoritative_link" in data

# ---------------------------------------------------------------------------
# 3. Discrepancy Reporting & Correction Request Review Workflow
# ---------------------------------------------------------------------------
def test_discrepancy_and_correction_workflow(client, db_session):
    new_website = "https://www.niet-domain-update.edu.in"
    inst = db_session.query(Institution).filter(Institution.id == "INST-10482").first()
    inst.website = "https://www.niet.co.in"
    db_session.commit()

    # 1. Public or College submits a correction request
    post_resp = client.post(
        "/api/institutions/INST-10482/correction-request",
        json={
            "reported_by": "Registrar Dr. A. Sharma",
            "contact_email": "registrar@niet.co.in",
            "field_name": "website",
            "proposed_value": new_website,
            "evidence_file": "Registrar_Affidavit_2026.pdf",
            "rationale": "Official domain updated to .edu.in"
        }
    )
    assert post_resp.status_code == 200
    corr = post_resp.json()
    assert corr["status"] == "Pending Review"
    req_id = corr["id"]

    # Verify production record is NOT immediately changed before approval
    inst_before = db_session.query(Institution).filter(Institution.id == "INST-10482").first()
    assert inst_before.website != new_website

    # 2. Officer views correction requests
    token = get_auth_token(client, "superadmin")
    headers = {"Authorization": f"Bearer {token}"}
    list_resp = client.get("/api/institutions/INST-10482/correction-requests", headers=headers)
    assert list_resp.status_code == 200
    assert any(c["id"] == req_id for c in list_resp.json())

    # 3. Officer approves correction request
    review_resp = client.post(
        f"/api/institutions/correction-requests/{req_id}/review",
        json={
            "decision": "Approve",
            "review_notes": "Domain verified against DNS records and AICTE letterhead"
        },
        headers=headers
    )
    assert review_resp.status_code == 200
    assert review_resp.json()["status"] == "Approved"

    # Verify production record is NOW updated
    db_session.expire_all()
    inst_after = db_session.query(Institution).filter(Institution.id == "INST-10482").first()
    assert inst_after.website == new_website

# ---------------------------------------------------------------------------
# 4. Data Quality Audit Endpoint
# ---------------------------------------------------------------------------
def test_data_quality_audit(client, db_session):
    token = get_auth_token(client, "superadmin")
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/institutions/data-quality", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_institutions" in data
    assert "data_quality_score" in data
    assert "flags" in data
    assert "missing_district_count" in data["flags"]

# ---------------------------------------------------------------------------
# 5. Operational Dashboard: 15 Real-Record KPIs
# ---------------------------------------------------------------------------
def test_analytics_15_kpis_endpoint(client, db_session):
    token = get_auth_token(client, "superadmin")
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/analytics/kpis", headers=headers)
    assert resp.status_code == 200
    kpis = resp.json()

    expected_keys = [
        "total_institutions", "verified_institutions", "active_applications",
        "sla_compliance_rate", "scrutiny_completed", "evc_scheduled",
        "evc_completed", "undertakings_active", "undertakings_breached",
        "document_validity_critical", "active_complaints", "ragging_complaints",
        "pgrc_resolved", "avg_processing_days", "escalated_cases"
    ]
    for key in expected_keys:
        assert key in kpis, f"Missing KPI card metric: {key}"
        assert isinstance(kpis[key], (int, float)), f"KPI {key} should be numeric"

# ---------------------------------------------------------------------------
# 6. Operational Dashboard: Graphs A through L
# ---------------------------------------------------------------------------
def test_analytics_graphs_a_through_l(client, db_session):
    token = get_auth_token(client, "superadmin")
    headers = {"Authorization": f"Bearer {token}"}

    # Graph A: Workflow Stages
    resp_a = client.get("/api/analytics/graphs/workflow-stages", headers=headers)
    assert resp_a.status_code == 200
    data_a = resp_a.json()
    assert "segments" in data_a and "total" in data_a

    # Graph B: Complaints by Category
    resp_b = client.get("/api/analytics/graphs/complaints-by-category", headers=headers)
    assert resp_b.status_code == 200
    data_b = resp_b.json()
    assert "categories" in data_b and "total" in data_b

    # Graph C: Application Trends
    resp_c = client.get("/api/analytics/graphs/application-trends", headers=headers)
    assert resp_c.status_code == 200
    data_c = resp_c.json()
    assert "series" in data_c

    # Graph D: Pendency Ageing
    resp_d = client.get("/api/analytics/graphs/pendency-ageing", headers=headers)
    assert resp_d.status_code == 200
    data_d = resp_d.json()
    assert "buckets" in data_d and "total_active" in data_d

    # Graph E: Regional Distribution
    resp_e = client.get("/api/analytics/graphs/regional-distribution", headers=headers)
    assert resp_e.status_code == 200
    data_e = resp_e.json()
    assert "top_states" in data_e

    # Graph F: Application Pipeline Funnel
    resp_f = client.get("/api/analytics/graphs/application-funnel", headers=headers)
    assert resp_f.status_code == 200
    data_f = resp_f.json()
    assert "funnel" in data_f and "total_applications" in data_f

    # Graph G: EVC Visits Status
    resp_g = client.get("/api/analytics/graphs/evc-status", headers=headers)
    assert resp_g.status_code == 200
    data_g = resp_g.json()
    assert "status_breakdown" in data_g and "total_evc_sessions" in data_g

    # Graph H: Institutional Compliance Index
    resp_h = client.get("/api/analytics/graphs/compliance-index", headers=headers)
    assert resp_h.status_code == 200
    data_h = resp_h.json()
    assert "compliance_index_percentage" in data_h

    # Graph I: Document Validity Health
    resp_i = client.get("/api/analytics/graphs/document-validity", headers=headers)
    assert resp_i.status_code == 200
    data_i = resp_i.json()
    assert "breakdown" in data_i and "total_tracked_documents" in data_i

    # Graph J: Officer Workload & Caseload
    resp_j = client.get("/api/analytics/graphs/officer-workload", headers=headers)
    assert resp_j.status_code == 200
    data_j = resp_j.json()
    assert "officers" in data_j

    # Graph K: Bottleneck Dwell Time Heatmap
    resp_k = client.get("/api/analytics/graphs/bottleneck-heatmap", headers=headers)
    assert resp_k.status_code == 200
    data_k = resp_k.json()
    assert "heatmap" in data_k

    # Graph L: Anomaly Review Queue
    resp_l = client.get("/api/analytics/graphs/anomaly-review-queue", headers=headers)
    assert resp_l.status_code == 200
    data_l = resp_l.json()
    assert "flagged_documents_count" in data_l and "items" in data_l

# ---------------------------------------------------------------------------
# 7. Authoritative Dataset Batch Import Pipeline
# ---------------------------------------------------------------------------
def test_import_pipeline_preview_and_confirm(client, db_session):
    token = get_auth_token(client, "superadmin")
    headers = {"Authorization": f"Bearer {token}"}

    # Step 1: Preview import using official dataset (preview limit 20)
    preview_resp = client.post(
        "/api/institutions/import/preview",
        json={"sample_limit": 20},
        headers=headers
    )
    assert preview_resp.status_code == 200
    preview = preview_resp.json()
    assert preview["total_records_in_source"] > 0
    assert len(preview["preview_items"]) > 0

    # Step 2: Confirm import with small batch limit
    confirm_resp = client.post(
        "/api/institutions/import/confirm",
        json={"batch_limit": 20},
        headers=headers
    )
    assert confirm_resp.status_code == 200
    confirm = confirm_resp.json()
    assert confirm["status"] in ["Success", "Partial", "SUCCESS"]
    assert "created" in confirm
    assert confirm["total_processed"] > 0

# ---------------------------------------------------------------------------
# 8. Administrative CSV Data Export & Audit Logging
# ---------------------------------------------------------------------------
def test_export_institutions_csv_security_and_format(client, db_session):
    # Unauthenticated rejected
    unauth_resp = client.get("/api/analytics/export/institutions-csv")
    assert unauth_resp.status_code == 401

    # Superadmin permitted
    token = get_auth_token(client, "superadmin")
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/analytics/export/institutions-csv", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    content = resp.text
    assert "id,permanent_id,aicte_id,name,state,district" in content
    assert "Noida Institute of Engineering" in content
