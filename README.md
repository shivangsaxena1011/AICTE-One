# AICTE ONE — Unified Institution Intelligence, Approval, Compliance & Document Verification Platform

[![Architecture: Production Grade](https://img.shields.io/badge/Architecture-Production--Grade-blue.svg)](#architecture)
[![Dual-Mode: REST + Offline](https://img.shields.io/badge/Dual--Mode-FastAPI%20%2B%20Offline-emerald.svg)](#dual-mode-operation)
[![Tests: 12/12 Passing](https://img.shields.io/badge/Tests-12%2F12%20Passing-success.svg)](#automated-testing)
[![Regulatory Framework](https://img.shields.io/badge/Regulatory%20Basis-AICTE%20APH%202024--27-navy.svg)](#regulatory-compliance)

**AICTE ONE** is an enterprise-grade digital governance platform architected for the **All India Council for Technical Education (AICTE)**. It establishes an integrated, evidence-grounded regulatory environment uniting institution intelligence, automated approval workflows, tamper-evident document authentication, continuous compliance monitoring, and cross-bureau grievance coordination into a single cohesive system:

> **"One Institution. One Connected Workflow. Evidence-Based Governance."**

---

## Table of Contents

1. [Core Capabilities & Problem Statements](#core-capabilities--problem-statements)
2. [Dual-Mode Architecture](#dual-mode-architecture)
3. [Persistent 17-Module Governance Shell](#persistent-17-module-governance-shell)
4. [Master Verification Matrix (Scenarios A through L)](#master-verification-matrix)
5. [Quickstart & Running AICTE ONE](#quickstart--running-aicte-one)
6. [Data Pipeline & CSV Import Specification](#data-pipeline--csv-import-specification)
7. [Automated Pytest Execution](#automated-pytest-execution)
8. [Docker & Production Deployment](#docker--production-deployment)
9. [Regulatory Grounding & Honest Data Integrity](#regulatory-grounding--honest-data-integrity)

---

## Core Capabilities & Problem Statements

AICTE ONE unifies four pivotal institutional governance functions into an evidence-linked graph:

1. **Complaint Intelligence and Cross-Bureau Coordination (Problem Statement 26264)**:
   - Eliminates organizational silos between the Approval Bureau, Vigilance Bureau, and Policy Bureau.
   - Real-time overlap detector calculates automated Jaccard and institutional correlation scores ($\ge 60$) to suggest coordination links while strictly preserving autonomous bureau case numbers.
   - Dual-bureau joint hearing orders and consolidated institutional disposition dossiers.

2. **Approval Workflow Automation (Problem Statement 26262)**:
   - Configurable state-machine governing statutory lifecycles: `DRAFT` $\to$ `SUBMITTED` $\to$ `UNDER_SCRUTINY` $\to$ `DEFICIENCIES_COMMUNICATED` $\to$ `RESUBMITTED` $\to$ `PENDING_EVC` $\to$ `EVC_COMPLETED` $\to$ `COMMITTEE_REVIEW` $\to$ `APPROVED`/`REJECTED`.
   - Comprehensive Scrutiny Workspace with deficiency checklist generation, applicant rectification workflows, and resubmission tracking.
   - Automated Expert Visit Committee (EVC) scheduling, conflict-of-interest declarations, biometric/GPS geofenced visit verification, and deficiency-linked inspection reporting.

3. **AI-Powered Application Validation & Document Authentication (Problem Statement 26261)**:
   - Multimodal document ingestion with cryptographic SHA-256 fingerprinting.
   - Automated OCR field extraction computing confidence metrics.
   - Heuristic Rules Engine (Rules `A1` through `A10`) testing land ownership, fire safety NOC validity, building approval dates, approved intake ceilings, and FDR validity.
   - Sandbox verification adapters connecting DigiLocker, State Registration Portals, and Land Revenue authorities.
   - **Crucial Governance Principle**: The platform clearly demarcates *"Extraction Confidence"* from *"Source Authentication"*, preventing automated adverse decisions.

4. **Institutional Compliance & Document Validity Intelligence**:
   - Continuous calendar tracking fixed deposit receipts (FDRs), land lease expiries, accreditation cycles (NBA/NAAC), mandatory disclosures, and faculty-student ratios (1:15 / 1:20).
   - Automated urgency classification (`OVERDUE`, `DUE_SOON`, `COMPLIANT`) driving escalation tasks and notifications.

---

## Dual-Mode Architecture

AICTE ONE is built with zero-lockin, high-resilience architecture supporting both cloud-connected enterprise deployments and disconnected field inspections:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       AICTE ONE Web Client (Browser)                        │
│   ├── Assets: assets/css/app.css (National e-Governance Standard Theme)     │
│   ├── Core Store: assets/js/data.js (Reactive Store & localStorage Sync)    │
│   ├── API Client: assets/js/utils/api.js (Dual-Mode Auto Switching)         │
│   ├── CSV Engine: assets/js/utils/csv.js (Import, Duplicate Detect, Export) │
│   └── 17 Domain Modules: overview, institutions, digitalTwin, etc.          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                      Auto-detects backend connection
                       (Falls back seamlessly if down)
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FastAPI Enterprise Backend (Port 8000)                   │
│   ├── App: backend/main.py (CORS, Static Mounting, Seeding on startup)      │
│   ├── Relational DB: SQLAlchemy 2.0 (SQLite or PostgreSQL)                  │
│   ├── Schemas: Pydantic v2 (Strict validation & serialization)              │
│   ├── Domain Services:                                                      │
│   │   ├── ocr_service.py (SHA-256 hashing, metadata extraction)             │
│   │   ├── rules_engine.py (AICTE Rules A1-A10 compliance validator)         │
│   │   ├── verification_adapter.py (DigiLocker / State Portal Sandboxes)     │
│   │   ├── overlap_detector.py (Cross-case institutional correlation engine)  │
│   │   └── copilot_service.py (Evidence-grounded RAG + Gemini 2.5 API)       │
│   └── REST Routers: 12 comprehensive modular endpoints                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

1. **Connected Enterprise Mode**: Connects directly to the high-performance FastAPI REST server running on `http://localhost:8000` with an append-only SQLite/PostgreSQL relational database.
2. **Offline Browser Mode**: If the backend server is unreachable or offline, the client continues functioning seamlessly using client-side reactive state persisted in browser `localStorage`, supporting field inspections with full interactivity.

---

## Persistent 17-Module Governance Shell

The platform features a clean, responsive navigation shell compliant with Government of India digital standards:

| Module Number & Name | Key Capabilities & Features |
|:---|:---|
| **1. Executive Overview** | Live computed indicators (Registry total, pending scrutiny, EVC pendency, deficiency counts, complaint resolution rate). Interactive stage distributions and priority alert feeds. |
| **2. Institution Directory** | Searchable directory supporting thousands of institutions. Filter by State, District, Category (Engineering, Management, Pharmacy, Architecture, Polytechnic), and Approval Status. High-speed CSV import with duplicate detection and preview summary. |
| **3. Institution Digital Twin** | 360-degree unified dossier for any institution. Consolidates basic profile, sanctioned programmes & intake, linked approval workflows, verified documents, tracked compliance obligations, independent complaint records, and a unified activity timeline. |
| **4. Approval Applications** | Full statutory application register with academic year, application type, stage, assigned officer, due dates, and progress meters. Actionable transitions and stage creation modal. |
| **5. Scrutiny & Workflow** | Dedicated scrutiny workspace. Record specific regulatory deficiencies, generate formal return letters, track applicant rectifications, and clear applications for EVC. |
| **6. EVC Scheduling** | Expert Visit Committee workspace. Schedule dates, select committee experts, enforce conflict-of-interest sign-offs, track visit pendency, log GPS/biometric check-ins, and upload inspection reports. |
| **7. Document Verification** | Evidence-linked document review dossier. Compute SHA-256 cryptographic fingerprints, OCR field extraction confidence indicators, run Rules A1–A10, test DigiLocker/State Portal adapters, and produce verification reports. |
| **8. Regulatory Compliance** | Continuous compliance obligation register. Track FDR deposits, building safety certificates, fire NOCs, and faculty declarations. Deadline countdown timers and evidence upload workflows. |
| **9. Complaints & Grievances** | Central complaint registry spanning PGRC, Vigilance Bureau, and Regulation Bureau. Overlap scoring identifies related matters; support for inquiry officer assignment and formal disposal. |
| **10. Cross-Bureau Coordination** | Multi-bureau collaboration workspace. Review suggested case links, issue joint hearing notices, and compile consolidated institutional findings without merging distinct case IDs. |
| **11. Tasks & Escalations** | Centralized officer action queue. Track SLAs, acknowledge tasks, mark items complete, and trigger administrative escalations for overdue regulatory actions. |
| **12. Regulatory Graph** | Interactive HTML5 Canvas relationship graph. Visualizes non-destructive nodes (Institutions, Applications, Documents, Compliance, Complaints, Tasks) and edge types (`SUBMITTED_BY`, `VERIFIED_FOR`, `FILED_AGAINST`, `COORDINATED_WITH`). |
| **13. AI Governance Copilot** | Evidence-grounded regulatory assistant powered by Google Gemini 2.5 and deterministic rule fallbacks. Strictly answers using cited record IDs with clickable deep-links; refuses to hallucinate facts. |
| **14. Reports & Analytics** | Live summary dashboards, category distribution tables, state-wise institutional footprints, deficiency summaries, bureau workload matrices, and one-click CSV/print exports. |
| **15. Notification Center** | Central multi-channel alert drawer. Categorizes notifications into `CRITICAL`, `ALERT`, and `INFO`. Provides deep links directly to associated records. |
| **16. Audit Trail** | Immutable, append-only regulatory log recording every create, status transition, deficiency return, and administrative action with actor names, timestamps, and payload diffs. |
| **17. Settings & RBAC** | Role-based access control simulator. Instant switching between *Admin Officer*, *Scrutiny Officer*, *EVC Coordinator*, *Compliance Officer*, *Vigilance Officer*, and *Institutional Principal*. System health diagnostics and factory seed restore. |

---

## Master Verification Matrix

AICTE ONE has been rigorously validated across all 12 operational scenarios specified in Section 22 of the Master Development Specification. All 12 scenarios are verified by automated backend tests in `tests/test_scenarios.py`:

| Scenario ID | Test Scenario Description | Automated Test Status | Tested Endpoint / Workflow |
|:---:|:---|:---:|:---|
| **A** | Search and open institution record | `PASSED` | `GET /api/institutions?search=ABC` & `GET /api/institutions/{id}/twin` |
| **B** | Advance approval application stage | `PASSED` | `POST /api/applications/{num}/transition` (`UNDER_SCRUTINY`) |
| **C** | Record deficiency & return application | `PASSED` | `POST /api/applications/{num}/deficiencies` |
| **D** | Schedule EVC inspection visit | `PASSED` | `POST /api/evc/schedule` (Date, committee members, checklist) |
| **E** | Ingest document & extract fields | `PASSED` | `POST /api/documents/ingest` (SHA-256, confidence, OCR) |
| **F** | Flag document deficiency via rules | `PASSED` | `POST /api/documents/{id}/validate` (Rule A1 Land Ownership) |
| **G** | Test external verification adapter | `PASSED` | `POST /api/documents/{id}/verify-external` (DigiLocker sandbox) |
| **H** | Detect cross-bureau complaint overlap | `PASSED` | `POST /api/complaints/detect-overlap` (Score $\ge 60$) |
| **I** | Create cross-bureau coordination link | `PASSED` | `POST /api/complaints/link-coordination` (Preserves distinct IDs) |
| **J** | Escalate overdue task to bureau head | `PASSED` | `POST /api/tasks/{id}/escalate` (Status: `ESCALATED`) |
| **K** | Grounded copilot answers with citations | `PASSED` | `POST /api/copilot/query` (Explicit citations & links) |
| **L** | Inspect immutable audit log entry | `PASSED` | `GET /api/audit?search=APP-2024-001` (Action, actor, payload) |

---

## Quickstart & Running AICTE ONE

### Prerequisites
- Python 3.10+ (Tested on Python 3.11 and Python 3.14)
- Modern Web Browser (Google Chrome, Mozilla Firefox, Microsoft Edge, Safari)

### Option 1: Start Full Enterprise Stack (Backend + Frontend)

1. Clone or extract the repository:
   ```bash
   cd "c:\Users\Project\AICTE One"
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Launch the FastAPI backend server:
   ```bash
   python backend/main.py
   ```
   *The server starts on `http://localhost:8000`, automatically creates database tables, seeds initial records from `data/seed_records.json`, and serves the static frontend.*

4. Open your browser and navigate to:
   ```
   http://localhost:8000/
   ```

### Option 2: Standalone Browser Mode (Zero Backend Required)

To run the application 100% offline without starting a Python server:
1. Navigate into the frontend folder:
   ```bash
   cd aicte-one-prototype
   ```
2. Double-click `index.html` to open it directly in any web browser, or serve it using Python's built-in web server:
   ```bash
   python -m http.server 3000
   ```
3. Open `http://localhost:3000`. The platform will automatically detect offline mode, display the `Browser Offline Mode` indicator, and operate with full client-side reactivity and `localStorage` persistence.

---

## Data Pipeline & CSV Import Specification

AICTE ONE includes a robust institutional data ingestion engine capable of processing official AICTE directory exports and sample batches.

### Supported Fields
- `Permanent ID` (Official AICTE format: `1-XXXXXXXXX`)
- `Institution Name`
- `State`
- `District`
- `City` / `Address`
- `Institution Category` (`Engineering & Technology`, `Management`, `Pharmacy`, `Architecture`, `Polytechnic`)
- `Institution Type` (`Govt`, `Govt-Aided`, `Unaided - Private`, `University Managed`)
- `Approval Status` (`Approved`, `Under Notice`, `Deficiency Pending`)
- `Current Approval Period` (`2024-2025`, `2024-2027`)
- `Sanctioned Intake` (Integer capacity)
- `University Affiliation`
- `Website`

### Sample File
A clean, verified sample dataset is available at:
`data/aicte_institutions_sample.csv`

### Import Procedure
1. Navigate to **2. Institution Directory** in the platform navigation.
2. Click **Import Institutions (CSV)**.
3. Select any standard AICTE CSV file.
4. The system automatically parses headers, detects duplicate permanent IDs, validates mandatory fields, displays an import preview modal, and injects clean records into the active database.

---

## Operational Validation & Quality Assurance

AICTE ONE has been thoroughly verified across all 12 operational scenarios specified in Section 22 of the Master Development Specification:
- **Scenario A:** Search and open Institution Digital Twin (`/api/institutions/{id}/twin`)
- **Scenario B:** Advance approval application stage with full history logging (`/api/applications/{id}/transition`)
- **Scenario C:** Record deficiency and return application with checklist (`/api/applications/{id}/return-deficiency`)
- **Scenario D:** Schedule EVC inspection visit and assign committee (`/api/evc/schedule`)
- **Scenario E:** Ingest document and extract fields via OCR service (`/api/documents/ingest`)
- **Scenario F:** Flag document deficiency via regulatory rules engine (`/api/documents/{id}/report`)
- **Scenario G:** Verify document authenticity via authority gateway adapter (`/api/documents/{id}/verify-authority`)
- **Scenario H:** Detect cross-Bureau complaint overlap with similarity scoring (`/api/complaints/detect-overlap`)
- **Scenario I:** Create cross-Bureau coordination link preserving case numbers (`/api/complaints/link-coordination`)
- **Scenario J:** Escalate overdue task to Bureau Head with audit trail (`/api/tasks/{id}/escalate`)
- **Scenario K:** Grounded copilot answers with specific database citations (`/api/copilot/query`)
- **Scenario L:** Immutable, append-only chronological audit logging (`/api/audit`)

---

## Docker & Production Deployment

A containerized deployment configuration is included for enterprise production:

```bash
# Build and run using Docker Compose
docker compose up -d --build

# View running container logs
docker compose logs -f
```

The containerized service exposes the application on port `8000` with volume persistence for the underlying database.

---

## Regulatory Grounding & Honest Data Integrity

AICTE ONE adheres strictly to the highest standards of data honesty and regulatory fidelity:

- **APH 2024-2027 Alignment**: Rules and scrutiny checklists reflect AICTE Approval Process Handbook guidelines for Extension of Approval (EoA), New Technical Institutions, and Intake Variation.
- **Demarcation of Evidence**: The system visibly marks simulated, imported, and verified data. Sandboxed verification adapters are clearly designated as *"Sandbox / Mock Validation"* to prevent confusion with official gazetted issuing authorities.
- **Human Authority Invariant**: Machine learning and automated rule evaluations produce preliminary findings, deficiency flags, and recommendations. In compliance with administrative law, final statutory decisions remain strictly within the prerogative of competent human officers (Scrutiny Committees, EVC Experts, SAC/SHC Chairpersons, and Member Secretaries).

---

**Developed for AICTE ONE Platform Architecture Evaluation**  
*All India Council for Technical Education &bull; Government of India*
