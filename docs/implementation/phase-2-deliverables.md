# AICTE ONE (SHANKH) — Phase 2 Deliverables Report
## Approval Workflow Engine, EVC, Compliance Undertakings & Multi-Tier Escalation

**Project:** SHANKH — AICTE ONE (SIH 2026)  
**Milestone:** Phase 2 Implementation  
**Status:** Complete & Verified (100% Test Pass Rate: 44/44 Automated Tests)  
**Date:** 2026-10-22  

---

## 1. Executive Summary

Phase 2 builds upon the rock-solid security and RBAC foundation established in Phase 1, delivering a production-grade, configurable workflow automation engine adhering strictly to the **AICTE Approval Process Handbook (APH)**. 

The implementation introduces:
1. **Configurable Persistent Workflow Engine:** Supports multiple statutory APH routes (`SCRUTINY_ONLY`, `SCRUTINY_EVC`, `EVC_SAC_SHC`, `EVC_ONLY`) with prerequisite enforcement, idempotency protection, and non-linear deficiency returns.
2. **Hardened Expert Visit Committee (EVC) Module:** Implements institutional conflict-of-interest prevention, committee quorum validation, and geo-tagged inspection report filings.
3. **Statutory Time-Bound Undertakings Register:** Manages conditional approvals and deficiency remediations with statutory deadline tracking, tenant-isolated evidence submissions, and officer review dispositions.
4. **Lease & Prescribed Document Validity Engine:** Tracks expiration of land leases, building safety certificates, and fire NOCs with advance warning windows and automatic regulatory blocks on non-compliant applications.
5. **SLA, Ageing, Pendency Monitoring & Multi-Tier Escalation:** Real-time SLA clock tracking, pause/resume mechanisms for statutory stay periods, automated breach detection, and multi-tier escalation (Level 1 Regional Officer, Level 2 Bureau Head, Level 3 Member Secretary).

---

## 2. Core Architecture & Database Models

### 2.1 Database Schema Extensions (`backend/models.py`)

| Model | Table Name | Purpose & Primary Attributes |
|---|---|---|
| `WorkflowDefinition` | `workflow_definitions` | Stores persistent APH workflow templates: `route_type`, `version`, `stages_config`, `rules_config`, `is_active`. |
| `WorkflowStageDefinition` | `workflow_stage_definitions` | Individual stage configuration within a route: `sequence_order`, `allowed_transitions_json`, `required_roles_json`, `prerequisites_json`, `sla_days`, `escalation_policy_json`. |
| `Application` (Enhanced) | `applications` | Extended with: `workflow_definition_id`, `workflow_version`, `route_type`, `stage_code`, `stage_entered_at`, `stage_due_date`, `is_paused`, `total_pause_days`, `resubmission_count`, `is_escalated`, `escalation_level`, `last_idempotency_key`. |
| `ApplicationStage` (Enhanced) | `application_stages` | Extended with: `from_stage`, `to_stage`, `stage_code`, `action`, `time_spent_hours`, `sla_breached`, `idempotency_key`. |
| `EVCSchedule` (Enhanced) | `evc_schedules` | Extended with: `convener`, `expert_members_json`, `conflicts_declared`, `geo_latitude`, `geo_longitude`, `recommendation`, `checklist_findings_json`. |
| `Undertaking` | `undertakings` | Time-bound compliance conditions: `condition_ref`, `undertaking_type`, `statutory_deadline`, `evidence_file`, `review_notes`, `reviewed_by`, `status`. |
| `DocumentValidity` | `document_validities` | Land lease and safety certificate registry: `document_type`, `document_ref_number`, `issue_date`, `expiry_date`, `advance_warning_days`, `status`, `renewal_application_ref`. |
| `EscalationEvent` | `escalation_events` | Multi-tier SLA breach tracking: `entity_type`, `entity_id`, `escalation_level`, `trigger_reason`, `escalated_to_role`, `status`, `resolution_notes`. |

### 2.2 Non-Destructive Auto-Migration (`backend/database.py`)

All new models and table columns are created or altered automatically on engine connection without dropping existing tables or data.

---

## 3. Workflow Engine (`backend/services/workflow_engine.py`)

### 3.1 Supported Statutory Routes

1. **`SCRUTINY_ONLY` Route:**  
   *Use Case:* Existing institutions, minor alterations, course closures, and accredited programmes.  
   *Path:* `PRELIMINARY_VALIDATION` &rarr; `SCRUTINY` &rarr; `FINAL_DISPOSITION` (Can loop to `RE_SCRUTINY` on deficiency).
2. **`SCRUTINY_EVC` Route:**  
   *Use Case:* Standard statutory route for new institution setups, intake expansions, and infrastructure alterations.  
   *Path:* `PRELIMINARY_VALIDATION` &rarr; `SCRUTINY` &rarr; `EVC_SCHEDULING` &rarr; `EVC_EVALUATION` &rarr; `FINAL_DISPOSITION`.
3. **`EVC_SAC_SHC` Route:**  
   *Use Case:* Contested inspections or major non-compliances requiring Standing Appellate or Hearing Committee appraisal.  
   *Path:* `PRELIMINARY_VALIDATION` &rarr; `SCRUTINY` &rarr; `EVC_SCHEDULING` &rarr; `EVC_EVALUATION` &rarr; `SAC_SHC_REVIEW` &rarr; `FINAL_DISPOSITION`.
4. **`EVC_ONLY` Route:**  
   *Use Case:* Surprise inspections, complaint investigations, or specific physical re-verification visits.  
   *Path:* `EVC_SCHEDULING` &rarr; `EVC_EVALUATION` &rarr; `FINAL_DISPOSITION`.

### 3.2 State Transition & Safety Guarantees

- **No Stage Skipping:** Transitions are strictly validated against the active workflow stage configuration. Bypassing uncompleted intermediate stages raises HTTP 400.
- **Idempotency Protection:** Clients can send an `idempotency_key` with transition requests. Repeated or replayed calls return the previous result with `"is_idempotent": true` without re-creating stage or audit logs.
- **Prerequisite Validation:** Applications cannot advance to `FINAL_DISPOSITION` if mandatory documents are missing, critical documents (e.g. lease, fire NOC) are expired, or mandatory EVC reports have not been filed.
- **Deficiency Return & Resubmission:** Reviewers can return applications with mandatory deficiency checklists to `RE_SCRUTINY`. Institute Heads can resubmit rectified evidence, advancing status to `Resubmitted for scrutiny` while tracking resubmission rounds.
- **SLA Pause and Resume:** Authorized officers can pause the application clock for legal or administrative holds (e.g. court stay), and resuming automatically extends the target disposal deadline by the exact paused duration.

---

## 4. EVC Hardening & Inspection Reports (`backend/routes/evc.py`)

- **Route Eligibility Check:** EVC scheduling is rejected for applications registered under non-inspection routes (such as `SCRUTINY_ONLY`).
- **Conflict of Interest Detection:** Validates committee chair and expert names against target institution identifiers, contact details, and affiliations.
- **Quorum Enforcement:** Mandates committee composition comprising a Convener, Chair, and at least 2 subject experts.
- **Geo-Tagged Inspection Findings:** Committee report filings mandate geo-coordinates (`geo_latitude`, `geo_longitude`), checklist evaluation (`infrastructure`, `faculty_cadre`, `laboratories`), and formal recommendations (`Recommended`, `Not Recommended`, `Conditional`).
- **Automated Workflow Advance:** Filing an approved EVC report automatically transitions the application to the `EVC_EVALUATION` stage and queues SAC/SHC or Final Disposition.

---

## 5. Compliance Undertakings & Lease Validity Engines

### 5.1 Time-Bound Undertakings (`backend/routes/compliance.py`)
- Tracks statutory undertakings (e.g. faculty recruitment within 6 months, endowment fund deposit, land revenue order).
- Scoped tenant isolation: Institute Heads can view and submit evidence only for their assigned institution.
- Formal review disposition: Compliance officers can evaluate evidence and mark conditions as `Verified & Accepted` or `Rejected` with audit notes.
- Automatic breach detection: Background/trigger scans identify overdue undertakings and flag regulatory non-compliance.

### 5.2 Lease & Prescribed Document Validity (`backend/routes/documents.py`)
- Tracks land lease deeds, building safety certificates, and municipal fire NOCs.
- Automatic status derivation: `Active`, `Expiring Soon` (within advance warning window, e.g. 60 days), or `Expired`.
- Regulatory safety check: Applications are automatically blocked from approval if critical documents are expired.
- Renewal workflow: Institutions can submit verified renewal certificates with updated expiry dates and authority reference numbers.

---

## 6. SLA Monitoring & Multi-Tier Escalation (`backend/routes/escalations.py`)

The escalation service (`backend/services/escalation_service.py`) provides real-time SLA breach detection and multi-tier escalation policies:

| Escalation Level | Threshold | Escalation Target | Alert Priority |
|---|---|---|---|
| **Level 1** | Overdue by 1–2 days | Regional Officer (`REGIONAL_OFFICER`) | Important |
| **Level 2** | Overdue by 3–5 days | Bureau Head (`BUREAU_HEAD`) | Critical |
| **Level 3** | Overdue by > 5 days | Member Secretary (`SUPER_ADMIN`) | Emergency / Urgent |

- Automatically generates `EscalationEvent` records and in-app `Notification` alerts.
- Dedicated resolution workflow allows officers to record resolution notes and reset escalation flags upon action.

---

## 7. Automated Test Suite Results

A comprehensive automated test suite covering Phase 1 (30 tests) and Phase 2 (14 tests) was executed using `pytest`:

```
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
collected 44 items

tests/test_auth.py (10/10 PASSED)
tests/test_database_and_security.py (6/6 PASSED)
tests/test_rbac_and_isolation.py (14/14 PASSED)
tests/test_workflow_engine.py (5/5 PASSED)
  - test_list_and_get_workflow_definitions: PASSED
  - test_workflow_route_scrutiny_only_transition: PASSED
  - test_workflow_prevents_skipping_stages: PASSED
  - test_workflow_idempotency_control: PASSED
  - test_workflow_return_and_resubmission_flow: PASSED
tests/test_evc_and_compliance.py (5/5 PASSED)
  - test_evc_scheduling_rejected_on_scrutiny_only_route: PASSED
  - test_evc_conflict_of_interest_detection: PASSED
  - test_evc_completion_and_report_submission: PASSED
  - test_time_bound_undertakings_lifecycle: PASSED
  - test_document_and_lease_validity_engine: PASSED
tests/test_sla_and_escalation.py (4/4 PASSED)
  - test_sla_pendency_calculation: PASSED
  - test_application_sla_pause_and_resume: PASSED
  - test_automated_sla_scan_and_escalation_triggers: PASSED
  - test_pendency_summary_metrics: PASSED

============================= 44 passed in 23.84s =============================
```

**Overall Test Pass Rate: 100% (44/44 passed).**
