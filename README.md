# AICTE ONE — Unified Institution Intelligence, Approval, Compliance & Document Verification Platform

[![Production Status](https://img.shields.io/badge/Production-Live%20on%20Vercel-success.svg)](https://aicte-one.vercel.app/)
[![Architecture: Enterprise Grade](https://img.shields.io/badge/Architecture-FastAPI%20%2B%20Serverless%20REST-blue.svg)](#system-architecture)
[![Design System](https://img.shields.io/badge/Design%20System-Bharat%20Civic--Sovereign%20Tech-orange.svg)](#design-system--uiux)
[![Responsive: Mobile & Desktop](https://img.shields.io/badge/Responsive-Mobile%20%7C%20Tablet%20%7C%20Desktop-emerald.svg)](#multi-device-responsive-layout)
[![Automated Test Suite](https://img.shields.io/badge/Tests-109%2F109%20Passing%20(100%25)-brightgreen.svg)](#automated-verification--code-quality)
[![Regulatory Framework](https://img.shields.io/badge/Regulatory%20Basis-AICTE%20APH%202026--27-indigo.svg)](#regulatory-grounding)

**AICTE ONE (SHANKH)** is an enterprise-grade digital public infrastructure (DPI) platform architected for the **All India Council for Technical Education (AICTE)** under the Ministry of Education, Government of India. It establishes an integrated, evidence-grounded regulatory governance environment uniting institutional directory intelligence, automated multi-stage approval scrutiny, cryptographic document verification, continuous statutory compliance monitoring, and cross-bureau grievance coordination into a single sovereign platform.

> **"One Institution. One Connected Workflow. Evidence-Based Governance."**

- **Live Production URL:** [https://aicte-one.vercel.app/](https://aicte-one.vercel.app/)
- **Document Verification Demo:** [https://documentverify-two.vercel.app/](https://documentverify-two.vercel.app/)
- **Repository:** [https://github.com/shivangsaxena1011/AICTE-One](https://github.com/shivangsaxena1011/AICTE-One)

---

## Table of Contents

1. [Executive Summary & Core Problem Statements](#executive-summary--core-problem-statements)
2. [Key Platform Capabilities (Phases 1–5 Release Baseline)](#key-platform-capabilities)
3. [Design System & UI/UX ("Bharat Civic-Sovereign Tech")](#design-system--uiux)
4. [Multi-Device Responsive Layout](#multi-device-responsive-layout)
5. [System Architecture & Resilience](#system-architecture--resilience)
6. [The 17 Statutory Governance Modules](#the-17-statutory-governance-modules)
7. [Live REST API Specification](#live-rest-api-specification)
8. [Running Locally & Deployment Guide](#running-locally--deployment-guide)
9. [Automated Verification & Security Audit](#automated-verification--security-audit)
10. [Regulatory Grounding & Honest Data Integrity](#regulatory-grounding--honest-data-integrity)

---

## Executive Summary & Core Problem Statements

AICTE ONE resolves critical institutional oversight bottlenecks across technical education regulatory governance:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 AICTE ONE CORE PLATFORM                                │
├──────────────────────────┬──────────────────────────┬──────────────────────────────────┤
│ Problem Statement 26264  │ Problem Statement 26262  │ Problem Statement 26261          │
│ Complaint Intelligence & │ Approval Workflow &      │ AI Document Verification &       │
│ Cross-Bureau Overlap     │ Scrutiny Automation      │ Forensic Anomaly Detection       │
├──────────────────────────┼──────────────────────────┼──────────────────────────────────┤
│ • Cross-bureau clashes   │ • 5 configurable routes  │ • Multimodal forensic OCR        │
│ • PGRC ⟷ Regulation audit│ • Land & faculty rules   │ • DigiLocker DPI relay           │
│ • Automated holds        │ • Geofenced EVC visits   │ • SHA-256 seal verification      │
│ • Joint hearing dossiers │ • Deficiency checklists  │ • Cadastral deed lease tracking  │
└──────────────────────────┴──────────────────────────┴──────────────────────────────────┘
```

1. **Complaint Intelligence and Cross-Bureau Coordination (Problem Statement 26264)**:
   - Eliminates organizational silos between the Approval Bureau, Regulation Bureau (RB), and Public Grievance Redressal Cell (PGRC).
   - Real-time overlap detector calculates automated correlation scores ($\ge 60$) across institution Permanent IDs (PIDs) to highlight concurrent inquiries and prevent conflicting dispositions.
   - Dual-bureau joint hearing orders and automated injunction holds.

2. **Approval Workflow Automation (Problem Statement 26262)**:
   - Configurable 5-stage state-machine governing statutory lifecycles under AICTE APH 2026–27:
     `Intake & TER Fee` $\to$ `Rule Engine Ingestion` $\to$ `Scrutiny Committee` $\to$ `EVC Inspection` $\to$ `SHC / SAC Appeal`.
   - Comprehensive Scrutiny Workspace with deficiency checklist generation, applicant rectification windows (15-day SLA), and resubmission tracking.
   - Automated Expert Visit Committee (EVC) scheduling with conflict-of-interest prevention.

3. **AI-Powered Application Validation & Document Authentication (Problem Statement 26261)**:
   - Multimodal document ingestion with cryptographic SHA-256 fingerprinting.
   - Optical Character Recognition (OCR) extraction computing per-field confidence metrics.
   - Heuristic Rules Engine (Rules `A1` through `A10`) testing registered land ownership, fire safety NOC validity, building approval dates, approved intake ceilings, and FDR validity.
   - Direct integration link to the live **[Document Verification Demo](https://documentverify-two.vercel.app/)** service.
   - **Crucial Governance Principle**: The platform clearly demarcates *"Extraction Confidence"* from *"Source Authentication"*, preventing automated adverse decisions without human review.

4. **Institutional Compliance & Digital Twin 360°**:
   - Continuous calendar tracking fixed deposit receipts (FDRs), land lease expiries, accreditation cycles (NBA/NAAC), mandatory disclosures, and faculty cadre ratios (1:2:6 / 1:15 / 1:20).
   - Real-time Institution Digital Twin aggregating approvals, documents, complaints, compliance obligations, and audit logs.

---

## Key Platform Capabilities

### 1. Configurable Approval Workflow Engine (APH 2026–27)
- **5 Supported Processing Routes:** `SCRUTINY_ONLY` (Extension of Approval), `SCRUTINY_EVC` (New Institutions / Program Addition), `STANDALONE_EVC` (Surprise Inspection / Verification), `APPEAL_HEARING` (Standing Appellate Committee review), and `CLOSURE_REVERSAL`.
- **Enforced State Progression:** Guaranteed stage prerequisites prevent illegal progression jumps.
- **Deficiency Loop:** Deficiencies return applications to applicants with detailed deficiency checklists while pausing statutory SLA clocks.
- **Audit Trails:** Immutable, append-only logs capture actor, role, timestamp, prior state, target state, and regulatory rationale.

### 2. Expert Visiting Committee (EVC) & Conflict-of-Interest Guard
- **Automated CoI Detection:** Cross-checks committee member institutional histories and affiliations to eliminate bias.
- **Biometric & Geofenced Scheduling:** Supports GPS coordinate verification, date windows, and surprise inspection dispatch.

### 3. Authoritative Institutional Dataset (8,842 Records Ingested)
- **Authoritative Provenance:** Normalized and persisted **8,842 official technical institutions** across 36 States/UTs from national AICTE datasets into `aicte_one.db`.
- **Intelligent Lookup:** Fast Permanent ID matching (`1-XXXXXXXXX`) and educational acronym expansion (e.g., `VJTI`, `COEP`, `OIST`, `RVCE`, `BITS`).
- **Non-Hallucinating Verification Gateway:** Unrecognized records return `"Needs Verification"` with direct links to the AICTE Central Portal, strictly avoiding false unapproved classifications.

### 4. Multilingual AI Copilot & Deterministic SQL Grounding
- **Dual-Engine Architecture:** Combines Google Gemini LLM with a 100% deterministic, zero-hallucination grounded SQL engine.
- **Trilingual Comprehension:** Fluent in English, formal Hindi, and conversational Hinglish.
- **Prompt-Injection Defense:** Automated input sanitizer intercepts adversarial attempts to override regulatory constraints.

### 5. Forensic Document Intelligence
- **Deep File Validation:** Rejects disguised scripts using MIME checks and binary magic byte verification (`%PDF`, `\xFF\xD8\xFF`, `\x89PNG`).
- **SHA-256 Deduplication:** Detects re-submitted or cross-institution recycled documents.
- **Live Demo Bridge:** Dedicated interface button launching the standalone [AI Document Verification Demo](https://documentverify-two.vercel.app/).

### 6. Role-Based Access Control (RBAC) & Security Hardening
- **8 Individual Statutory Roles:** Super Administrator, Security Officer, Compliance Officer, Complaint Officer, Anti-Ragging Officer, Institute Head, Student Complainant, and Public Visitor.
- **Defensive Safeguards:** Argon2/Bcrypt password hashing, account lockout after 5 failed attempts, TOTP MFA for privileged accounts, sanitized CSV exports against spreadsheet macro injection, and path-traversal neutralization.

---

## Design System & UI/UX

AICTE ONE implements the **"Bharat Civic-Sovereign Tech"** visual design language, inspired by India Stack platforms (DigiLocker, Aadhaar, ONDC) alongside high-trust enterprise compliance environments:

### Typography
- **Display & Headings:** `Plus Jakarta Sans` — Authoritative geometric headers with clear aperture definition.
- **Body & Data Grid:** `Inter` — Tabular alignment optimized for dense screen display and alphanumeric codes (AICTE PID, NIRF Rank, AISHE Codes).
- **Monospaced Verification:** `JetBrains Mono` — Dedicated to cryptographic hashes, DigiLocker URI references, timestamped digital signatures, and SLA countdowns.
- **Iconography:** `Material Symbols Outlined` — Modern, standardized civic iconography.

### Sovereign Color Palette
- **Primary Sovereign Navy (`#001332` / `#0f284e`):** Represents structural reliability and regulatory stewardship.
- **Accent Bharat Saffron (`#ea580c` / `#fd651e`):** Drives vital administrative urgency, pending verification states, and focal review triggers.
- **Ashoka Emerald (`#002f1e` / `#23a274`):** Governs sovereign validation states, verified cryptographic credentials, and compliance sign-offs.
- **Alert Rose (`#ba1a1a` / `#ffdad6`):** Statutory deficiencies, audit failures, and concurrent inquiry injunctions.
- **Canvas Base (`#faf8ff`):** Crisp border system (`#dae2fd` / `#e2e8f0`) meeting WCAG AAA contrast standards.

---

## Multi-Device Responsive Layout

AICTE ONE delivers complete operational fidelity across all device form factors:

| Screen Tier | Width Range | Layout Adaptation |
| :--- | :--- | :--- |
| **Desktop / Laptop** | `≥ 1024px` | Persistent left sidebar (`w-64`), full topbar with dynamic institutional context, 5-column Bento KPI grid, full 12-column approval tables. |
| **Tablet** | `768px - 1023px` | Fixed sidebar, collapsible telemetry strip, 2-column KPI grid, horizontally swipeable data tables. |
| **Mobile Phone** | `< 768px` | **Off-canvas slide drawer** with touch backdrop scrim and explicit close trigger; full-width main workspace; responsive header; edge-to-edge modal dialogs with sticky headers/footers. |

---

## System Architecture & Resilience

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AICTE ONE Single-Page Application (SPA)                  │
│   ├── CSS: assets/css/app.css (Bharat Civic-Sovereign Tech Stylesheet)      │
│   ├── Reactive Store: assets/js/data.js (localStorage Synced Store)         │
│   ├── API Client: assets/js/utils/api.js (FastAPI Connected)                │
│   ├── CSV Engine: assets/js/utils/csv.js (Import, Export, Sanitization)     │
│   └── 17 Domain Modules: overview, institutions, digitalTwin, verification  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                          Statutory REST API Calls
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FastAPI Enterprise Backend (Port 8000)                   │
│   ├── Entry: backend/main.py & api/index.py (Vercel Serverless Entrypoint)  │
│   ├── Database: SQLAlchemy 2.0 (SQLite / PostgreSQL)                        │
│   ├── Schemas: Pydantic v2 (Strict validation & sanitization)               │
│   ├── Security Middleware: RBAC, CORS, HSTS, CSP, X-Request-ID, Throttling  │
│   ├── Domain Services:                                                      │
│   │   ├── workflow_engine.py (Configurable APH approval state machine)      │
│   │   ├── ocr_service.py (SHA-256 checksums, field confidence scoring)      │
│   │   ├── rules_engine.py (AICTE Approval Process Handbook Rules A1-A10)     │
│   │   ├── institution_search.py (PID search, acronym expansion)             │
│   │   ├── institution_importer.py (Deduplicated national dataset ingestion) │
│   │   ├── escalation_service.py (Automated SLA monitoring & escalation)     │
│   │   └── copilot_service.py (Multilingual grounded SQL AI Assistant)       │
│   └── REST Routers: 17 fully registered, tested endpoints                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The 17 Statutory Governance Modules

| # | Group | Module Name | Core Capabilities |
|:---|:---|:---|:---|
| **1** | Core Operations | **Executive Overview** | Apex command center, 15 real-time KPIs, regional velocity matrix, live pipeline feed. |
| **2** | Core Operations | **Institution Directory** | Searchable registry of 8,842 technical colleges. Filter by state, category, type, and intake. |
| **3** | Core Operations | **Institution Digital Twin** | 360° unified institutional dossier aggregating applications, evidence, compliance, and complaints. |
| **4** | Core Operations | **Approval Applications** | Multi-type application register (EoA, New Institution, Intake Increase, Closure). |
| **5** | Core Operations | **Scrutiny & Workflow** | 5-stage APH scrutiny stepper, deficiency checklist generator, 15-day applicant rectification window. |
| **6** | Core Operations | **EVC Scheduling** | Expert Visit Committee visit scheduler, conflict-of-interest checker, GPS geofenced visit verification. |
| **7** | Evidence & Oversight | **Document Verification** | Forensic OCR engine, SHA-256 seal verification, [External Verification Demo](https://documentverify-two.vercel.app/) link. |
| **8** | Evidence & Oversight | **Regulatory Compliance** | Time-bound compliance calendar tracking FDRs, land leases, NBA/NAAC accreditations, and disclosures. |
| **9** | Evidence & Oversight | **Complaints & Grievances** | Central grievance intake (PGRC, CPGRAMS), whistleblower isolation, case transfer and disposal. |
| **10** | Evidence & Oversight | **Cross-Bureau Clashes** | Overlap coordination workspace calculating correlation scores, concurrent inquiry flags, and joint hearings. |
| **11** | Evidence & Oversight | **Tasks & Escalations** | Action-oriented task workflow with SLA urgency indicators (`Critical`, `High`, `Normal`) and auto-escalation. |
| **12** | Graph & AI | **Regulatory Graph** | Graph visualizer mapping relationships between Institutions, Approvals, Documents, and Officials. |
| **13** | Graph & AI | **AI Governance Copilot** | Evidence-grounded regulatory assistant in English, Hindi, and Hinglish with zero hallucination. |
| **14** | Assurance & Admin | **Reports & Analytics** | 12 distribution graphs (A–L), intake vs. capacity, regional pendency charts, secure CSV export. |
| **15** | Assurance & Admin | **Notification Center** | Real-time notification drawer with unread badge counter and role-based broadcasts. |
| **16** | Assurance & Admin | **Audit Trail** | Append-only, immutable regulatory log recording every status transition, inspection, and action. |
| **17** | Assurance & Admin | **Settings & Security** | Role persona switcher (8 roles), password management, MFA setup, and database snapshot utilities. |

---

## Live REST API Specification

All REST API endpoints are secured with JWT authentication and strict RBAC:

```bash
# Health & Diagnostics
GET    /api/health                       # Public health probe (Status, Version, Database state)
GET    /api/system/health/detailed       # Telemetry probe (DB latency, storage stats, queues)
POST   /api/system/backup/create         # Cryptographic database backup snapshot

# Authentication & Sessions
POST   /api/auth/login                   # Authenticate user (Supports TOTP MFA)
GET    /api/auth/profile                 # Retrieve active authenticated user profile & tenant ID
POST   /api/auth/logout                  # Invalidate active session token
POST   /api/auth/password-reset-request  # Request password recovery token
POST   /api/auth/password-reset-confirm  # Reset password with secure recovery token

# Institutional Registry & Verification
GET    /api/institutions                 # Paginated institution directory (search, filter)
GET    /api/institutions/search          # Acronym expansion & fuzzy search
GET    /api/institutions/verify/{id}     # Authoritative public approval verification gateway
GET    /api/institutions/{id}            # Institutional profile details
GET    /api/institutions/{id}/twin       # 360° Digital Twin composite dossier
POST   /api/institutions/import          # Ingest authoritative AICTE records (Preview & Confirm)
GET    /api/institutions/export/csv      # Sanitized CSV export (Formula injection protected)

# Approval Applications & Workflows
GET    /api/applications                 # Application register (Tenant-isolated)
POST   /api/applications                 # Lodge new approval application
GET    /api/applications/{id}            # Application details & deficiency history
POST   /api/applications/{id}/transition # Execute workflow stage transition (APH validated)
GET    /api/workflows/definitions        # List configurable APH workflow routes

# Document Forensics & Verification
GET    /api/documents                    # Document ingestion register
POST   /api/documents/upload             # Validate MIME/magic bytes, SHA-256 hash, run OCR
GET    /api/documents/{id}               # Document verification dossier & forensic report
POST   /api/documents/{id}/review        # Human-in-the-loop scrutiny adjudication

# Compliance & Obligations
GET    /api/compliance                   # Compliance obligations calendar
POST   /api/compliance                   # Register compliance undertaking or FDR
GET    /api/compliance/expiring          # List obligations approaching deadline

# Complaints & Overlap Intelligence
GET    /api/complaints                   # Central complaints registry (Privacy isolated)
POST   /api/complaints                   # Register citizen grievance or audit case
GET    /api/complaints/overlaps          # Cross-bureau overlap correlation detector
POST   /api/complaints/{id}/transfer     # Transfer case between bureaus
POST   /api/complaints/{id}/dispose      # Record final disposal order

# Tasks & EVC Scheduling
GET    /api/tasks                        # Administrative task list
POST   /api/tasks                        # Create new task
GET    /api/evc                          # EVC inspection schedules
POST   /api/evc/schedule                 # Schedule committee visit (Conflict-of-interest verified)

# Intelligence Graph & Copilot
GET    /api/graph                        # Complete node-edge graph data
POST   /api/copilot/query                # Multilingual grounded AI query engine (English/Hindi/Hinglish)

# Audit & Notifications
GET    /api/audit                        # Append-only governance audit trail
GET    /api/notifications                # Notification stream (Role-filtered)
```

---

## Running Locally & Deployment Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.12 and 3.14)
- Node.js 18+ (for frontend AST verification)

### 1. Local Development (FastAPI + Client)

```bash
# 1. Clone the repository
git clone https://github.com/shivangsaxena1011/AICTE-One.git
cd "AICTE One"

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Start the FastAPI backend
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser at `http://127.0.0.1:8000/`. The backend will automatically serve both the REST API and the frontend application with active database seeding.

*(On Windows, you can also double-click `RUN_AICTE_ONE.bat` to launch automatically).*

### 2. Running Automated Tests

```bash
# Run full regression test suite (109 tests)
python -m pytest -v
```

### 3. Deployment on Vercel

AICTE ONE is pre-configured for zero-friction serverless deployment on Vercel:

1. Import the repository in [Vercel](https://vercel.com/new).
2. Set the **Framework Preset** to **`Other`**.
3. Click **Deploy**. Vercel builds and deploys both the frontend single-page application and Python serverless API functions automatically.

---

## Automated Verification & Security Audit

AICTE ONE passes comprehensive automated security and regression test suites:

```
======================= 109 passed in 64.99s (100% PASS RATE) =======================
```

- **Authentication & Security (`tests/test_auth.py`):** Login, lockout protection, individual sessions, profile scoping, TOTP MFA, password recovery.
- **Database & Integrity (`tests/test_database_and_security.py`):** Password hashing, unique permanent IDs, security headers (HSTS, CSP, X-Frame-Options), audit trails.
- **Workflow Engine (`tests/test_workflow_engine.py`):** Configurable APH routes, illegal transition blocking, deficiency return and resubmission loops, idempotency.
- **EVC & Compliance (`tests/test_evc_and_compliance.py`):** EVC route validation, committee conflict-of-interest detection, report filing, undertaking lifecycle.
- **Institutions & Analytics (`tests/test_institutions_and_analytics.py`):** Permanent ID lookup, acronym expansion, non-hallucinating verification, 15 dashboard KPIs, 12 distribution graphs, CSV formula injection defense.
- **AI Copilot & OCR Intelligence (`tests/test_phase4_ai_and_documents.py`):** Multilingual prompt understanding (English/Hindi/Hinglish), prompt injection defense, file magic byte enforcement, duplicate document detection, human-in-the-loop review.
- **End-to-End Acceptance (`tests/test_phase5_security_and_acceptance.py`):** Complete acceptance criteria across all 5 implementation phases.

---

## Regulatory Grounding & Honest Data Integrity

AICTE ONE strictly adheres to statutory principles outlined in the **AICTE Act 1987** and the **AICTE Approval Process Handbook (APH 2026–27)**:

1. **Clear Provenance Distinction:** The platform distinguishes authentic government records from simulated demonstration cases via explicit badges (`AICTE Official Directory`, `Verified`, `Demonstration Record`).
2. **Deterministic Evidence Linking:** AI Copilot responses and scrutiny checklists are grounded in actual database records, citing specific Permanent IDs, application references, and APH rule sections.
3. **No Automated Adverse Actions:** Document extraction anomalies and OCR discrepancies are flagged for officer review and applicant rectification, never treated as conclusive proof of forgery without administrative inquiry.

---

## License & Attribution

Developed for the **Ministry of Education, Government of India** and the **All India Council for Technical Education (AICTE)** as an Enterprise Regulatory Platform for the Smart India Hackathon (SIH 2026) Initiative.
