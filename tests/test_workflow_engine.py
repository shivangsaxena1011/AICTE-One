"""
Phase 2 Test Suite: Configurable Approval Workflow Engine
Tests statutory APH routes, state transitions, prerequisites enforcement,
idempotency controls, deficiency returns, and resubmissions.
"""
import pytest
from fastapi.testclient import TestClient

def test_list_and_get_workflow_definitions(client: TestClient, superadmin_token: str):
    """Verifies that statutory APH workflow definitions are seeded and queryable."""
    res = client.get(
        "/api/workflows",
        headers={"Authorization": f"Bearer {superadmin_token}"}
    )
    assert res.status_code == 200
    wfs = res.json()
    assert len(wfs) >= 4
    route_types = {w["route_type"] for w in wfs}
    assert "SCRUTINY_ONLY" in route_types
    assert "SCRUTINY_EVC" in route_types
    assert "EVC_SAC_SHC" in route_types
    assert "EVC_ONLY" in route_types

    # Inspect single workflow details
    wf_id = wfs[0]["id"]
    res_single = client.get(
        f"/api/workflows/{wf_id}",
        headers={"Authorization": f"Bearer {superadmin_token}"}
    )
    assert res_single.status_code == 200
    data = res_single.json()
    assert "stages" in data
    assert len(data["stages"]) >= 3

def test_workflow_route_scrutiny_only_transition(client: TestClient, superadmin_token: str):
    """
    Tests an application proceeding through the SCRUTINY_ONLY route:
    PRELIMINARY_VALIDATION -> SCRUTINY -> FINAL_DISPOSITION
    """
    # 1. Create Application under SCRUTINY_ONLY route
    res_create = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        json={
            "institution_id": "INST-10482",
            "category": "Technical",
            "type": "Closure of Course (NBA Accredited)",
            "route_type": "SCRUTINY_ONLY",
            "academic_year": "2026-2027"
        }
    )
    assert res_create.status_code == 200
    app_id = res_create.json()["id"]

    # Upload sample document so prerequisites are fulfilled
    client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        data={
            "institution_id": "INST-10482",
            "application_id": app_id,
            "document_type": "Governing Body Resolution",
            "name": "GB_Resolution_Closure.pdf"
        }
    )

    # 2. Advance to SCRUTINY
    res_tr1 = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        json={
            "stage_code": "SCRUTINY",
            "status": "In scrutiny",
            "remarks": "Preliminary documents verified. Moving to Scrutiny Committee."
        }
    )
    assert res_tr1.status_code == 200
    assert res_tr1.json()["stage_code"] == "SCRUTINY"

    # 3. Advance from SCRUTINY to FINAL_DISPOSITION
    res_tr2 = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        json={
            "stage_code": "FINAL_DISPOSITION",
            "status": "Approved",
            "remarks": "Scrutiny committee found no deficiencies. Approved by Competent Authority."
        }
    )
    assert res_tr2.status_code == 200
    assert res_tr2.json()["stage_code"] == "FINAL_DISPOSITION"

def test_workflow_prevents_skipping_stages(client: TestClient, compliance_token: str):
    """
    Tests that the workflow engine rejects invalid stage skipping:
    Attempting to jump from PRELIMINARY_VALIDATION straight to FINAL_DISPOSITION.
    """
    res_create = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {compliance_token}"},
        json={
            "institution_id": "INST-10482",
            "category": "Technical",
            "type": "Extension of Approval",
            "route_type": "SCRUTINY_EVC"
        }
    )
    assert res_create.status_code == 200
    app_id = res_create.json()["id"]

    # Attempt illegal jump directly to FINAL_DISPOSITION
    res_illegal = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {compliance_token}"},
        json={
            "stage_code": "FINAL_DISPOSITION",
            "status": "Approved",
            "remarks": "Bypassing scrutiny and EVC illegally"
        }
    )
    assert res_illegal.status_code == 400
    assert "Invalid stage transition" in res_illegal.json()["detail"]

def test_workflow_idempotency_control(client: TestClient, superadmin_token: str):
    """
    Verifies that duplicate requests with the same idempotency key return the cached result
    and do not create duplicate stage logs or re-trigger state changes.
    """
    res_create = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        json={
            "institution_id": "INST-10482",
            "category": "Technical",
            "type": "New Programme Setup",
            "route_type": "SCRUTINY_EVC"
        }
    )
    app_id = res_create.json()["id"]
    idempotency_key = "IDEM-TEST-KEY-9999"

    # First call with idempotency key
    res_1 = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        json={
            "stage_code": "SCRUTINY",
            "status": "In scrutiny",
            "remarks": "First execution",
            "idempotency_key": idempotency_key
        }
    )
    assert res_1.status_code == 200
    assert res_1.json()["is_idempotent"] is False

    # Second call with the same idempotency key (retry/network replay)
    res_2 = client.post(
        f"/api/applications/{app_id}/transition",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        json={
            "stage_code": "SCRUTINY",
            "status": "In scrutiny",
            "remarks": "Duplicate execution",
            "idempotency_key": idempotency_key
        }
    )
    assert res_2.status_code == 200
    assert res_2.json()["is_idempotent"] is True
    assert "idempotent result preserved" in res_2.json()["message"]

def test_workflow_return_and_resubmission_flow(
    client: TestClient,
    superadmin_token: str,
    institute_head_token: str
):
    """
    Tests the complete deficiency lifecycle:
    1. Scrutiny officer returns application with deficiencies.
    2. Status moves to 'Returned for rectification'.
    3. Institute Head resubmits with rectification notes.
    4. Status advances to 'Resubmitted for scrutiny'.
    """
    res_create = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        json={
            "institution_id": "INST-10482",
            "category": "Technical",
            "type": "Increase in Intake",
            "route_type": "SCRUTINY_EVC"
        }
    )
    app_id = res_create.json()["id"]

    # 1. Return for deficiencies
    res_return = client.post(
        f"/api/applications/{app_id}/return-deficiency",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        json={
            "reason": "Cadre ratio deficient in CSE department. Missing Form 16.",
            "deficiencies": [
                "Submit certified Form 16 for 4 Assistant Professors",
                "Upload updated land classification certificate"
            ]
        }
    )
    assert res_return.status_code == 200
    assert res_return.json()["status"] == "Returned for rectification"
    assert res_return.json()["deficiency_count"] == 2

    # Verify application details reflect deficiency state
    res_get = client.get(
        f"/api/applications/{app_id}",
        headers={"Authorization": f"Bearer {superadmin_token}"}
    )
    assert res_get.json()["status"] == "Returned for rectification"
    assert res_get.json()["stage_code"] == "RE_SCRUTINY"

    # 2. Institute Head resubmits rectification
    res_resubmit = client.post(
        f"/api/applications/{app_id}/resubmit",
        headers={"Authorization": f"Bearer {institute_head_token}"},
        json={
            "compliance_notes": "Uploaded certified Form 16 and updated land revenue conversion certificate."
        }
    )
    assert res_resubmit.status_code == 200
    assert res_resubmit.json()["status"] == "Resubmitted for scrutiny"
    assert res_resubmit.json()["resubmission_count"] == 1
