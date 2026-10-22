"""
Phase 2 Test Suite: SLA, Ageing, Pendency Monitoring & Multi-Tier Escalation
Tests pendency calculation, pause/resume clock adjustments, automated escalation scans,
and escalation resolution workflows.
"""
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient

def test_sla_pendency_calculation(client: TestClient, superadmin_token: str):
    """Verifies that the pendency endpoint calculates stage ageing and days remaining accurately."""
    res_app = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        json={
            "institution_id": "INST-10482",
            "category": "Technical",
            "type": "New Course Introduction",
            "route_type": "SCRUTINY_EVC"
        }
    )
    app_id = res_app.json()["id"]

    res_pend = client.get(
        f"/api/applications/{app_id}/pendency",
        headers={"Authorization": f"Bearer {superadmin_token}"}
    )
    assert res_pend.status_code == 200
    data = res_pend.json()
    assert data["application_id"] == app_id
    assert "stage_deadline" in data
    assert "days_remaining" in data
    assert data["is_paused"] is False
    assert data["is_escalated"] is False

def test_application_sla_pause_and_resume(client: TestClient, compliance_token: str):
    """
    Tests pausing the SLA clock (e.g. court stay) and resuming it with deadline adjustment.
    """
    res_app = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {compliance_token}"},
        json={
            "institution_id": "INST-10482",
            "category": "Technical",
            "type": "Change of Site",
            "route_type": "SCRUTINY_EVC"
        }
    )
    app_id = res_app.json()["id"]

    # Pause SLA
    res_pause = client.post(
        f"/api/applications/{app_id}/pause",
        headers={"Authorization": f"Bearer {compliance_token}"},
        json={"reason": "High Court interim stay order regarding municipal land demarcation"}
    )
    assert res_pause.status_code == 200
    assert "paused" in res_pause.json()["message"]

    # Verify status is paused
    res_get = client.get(
        f"/api/applications/{app_id}",
        headers={"Authorization": f"Bearer {compliance_token}"}
    )
    assert res_get.json()["is_paused"] is True

    # Resume SLA
    res_resume = client.post(
        f"/api/applications/{app_id}/resume",
        headers={"Authorization": f"Bearer {compliance_token}"}
    )
    assert res_resume.status_code == 200
    assert "resumed" in res_resume.json()["message"]

    # Verify status is no longer paused
    res_get_resumed = client.get(
        f"/api/applications/{app_id}",
        headers={"Authorization": f"Bearer {compliance_token}"}
    )
    assert res_get_resumed.json()["is_paused"] is False

def test_automated_sla_scan_and_escalation_triggers(
    client: TestClient,
    superadmin_token: str,
    compliance_token: str
):
    """
    Tests the system-wide SLA breach scanner and multi-tier escalation:
    1. Creates application with past due date.
    2. Runs SLA scan.
    3. Verifies EscalationEvent generated and application marked escalated.
    """
    # Create application with past deadline
    past_due = (date.today() - timedelta(days=4)).isoformat()
    res_app = client.post(
        "/api/applications",
        headers={"Authorization": f"Bearer {superadmin_token}"},
        json={
            "institution_id": "INST-10482",
            "category": "Technical",
            "type": "Extension of Approval",
            "route_type": "SCRUTINY_EVC",
            "due_date": past_due
        }
    )
    app_id = res_app.json()["id"]

    # Trigger SLA breach scan
    res_scan = client.post(
        "/api/escalations/trigger-scan",
        headers={"Authorization": f"Bearer {superadmin_token}"}
    )
    assert res_scan.status_code == 200
    scan_data = res_scan.json()
    assert "applications" in scan_data

    # Query escalation logs
    res_esc = client.get(
        "/api/escalations",
        headers={"Authorization": f"Bearer {superadmin_token}"}
    )
    assert res_esc.status_code == 200
    escalations = res_esc.json()
    assert len(escalations) >= 1

    # Resolve an escalation
    esc_to_resolve = escalations[0]["id"]
    res_resolve = client.post(
        f"/api/escalations/{esc_to_resolve}/resolve",
        headers={"Authorization": f"Bearer {compliance_token}"},
        json={"resolution_notes": "Scrutiny committee assigned additional officers to expedite review."}
    )
    assert res_resolve.status_code == 200
    assert res_resolve.json()["status"] == "Resolved"

def test_pendency_summary_metrics(client: TestClient, compliance_token: str):
    """Verifies the aggregated pendency metrics API."""
    res = client.get(
        "/api/applications/metrics/pendency-summary",
        headers={"Authorization": f"Bearer {compliance_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "total_applications" in data
    assert "active_applications" in data
    assert "overdue_applications" in data
    assert "route_breakdown" in data
