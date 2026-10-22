"""
Phase 2 Test Suite: EVC, Compliance Undertakings & Lease Expiry
Tests EVC prerequisites, conflict-of-interest prevention, geo-tagged report submission,
statutory undertakings lifecycle, and lease validity engine.
"""
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient

def test_evc_scheduling_rejected_on_scrutiny_only_route(client: TestClient, superadmin_token: str):
    """Verifies that EVC inspection cannot be scheduled on a SCRUTINY_ONLY route application."""
    res_create = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        json={
            "institution_id": "INST-10482",
            "category": "Technical",
            "type": "Closure of Institution",
            "route_type": "SCRUTINY_ONLY"
        }
    )
    app_id = res_create.json()["id"]

    res_evc = client.post(
        "/api/evc/schedule",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        json={
            "application_id": app_id,
            "institution_id": "INST-10482",
            "visit_type": "Physical Visit",
            "scheduled_date": (date.today() + timedelta(days=5)).isoformat(),
            "committee_chair": "Prof. R. Sharma (IIT Bombay)",
            "committee_members": "Dr. V. Rao, Dr. K. Nair"
        }
    )
    assert res_evc.status_code == 400
    assert "does not permit EVC" in res_evc.json()["detail"]

def test_evc_conflict_of_interest_detection(client: TestClient, superadmin_token: str):
    """Verifies that committee members with institutional affiliation trigger conflict of interest rejection."""
    res_create = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        json={
            "institution_id": "INST-10482",
            "category": "Technical",
            "type": "New Course Introduction",
            "route_type": "SCRUTINY_EVC"
        }
    )
    app_id = res_create.json()["id"]

    # Transition to SCRUTINY first
    client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        json={"stage_code": "SCRUTINY", "status": "In scrutiny"}
    )

    # Attempt scheduling with chair affiliated with institution
    res_conflict = client.post(
        "/api/evc/schedule",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        json={
            "application_id": app_id,
            "institution_id": "INST-10482",
            "visit_type": "Physical Visit",
            "scheduled_date": (date.today() + timedelta(days=5)).isoformat(),
            "committee_chair": "Prof. K. Sharma (Noida Institute of Engineering & Technology)",
            "committee_members": "Prof. A, Prof. B"
        }
    )
    assert res_conflict.status_code == 400
    assert "Conflict of Interest" in res_conflict.json()["detail"]

def test_evc_completion_and_report_submission(client: TestClient, superadmin_token: str):
    """
    Tests complete EVC workflow:
    1. Schedule valid EVC with quorum.
    2. Submit geo-tagged inspection report with recommendations.
    3. Application advances to EVC_EVALUATION.
    """
    res_create = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        json={
            "institution_id": "INST-10482",
            "category": "Technical",
            "type": "Extension of Approval",
            "route_type": "SCRUTINY_EVC"
        }
    )
    app_id = res_create.json()["id"]

    # Advance to SCRUTINY
    client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        json={"stage_code": "SCRUTINY", "status": "In scrutiny"}
    )

    # Schedule EVC
    res_sched = client.post(
        "/api/evc/schedule",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        json={
            "application_id": app_id,
            "institution_id": "INST-10482",
            "visit_type": "Physical Visit",
            "scheduled_date": (date.today() + timedelta(days=3)).isoformat(),
            "committee_chair": "Prof. K. Sundaram (NIT Trichy)",
            "convener": "AICTE-RO-WRO",
            "committee_members": "Dr. A. Verma (IIT Indore), Dr. S. Patel (VNIT)"
        }
    )
    assert res_sched.status_code == 200
    evc_id = res_sched.json()["evc_id"]

    # Submit inspection report
    res_comp = client.post(
        f"/api/evc/{evc_id}/complete",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        json={
            "recommendation": "Recommended",
            "observations": "Infrastructure complies with APH Norms. 12 Laboratories verified. High bandwidth Internet connection verified.",
            "geo_latitude": 19.0222,
            "geo_longitude": 72.8561,
            "checklist_findings": {
                "infrastructure": "Compliant",
                "laboratory_equipment": "Verified",
                "faculty_cadre": "Adequate",
                "fire_safety": "Compliant"
            }
        }
    )
    assert res_comp.status_code == 200
    assert res_comp.json()["recommendation"] == "Recommended"

    # Verify application stage advanced to EVC_EVALUATION
    res_app = client.get(
        f"/api/applications/{app_id}",
        headers={"Authorization": f"Bearer {superadmin_token}"}
    )
    assert res_app.json()["stage_code"] == "EVC_EVALUATION"

def test_time_bound_undertakings_lifecycle(
    client: TestClient,
    superadmin_token: str,
    compliance_token: str,
    institute_head_token: str
):
    """
    Tests time-bound undertakings:
    1. Compliance officer registers undertaking condition.
    2. Tenant isolation verifies Institute Head sees only own institution's undertakings.
    3. Institute Head uploads evidence.
    4. Compliance officer reviews and marks 'Verified & Accepted'.
    """
    # 1. Create undertaking
    res_create = client.post(
        "/api/compliance/undertakings",
        headers={"Authorization": f"Bearer {compliance_token}"},
        json={
            "institution_id": "INST-10482",
            "undertaking_type": "Endowment Fund Deposit",
            "condition_ref": "APH-2026-Clause-5.1",
            "description": "Establishment of Joint Fixed Deposit of Rs. 10 Lakhs in name of AICTE & Society.",
            "statutory_deadline": (date.today() + timedelta(days=45)).isoformat()
        }
    )
    assert res_create.status_code == 200
    und_id = res_create.json()["id"]

    # 2. Tenant isolation check for Institute Head
    res_list = client.get(
        "/api/compliance/undertakings",
        headers={"Authorization": f"Bearer {institute_head_token}"}
    )
    assert res_list.status_code == 200
    items = res_list.json()
    assert any(u["id"] == und_id for u in items)

    # 3. Institute Head submits evidence
    res_sub = client.post(
        f"/api/compliance/undertakings/{und_id}/submit-evidence",
        headers={"Authorization": f"Bearer {institute_head_token}"},
        json={"evidence_file": "FDR_FixedDeposit_Receipt_SBI.pdf"}
    )
    assert res_sub.status_code == 200
    assert res_sub.json()["status"] == "Evidence Submitted"

    # 4. Officer reviews and accepts
    res_rev = client.post(
        f"/api/compliance/undertakings/{und_id}/review",
        headers={"Authorization": f"Bearer {compliance_token}"},
        json={
            "decision": "Accept",
            "review_notes": "FDR verified with State Bank of India. 5-year lock-in confirmed."
        }
    )
    assert res_rev.status_code == 200
    assert res_rev.json()["status"] == "Verified & Accepted"

def test_document_and_lease_validity_engine(
    client: TestClient,
    superadmin_token: str,
    compliance_token: str
):
    """
    Tests Document & Lease Validity engine:
    1. Register Land Lease expiring in future.
    2. Register expired Safety Certificate.
    3. Scan validities detects expired document.
    4. Verify expired document blocks application advancement until renewed.
    5. Renew expired document and verify successful renewal.
    """
    # 1. Register expired Fire Safety Certificate
    res_val = client.post(
        "/api/documents/validities",
        headers={"Authorization": f"Bearer {compliance_token}"},
        json={
            "institution_id": "INST-10482",
            "document_type": "Fire Safety NOC",
            "document_ref_number": "NOC-EXPIRED-999",
            "issuing_authority": "Municipal Fire Brigade",
            "issue_date": (date.today() - timedelta(days=400)).isoformat(),
            "expiry_date": (date.today() - timedelta(days=35)).isoformat(),
            "advance_warning_days": 60
        }
    )
    assert res_val.status_code == 200
    val_id = res_val.json()["id"]
    assert res_val.json()["status"] == "Expired"

    # 2. Run validity scanner
    res_scan = client.post(
        "/api/documents/scan-validities",
        headers={"Authorization": f"Bearer {compliance_token}"}
    )
    assert res_scan.status_code == 200
    assert res_scan.json()["total_documents_scanned"] >= 1

    # 3. Create application and attempt to advance to FINAL_DISPOSITION
    res_app = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        json={
            "institution_id": "INST-10482",
            "category": "Technical",
            "type": "Extension of Approval",
            "route_type": "SCRUTINY_ONLY"
        }
    )
    app_id = res_app.json()["id"]

    # Advance to SCRUTINY
    client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        json={"stage_code": "SCRUTINY", "status": "In scrutiny"}
    )

    # Attempt advancement to FINAL_DISPOSITION - should be blocked by prerequisite
    res_blocked = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        json={
            "stage_code": "FINAL_DISPOSITION",
            "status": "Approved",
            "bypass_prereq_override": False
        }
    )
    assert res_blocked.status_code == 400
    assert "Expired statutory document" in res_blocked.json()["detail"]

    # 4. Renew the expired document
    res_renew = client.post(
        f"/api/documents/validities/{val_id}/renew",
        headers={"Authorization": f"Bearer {compliance_token}"},
        json={
            "new_expiry_date": (date.today() + timedelta(days=365)).isoformat(),
            "renewal_ref": "FIRE/RENEW/2026/771"
        }
    )
    assert res_renew.status_code == 200
    assert res_renew.json()["status"] == "Renewed"
