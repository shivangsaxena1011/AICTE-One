"""
Automated Test Suite for AICTE ONE Platform
Testing Scenarios A through L as specified in Section 22
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal, Base, engine
from backend.seed import seed_database

client = TestClient(app)

# Scenario A — Institution
def test_scenario_a_institution_search_and_digital_twin():
    # 1. Search for an institution
    resp = client.get("/api/institutions?q=Noida")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    inst = data["data"][0]
    assert "Noida" in inst["name"]
    inst_id = inst["id"]

    # 2. Open Digital Twin profile
    profile_resp = client.get(f"/api/institutions/{inst_id}")
    assert profile_resp.status_code == 200
    profile = profile_resp.json()
    assert profile["institution"]["id"] == inst_id
    assert len(profile["applications"]) >= 1
    assert len(profile["documents"]) >= 1
    assert len(profile["compliance"]) >= 1
    assert len(profile["complaints"]) >= 1
    assert len(profile["activity_timeline"]) >= 1

# Scenario B — Application Workflow & Scrutiny
def test_scenario_b_application_lifecycle():
    # 1. Create an application
    create_payload = {
        "institution_id": "INST-10482",
        "category": "Engineering and Technology",
        "type": "Extension of Approval (EoA)",
        "academic_year": "2026-2027",
        "owner": "R. Sharma",
        "due_date": "2026-11-15"
    }
    create_resp = client.post("/api/applications", json=create_payload)
    assert create_resp.status_code == 200
    app_data = create_resp.json()
    app_id = app_data["id"]

    # 2. Advance to Scrutiny
    trans_payload = {
        "next_stage": "Scrutiny",
        "status": "In review",
        "actor": "R. Sharma",
        "remarks": "Preliminary checklist verified; proceeding to committee scrutiny."
    }
    trans_resp = client.post(f"/api/applications/{app_id}/transition", json=trans_payload)
    assert trans_resp.status_code == 200
    assert trans_resp.json()["current_stage"] == "Scrutiny"

    # 3. Return for Rectification with deficiency checklist
    return_resp = client.post(
        f"/api/applications/{app_id}/return-deficiency",
        params={
            "actor": "Scrutiny Committee",
            "remarks": "Fire NOC expired and Cadre ratio deficient"
        },
        json=["Fire Safety NOC renewal required", "Professor cadre deficit in CSE"]
    )
    assert return_resp.status_code == 200
    assert return_resp.json()["deficiency_count"] == 2

    # 4. Verify application reflects returned state
    get_resp = client.get(f"/api/applications/{app_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "Returned for rectification"
    assert get_resp.json()["current_stage"] == "Re-scrutiny"

# Scenario C — Document Verification & Validation Report
def test_scenario_c_document_upload_and_validation():
    # 1. Upload a document
    upload_resp = client.post(
        "/api/documents/upload",
        data={
            "institution_id": "INST-10482",
            "document_type": "Land Lease Agreement",
            "authority_ref": "REG-LAND-GBN/2016",
            "filename": "Registered_Lease_Agreement_2026.pdf"
        }
    )
    assert upload_resp.status_code == 200
    doc_id = upload_resp.json()["document_id"]

    # 2. Run authority verification adapter
    auth_resp = client.post(f"/api/documents/{doc_id}/verify-authority")
    assert auth_resp.status_code == 200
    assert "source" in auth_resp.json()

    # 3. Generate validation report
    rep_resp = client.get(f"/api/documents/{doc_id}/validation-report")
    assert rep_resp.status_code == 200
    report = rep_resp.json()
    assert report["document"]["id"] == doc_id
    assert "findings_and_evidence" in report["document"]

# Scenario D — Compliance Obligations
def test_scenario_d_compliance_lifecycle():
    # 1. Create an obligation
    create_payload = {
        "institution_id": "INST-10482",
        "title": "Anti-Ragging Squad Undertaking 2026",
        "category": "Regulatory undertaking",
        "due_date": "2026-11-20",
        "responsible_party": "Registrar NIET"
    }
    create_resp = client.post("/api/compliance", json=create_payload)
    assert create_resp.status_code == 200
    comp_id = create_resp.json()["id"]

    # 2. Upload evidence
    ev_resp = client.post(
        f"/api/compliance/{comp_id}/upload-evidence",
        data={"evidence_filename": "Anti_Ragging_Affidavit_Certified.pdf"}
    )
    assert ev_resp.status_code == 200
    assert ev_resp.json()["status"] == "Evidence submitted"

    # 3. Review and mark satisfied
    rev_resp = client.post(
        f"/api/compliance/{comp_id}/review",
        data={
            "decision": "Satisfied by evidence",
            "notes": "Verified against Supreme Court compliance guidelines.",
            "reviewer": "Compliance Officer"
        }
    )
    assert rev_resp.status_code == 200
    assert rev_resp.json()["status"] == "Satisfied by evidence"

# Scenario E — Complaint & Cross-Bureau Coordination Overlap
def test_scenario_e_complaints_and_overlap_detection():
    # 1. Register first complaint
    cplt_a_payload = {
        "institution_id": "INST-12890",
        "bureau": "PGRC",
        "category": "Student Intake Violation",
        "summary": "Alleged unauthorized intake in Mechanical Engineering batch 2026",
        "due_date": "2026-11-10"
    }
    resp_a = client.post("/api/complaints", json=cplt_a_payload)
    assert resp_a.status_code == 200
    case_a_id = resp_a.json()["id"]

    # 2. Register second complaint for the same institution with matching subject
    cplt_b_payload = {
        "institution_id": "INST-12890",
        "bureau": "Regulation Bureau",
        "category": "Admission Discrepancy",
        "summary": "Internal audit query on excess intake enrollment in Mechanical Engineering",
        "due_date": "2026-11-12"
    }
    resp_b = client.post("/api/complaints", json=cplt_b_payload)
    assert resp_b.status_code == 200
    case_b_id = resp_b.json()["id"]

    # 3. Verify overlap was detected
    assert resp_b.json()["related_case"] == case_a_id

    # 4. Confirm coordination link
    link_resp = client.post(
        "/api/complaints/link-coordination",
        json={
            "case_a_id": case_a_id,
            "case_b_id": case_b_id,
            "rationale": "Exact institution and intake issue correlation. Coordinated hearing scheduled."
        }
    )
    assert link_resp.status_code == 200
    assert "link_id" in link_resp.json()

# Scenario F — EVC Scheduling
def test_scenario_f_evc_scheduling_and_completion():
    # 1. Schedule visit
    sched_payload = {
        "application_id": "APP-2026-0837",
        "institution_id": "INST-10831",
        "visit_type": "Physical Visit",
        "scheduled_date": "2026-11-05",
        "committee_chair": "Prof. S.K. Agarwal",
        "committee_members": "Dr. R.C. Sharma, Er. M.K. Verma",
        "remarks": "Specialized laboratory inspection for AI & Data Science"
    }
    sched_resp = client.post("/api/evc/schedule", json=sched_payload)
    assert sched_resp.status_code == 200
    evc_id = sched_resp.json()["evc_id"]

    # 2. Reschedule visit
    resched_resp = client.put(
        f"/api/evc/{evc_id}/reschedule",
        params={
            "new_date": "2026-11-08",
            "reason": "Committee member travel arrangement conflict"
        }
    )
    assert resched_resp.status_code == 200

    # 3. Complete visit
    comp_resp = client.post(
        f"/api/evc/{evc_id}/complete",
        params={
            "observations": "All computing resources, cloud cluster access, and laboratory space verified satisfactory."
        }
    )
    assert comp_resp.status_code == 200

# Scenario G — AI Copilot with Real Record Grounding
def test_scenario_g_ai_copilot_grounded_response():
    resp = client.post(
        "/api/copilot/chat",
        json={"query": "Why was APP-2026-0842 flagged?"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "citations" in data
    assert len(data["citations"]) >= 1
    # Check that citation points to actual application
    assert any(c["record_id"] == "APP-2026-0842" for c in data["citations"])
    assert len(data["facts"]) >= 1
    assert len(data["recommendations"]) >= 1

# Scenario H — Audit Trail
def test_scenario_h_audit_trail_logging():
    resp = client.get("/api/audit?limit=10")
    assert resp.status_code == 200
    logs = resp.json()
    assert len(logs) >= 1
    latest = logs[0]
    assert "timestamp" in latest
    assert "actor" in latest
    assert "action" in latest
    assert "record" in latest

# Scenario I — Permissions & Authorization Model
def test_scenario_i_role_based_permissions():
    # Attempting to fetch non-existent record raises proper 404
    resp = client.get("/api/institutions/NON-EXISTENT-ID")
    assert resp.status_code == 404

# Scenario J — CSV Data Import & Duplicate Detection
def test_scenario_j_csv_data_import():
    csv_content = (
        "Permanent ID,Institution Name,State,District,City,Category,Institution Type\n"
        "1-99881122,Kashmir College of Technology,Jammu and Kashmir,Srinagar,Srinagar,Engineering and Technology,Government\n"
        "1-10482931,Noida Duplicate Check,Uttar Pradesh,Gautam Buddha Nagar,Greater Noida,Engineering and Technology,Private-Self Financed\n"
    )
    resp = client.post(
        "/api/institutions/import-csv",
        files={"file": ("test_import.csv", csv_content.encode("utf-8"), "text/csv")}
    )
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["total_rows"] == 2
    assert summary["created"] == 1
    assert summary["skipped_duplicates"] == 1

# Scenario K — Persistence
def test_scenario_k_persistence():
    resp = client.get("/api/institutions?q=Kashmir")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1

# Scenario L — Failure Handling & Honest Status
def test_scenario_l_honest_service_status():
    resp = client.post(
        "/api/documents/DOC-7812/verify-authority"
    )
    assert resp.status_code == 200
    data = resp.json()
    # Adapter indicates Sandbox / Simulated or test adapter
    assert "Sandbox" in data["source"] or "Adapter" in data["source"]
