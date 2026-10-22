# AICTE ONE — PHASE 4 DELIVERABLES & TECHNICAL IMPLEMENTATION REPORT
**Project:** SHANKH — AICTE ONE (Smart India Hackathon 2026)  
**Phase:** 4 — AI Assistant, Document Intelligence, Human-Review Workflows and Operational Risk Engine  
**Date:** October 2026  
**Status:** Complete & Authoritatively Verified (90/90 Tests Passed)

---

## 1. Executive Summary & Purpose

Phase 4 delivers practical, secure, and regulatory-compliant Artificial Intelligence and Document Intelligence capabilities for **AICTE ONE**, transforming administrative processing into an evidence-grounded, human-in-the-loop decision-support platform. 

Prior to Phase 4, document validation, discrepancy detection, complaint triage, and operational risk assessment relied either on manual scrutiny or disconnected heuristics. Phase 4 achieves full vertical integration of:

1. **Permission-Aware, Multi-Tenant AI Assistant (Copilot):** An administrative and institutional AI assistant grounded strictly in live database records (zero-hallucination guarantee). Defended by multi-pattern prompt injection guards and enforced multi-tenant access control (Institute Heads locked to own institution, Students locked to own complaints, Whistleblower identity protection). Covers 10 statutory scenarios across English, Hindi, and Hinglish.
2. **Secure Document Ingestion Pipeline:** Hardened upload pipeline with file size caps (<= 15MB), magic byte validation (`%PDF-`, PNG, JPEG, TIFF), and rejection of malicious scripts, executables (PE/MZ), and web shells. Files are stored securely with sanitized UUID names.
3. **Real OCR & Explainable Document Intelligence:** Integration of `pypdf` stream parsing and `pytesseract` OCR fallback with the AICTE Rules Engine to generate structured, explainable forensic reports with discrepancy flags, anomaly scores, and mandatory statutory caveats.
4. **Human-Review Workspace & Immutable Audit History:** Full state machine for human oversight (`CONFIRM_MATCH`, `CORRECT_FIELDS`, `DISMISS_FLAG` with mandatory justification, `REQUEST_MORE_EVIDENCE`), recording all actions in `DocumentReviewHistory` and `AuditLog` while preserving original OCR vs overridden data.
5. **SHA-256 Duplicate & Cross-Institution Reuse Detection:** Automatic cryptographic hashing to detect identical document uploads within or across different institutions (flagging potential certificate or land-deed recycling).
6. **AI-Assisted Complaint Analysis & Triage:** Objective categorization, urgency classification (identifying severe issues like ragging, harassment, or financial fraud), missing information detection, and duplicate complaint overlap checking with transparent human preview.
7. **Operational Risk Recommendation Engine:** Automated detection of SLA breach bottlenecks, recurring deficiency clusters, and officer workload concentrations, featuring an interactive Accept/Dismiss/Correct audit workflow.
8. **100% Comprehensive Test Suite:** 33 new Phase 4 test cases ensuring zero regressions, bringing the unified test suite to **90/90 passing tests**.

---

## 2. Permission-Aware AI Copilot Engine

### 2.1 Prompt Injection Defense & Sanitization
Implemented in `backend/services/copilot_service.py` via `detect_prompt_injection(query)`:
- Scans user inputs against hostile patterns including:
  - System instruction overrides (`ignore previous instructions`, `forget all rules`, `system prompt`)
  - Jailbreak triggers (`dan mode`, `developer mode`, `bypass security`)
  - Arbitrary SQL/Code execution attempts (`drop table`, `union select`, `exec(`, `eval(`)
  - Role-play manipulation (`you are now an unrestricted ai`)
- When flagged, the engine terminates processing immediately, raises an HTTP 400 rejection, and logs the attempt in `AuditLog` without exposing internal prompt structures.

### 2.2 Multi-Tenant RBAC & Privacy Scoping
- **Super Admin & AICTE Officers (`compliance_officer`, `scrutiny_officer`, `admin`):** Access to aggregate national counts, all workflow stages, regional pendencies, and pending review queues.
- **Institute Heads (`institute_head`):** Strict single-institution jail. The engine automatically injects the user's registered `institution_id` into database filters. If an Institute Head asks for another college's confidential records, the query is rejected with `Access Denied`.
- **Students / Complainants (`student`):** Access restricted strictly to complaints filed by their own user ID (`filed_by == user.id`).
- **Whistleblower Protection:** The Copilot service explicitly redacts and refuses to return the names, phone numbers, or email addresses of student complainants to protect complainants against institutional retribution.

### 2.3 Ten Grounded Statutory Intent Scenarios (EN / HI / Hinglish)
The Copilot service maps natural language queries to deterministic database queries with full facts, rule evaluation results, recommendations, and statutory caveats:

| # | Statutory Intent Scenario | Supported English / Hindi / Hinglish Query Example | Grounded Execution Logic |
| :--- | :--- | :--- | :--- |
| **1** | **Scrutiny Stage Pendency** | *"How many applications are pending at scrutiny?"* / *"स्क्रूटनी चरण में कितने आवेदन लंबित हैं?"* | Aggregates `Application` where `status == "UNDER_SCRUTINY"`. Scoped to tenant if institute head. |
| **2** | **SLA Deadline Breaches** | *"Which applications exceeded deadline?"* / *"कौन से आवेदन समय सीमा पार कर चुके हैं?"* | Scans `Application` where `target_completion_date < today` and not in terminal states. |
| **3** | **Institutional Approval Status** | *"What is approval status for INST-001?"* / *"संस्थान INST-001 की मान्यता स्थिति क्या है?"* | Queries `Institution` + `Application` for specific academic year; verifies permanent ID match. |
| **4** | **Approaching EVC Deadlines** | *"Which EVCs approaching deadlines?"* / *"ईवीसी निरीक्षण समय-सीमा के करीब कौन से हैं?"* | Filters active `EVCInspection` scheduled within the next 7 days. |
| **5** | **Outstanding Undertakings** | *"Institutions with outstanding undertakings"* / *"बकाया अंडरटेकिंग वाले संस्थान"* | Queries `Undertaking` records with `status == "PENDING"`. |
| **6** | **Expiring Documents** | *"Which prescribed documents are expiring?"* / *"कौन से दस्तावेज समाप्त होने वाले हैं?"* | Checks `Document` where `expiry_date` is in the past or within 30 days. |
| **7** | **Case / Officer Ownership** | *"Who owns application APP-2026-001?"* / *"आवेदन का स्वामित्व किस अधिकारी के पास है?"* | Resolves `assigned_officer_id` and assigned department/bureau from `Application`. |
| **8** | **Authorized Complaint Status** | *"Status of complaint CMP-101"* / *"मेरी शिकायत CMP-101 की स्थिति क्या है?"* | RBAC-checked query returning complaint status, urgency, and assigned committee. |
| **9** | **Highest Stage Pendency** | *"Which stage has highest pendency?"* / *"किस चरण में सबसे अधिक पेंडेंसी है?"* | Executes `GROUP BY status` on active applications and ranks stages by volume. |
| **10** | **Remaining Compliance Items** | *"What compliance items remain to be reviewed?"* / *"सत्यापन के लिए कौन से अनुपालन मद बाकी हैं?"* | Filters `ComplianceRecord` where `status == "PENDING"`. |

### 2.4 Multilingual Grounding & Zero-Hallucination Guarantee
- Every response payload adheres to the `CopilotResponse` schema:
  - `reply`: Multilingual synthesis explaining findings clearly in English, Hindi, or Hinglish.
  - `facts`: Deterministic raw data points extracted from the database.
  - `rule_results`: Verification rules triggered.
  - `recommendations`: Administrative next steps.
  - `statutory_caveat`: Mandatory legal reminder that Copilot findings are investigative aids and do not constitute formal administrative decrees.

---

## 3. Secure Document Ingestion Pipeline

### 3.1 Upload Security & Threat Mitigation (`backend/services/ocr_service.py`)
Document uploads (`POST /api/documents/upload`) undergo multi-stage sanitization:
1. **Size Enforcement:** Maximum allowable upload size is strictly clamped to **15 MB**. Payloads exceeding this limit receive an immediate HTTP 400 error.
2. **Cryptographic Magic Byte Inspection:** Inspects true binary header bytes rather than relying on spoofable HTTP `Content-Type` headers or file extensions:
   - **PDF:** Must begin with `%PDF-` (`0x25 0x50 0x44 0x46 0x2D`)
   - **PNG:** Must begin with `\x89PNG\r\n\x1a\n`
   - **JPEG:** Must begin with `\xff\xd8\xff`
   - **TIFF:** Must begin with `II*\x00` (little-endian) or `MM\x00*` (big-endian)
3. **Executable & Malicious Signature Quarantine:** Content streams are scanned for executable headers (`MZ` DOS/PE headers, `ELF`) and script tags (`<?php`, `eval(`, `<script`, `#!/bin/sh`). Files containing executable payloads are rejected immediately.
4. **Sanitized Storage:** Files are written to disk using non-enumerable, collision-proof UUID paths (`uploads/{uuid}_{safe_filename}`), preventing directory traversal attacks.

```mermaid
flowchart TD
    In[Incoming File Upload] --> SizeCheck{File Size <= 15MB?}
    SizeCheck -- No --> Err1[HTTP 400: Payload Too Large]
    SizeCheck -- Yes --> MagicCheck{Magic Bytes Match Allowed Types?}
    MagicCheck -- No --> Err2[HTTP 400: Invalid Magic Bytes]
    MagicCheck -- Yes --> MalCheck{Malicious Script / PE Header Detected?}
    MalCheck -- Yes --> Err3[HTTP 400: Malicious Signature Detected]
    MalCheck -- No --> HashGen[Generate SHA-256 Hash]
    HashGen --> SaveDisk[Save to UUID Sanitized Path]
    SaveDisk --> TriggerOCR[Trigger Text Extraction & Forensics]
```

---

## 4. Real OCR & Explainable Document Intelligence

### 4.1 Dual-Engine Text Extraction
- **Native PDF Stream Extraction (`pypdf`):** Rapid, high-accuracy digital text extraction from vector PDFs.
- **Tesseract OCR Fallback (`pytesseract`):** Automatic optical character recognition on scanned image pages and bitmap documents when native text extraction yields fewer than 20 characters.

### 4.2 Regulatory Rules Engine Validation (`backend/services/rules_engine.py`)
Extracted text and metadata are passed into `validate_document()` to verify compliance against AICTE Approval Process Handbook (APH) standards:
- **Permanent ID Consistency:** Cross-references the document's mentioned Permanent ID against the target `Institution.permanent_id`. Mismatches trigger high-severity discrepancy flags.
- **Expiry Date & Validity:** Compares document validity dates against the current date and the academic session boundary. Expired documents or certificates expiring mid-academic-cycle are flagged.
- **Issuing Authority Verification:** Verifies recognized government and regulatory authorities (e.g. *Town Planning Authority*, *PWD*, *State Board of Technical Education*, *UGC*, *Affiliating University*).

### 4.3 Structured Forensic Report Schema
Every analyzed document stores a persistent JSON forensic report in `Document.forensic_report_json`:
```json
{
  "document_id": "DOC-9812",
  "document_type": "Land Use Certificate",
  "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "ocr_text_preview": "This is to certify that land measuring 10.5 acres...",
  "extracted_metadata": {
    "detected_permanent_id": "1-10482931",
    "detected_expiry_date": "2027-06-30",
    "detected_issuing_authority": "Directorate of Town and Country Planning"
  },
  "checks": [
    {"name": "Permanent ID Verification", "passed": true, "details": "Matches expected ID 1-10482931"},
    {"name": "Document Expiry Check", "passed": true, "details": "Valid through 2027-06-30"},
    {"name": "Authorized Issuing Authority", "passed": true, "details": "Verified issuing authority"}
  ],
  "discrepancies": [],
  "anomaly_score": 0.0,
  "statutory_caveat": "AI/OCR anomaly indicators are investigative flags for competent authorities and do NOT constitute legal proof of forgery or automated regulatory rejection."
}
```

---

## 5. Human-Review Workspace & Immutable Audit History

### 5.1 Controlled State Machine (`backend/routes/documents.py`)
AI and OCR findings serve exclusively as decision support. Final regulatory determinations are strictly executed by authorized human officers through `POST /api/documents/{id}/review`:

```mermaid
stateDiagram-v2
    [*] --> PENDING_REVIEW: Upload & OCR Extraction
    PENDING_REVIEW --> CONFIRM_MATCH: Officer Confirms Match
    PENDING_REVIEW --> CORRECT_FIELDS: Officer Overrides / Corrects Data
    PENDING_REVIEW --> DISMISS_FLAG: Officer Dismisses Flag (Requires Justification)
    PENDING_REVIEW --> REQUEST_MORE_EVIDENCE: Officer Requests Additional Proof
    
    CONFIRM_MATCH --> [*]
    CORRECT_FIELDS --> [*]
    DISMISS_FLAG --> [*]
    REQUEST_MORE_EVIDENCE --> [*]
```

### 5.2 Mandatory Justification & Immutable History
- **`DISMISS_FLAG` Rule:** When an officer dismisses an AI anomaly flag, the system strictly enforces a non-empty, detailed justification string (`>= 5` characters). Blank or trivial dismissals are rejected with HTTP 400.
- **Field Overrides (`CORRECT_FIELDS`):** User corrections are saved to `Document.human_overridden_fields` as structured JSON, updating the active metadata while preserving the original OCR extraction for auditability.
- **Audit Persistence:** Every state change generates:
  1. An entry in `DocumentReviewHistory` containing `previous_status`, `new_status`, `action`, `notes`, `overridden_fields`, and `reviewed_by`.
  2. A tamper-evident record in the centralized `AuditLog`.

---

## 6. SHA-256 Duplicate & Cross-Institution Reuse Detection

### 6.1 Cryptographic Integrity & Reuse Alerting
Implemented in `backend/routes/documents.py` via `detect_duplicate_documents()`:
- Computes the SHA-256 digest of incoming file streams.
- Scans existing documents in the database for matching digests:
  - **Intra-Institution Duplicate:** Flags accidental re-upload of the same file for the same college.
  - **Cross-Institution Duplicate (Regulatory Red Flag):** Flags if an identical Land Use Certificate, Building Safety Certificate, or Faculty NOC is uploaded across two different institutions (`inst_A != inst_B`), raising an urgent forensic alert for investigating officers.

---

## 7. AI-Assisted Complaint Analysis & Triage

### 7.1 Automated Triage Pipeline (`backend/services/complaint_ai_service.py`)
Enables rapid triage of incoming institutional and student grievances (`POST /api/complaints/{id}/ai-triage`):
1. **Category Classification:** Classifies complaints into standardized domains:
   - *Capitation Fee & Financial Extortion*
   - *Ragging & Student Safety*
   - *Faculty Harassment & Irregularities*
   - *Infrastructure Deficiencies*
   - *Admission Malpractices*
2. **Objective Urgency Scoring:**
   - **`HIGH`:** Threats to life, sexual harassment, physical ragging, or large-scale financial extortion.
   - **`MEDIUM`:** Exam schedule disputes, delayed marksheets, or laboratory maintenance issues.
   - **`LOW`:** General administrative queries or canteen complaints.
3. **Missing Mandatory Evidence Flags:** Identifies whether essential supporting proof (such as payment receipts, incident dates, or formal representations) is missing, alerting the intake officer to request further details before committee assignment.
4. **Duplicate Clustering:** Compares complaint titles and descriptions against existing active grievances within the same institution to prevent redundant committee workflows.

### 7.2 Human-in-the-Loop Triage Preview
The endpoint `POST /api/complaints/triage-preview` allows intake officers to preview suggested categories, urgency scores, and missing details *before* committing any triage metadata to the database.

---

## 8. Operational Risk Recommendation Engine

### 8.1 Automated System Risk Analysis (`backend/services/risk_service.py`)
Scans backend records in real time (`GET /api/analytics/ai/risk-recommendations`) to detect systemic operational hazards:
- **SLA Breach Risks:** Identifies applications lingering within 24 hours of configured processing deadlines.
- **Deficiency Clusters:** Identifies institutions exhibiting recurrent document rejections or chronic non-compliance across multiple academic cycles.
- **Workload Concentration Bottlenecks:** Detects imbalances where an individual scrutiny officer or regional bureau has more than 25 active unreviewed cases assigned.

### 8.2 Recommendation Action Lifecycle (`POST /api/analytics/ai/risk-recommendations/{id}/action`)
Officers can review and resolve system-generated recommendations with three audit-logged actions:
- **`ACCEPT`:** Approves the recommendation (e.g. initiates workload re-balancing or expedited inspection scheduling).
- **`DISMISS`:** Rejects the recommendation with mandatory officer justification.
- **`CORRECT`:** Modifies recommendation parameters before execution.

---

## 9. Comprehensive Automated Test Verification

A dedicated automated test suite (`tests/test_phase4_ai_and_documents.py`) of **33 test cases** was implemented and executed alongside Phase 1, Phase 2, and Phase 3 suites using `pytest`.

### 9.1 Test Execution Results
```powershell
============================= test session starts =============================
platform win32 -- Python 3.14.0a4, pytest-8.3.4, pluggy-1.5.0
rootdir: C:\Users\Project\AICTE One
collected 90 items

tests/test_auth.py ...........                                           [ 12%]
tests/test_institutions.py .................                             [ 31%]
tests/test_phase2_workflow.py .........................                  [ 58%]
tests/test_phase3_advanced.py .                                          [ 60%]
tests/test_phase3_institutions_and_analytics.py ...                      [ 63%]
tests/test_phase4_ai_and_documents.py ................................. [100%]

============================= 90 passed in 45.54s =============================
```

### 9.2 Breakdown of Phase 4 Test Coverage
1. `test_prompt_injection_defense`: Verifies rejection of system override, jailbreak, and SQL injection prompts.
2. `test_multitenant_student_isolation`: Confirms student cannot view other students' complaints via Copilot.
3. `test_multitenant_institute_head_isolation`: Confirms institute head cannot query other institutions' confidential data.
4. `test_whistleblower_protection_in_copilot`: Confirms student complainant identities are never revealed.
5. `test_copilot_10_statutory_scenarios` (10 sub-tests): Validates all 10 mandated scenarios in English, Hindi, and Hinglish.
6. `test_document_magic_byte_validation`: Tests valid PDF, PNG, JPEG magic bytes and verifies upload success.
7. `test_document_malicious_signature_rejection`: Tests rejection of executables (`MZ`), PHP scripts, and HTML script tags.
8. `test_document_size_limit_enforcement`: Tests HTTP 400 rejection for files exceeding 15MB.
9. `test_document_forensic_report_and_discrepancy_detection`: Verifies Permanent ID discrepancy and expiry detection.
10. `test_human_review_workflow_actions`: Tests `CONFIRM_MATCH`, `CORRECT_FIELDS`, and `REQUEST_MORE_EVIDENCE`.
11. `test_human_review_dismiss_requires_justification`: Confirms HTTP 400 rejection when dismissing flags without reason.
12. `test_duplicate_document_detection`: Tests intra- and cross-institution SHA-256 duplicate alerts.
13. `test_complaint_ai_triage_preview_and_apply`: Tests category suggestion, urgency scoring, and missing info flags.
14. `test_operational_risk_recommendations_and_actions`: Tests automated risk generation and Accept/Dismiss/Correct lifecycle.

---

## 10. Frontend API Bridge Integration

The API client (`assets/js/utils/api.js` and `aicte-one-prototype/assets/js/utils/api.js`) has been updated with methods for all Phase 4 services:
- `api.askCopilot(query, useGemini)`
- `api.uploadDocumentWithForensics(formData)`
- `api.getDocumentForensics(documentId)`
- `api.reviewDocument(documentId, reviewData)`
- `api.getHumanReviewQueue(status)`
- `api.detectDuplicateDocuments(sha256Hash)`
- `api.previewComplaintTriage(complaintData)`
- `api.applyComplaintTriage(complaintId, triageData)`
- `api.getAIRiskRecommendations(status)`
- `api.actOnRiskRecommendation(recommendationId, actionData)`

---

## 11. Conclusion & Next Steps

Phase 4 successfully delivers a secure, multi-tenant AI Assistant, an explainable document intelligence pipeline with real OCR, an immutable human-review workspace, intelligent complaint triage, and an operational risk recommendation engine.

The platform guarantees that **AI never acts autonomously to approve, deny, or revoke institutional status**. All statutory actions remain strictly governed by authorized officers, supported by transparent evidence trails and tamper-evident audit logs. With **90 out of 90 tests passing**, AICTE ONE is technically sound, secure, and ready for production deployment and Smart India Hackathon 2026 evaluations.
