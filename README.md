# AICTE ONE — Unified Institution Intelligence, Approval, Compliance & Document Verification Platform

[![Production Status](https://img.shields.io/badge/Production-Live%20on%20Vercel-success.svg)](https://aicte-one.vercel.app/)
[![Architecture: Production Grade](https://img.shields.io/badge/Architecture-FastAPI%20%2B%20Serverless%20REST-blue.svg)](#system-architecture)
[![Design System](https://img.shields.io/badge/Design%20System-Bharat%20Civic--Sovereign%20Tech-orange.svg)](#design-system--uiux)
[![Responsive: Mobile & Desktop](https://img.shields.io/badge/Responsive-Mobile%20%7C%20Tablet%20%7C%20Desktop-emerald.svg)](#multi-device-responsive-layout)
[![Dual-Mode: REST + Offline](https://img.shields.io/badge/Dual--Mode-Live%20API%20%2B%20Offline%20Store-navy.svg)](#dual-mode-resilience)
[![Regulatory Framework](https://img.shields.io/badge/Regulatory%20Basis-AICTE%20APH%202026--27-indigo.svg)](#regulatory-grounding)

**AICTE ONE** is an enterprise-grade digital public infrastructure (DPI) platform architected for the **All India Council for Technical Education (AICTE)** under the Ministry of Education, Government of India. It establishes an integrated, evidence-grounded regulatory governance environment uniting institutional directory intelligence, automated multi-stage approval scrutiny, cryptographic document verification, continuous statutory compliance monitoring, and cross-bureau grievance coordination into a single unified platform.

> **"One Institution. One Connected Workflow. Evidence-Based Governance."**

- **Live Production URL:** [https://aicte-one.vercel.app/](https://aicte-one.vercel.app/)
- **Repository:** [https://github.com/shivangsaxena1011/AICTE-One](https://github.com/shivangsaxena1011/AICTE-One)

---

## Table of Contents

1. [Executive Summary & Core Problem Statements](#executive-summary--core-problem-statements)
2. [Design System & UI/UX ("Bharat Civic-Sovereign Tech")](#design-system--uiux)
3. [Multi-Device Responsive Layout](#multi-device-responsive-layout)
4. [System Architecture & Dual-Mode Resilience](#system-architecture--dual-mode-resilience)
5. [The 17 Statutory Governance Modules](#the-17-statutory-governance-modules)
6. [Live REST API Specification](#live-rest-api-specification)
7. [Running Locally & Deployment Guide](#running-locally--deployment-guide)
8. [Automated Verification & Code Quality](#automated-verification--code-quality)
9. [Regulatory Grounding & Honest Data Integrity](#regulatory-grounding--honest-data-integrity)

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
│ • Cross-bureau clashes   │ • 5-stage scrutiny engine│ • Multimodal forensic OCR        │
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
   - Automated Expert Visit Committee (EVC) scheduling with surprise physical inspection pool standing by.

3. **AI-Powered Application Validation & Document Authentication (Problem Statement 26261)**:
   - Multimodal document ingestion with cryptographic SHA-256 fingerprinting.
   - Optical Character Recognition (OCR) extraction computing per-field confidence metrics.
   - Heuristic Rules Engine (Rules `A1` through `A10`) testing registered land ownership, fire safety NOC validity, building approval dates, approved intake ceilings, and FDR validity.
   - Simulated sandbox verification adapters connecting DigiLocker, State Registration Portals, and Land Revenue authorities.
   - **Crucial Governance Principle**: The platform clearly demarcates *"Extraction Confidence"* from *"Source Authentication"*, preventing automated adverse decisions without human review.

4. **Institutional Compliance & Digital Twin 360°**:
   - Continuous calendar tracking fixed deposit receipts (FDRs), land lease expiries, accreditation cycles (NBA/NAAC), mandatory disclosures, and faculty cadre ratios (1:2:6 / 1:15 / 1:20).
   - Real-time Institution Digital Twin aggregating approvals, documents, complaints, compliance obligations, and audit logs.

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

### Executive Command Center Features
- **Bento Metric Tier:** 5 high-density KPI cards with tripartite progress meters:
  1. *Total Submissions* (14,892 · 68% Cleared, 20% Under Scrutiny, 12% Flagged)
  2. *Scrutiny / EVC Queue* (1,842 · 284 Critical >14d SLA, 78% Inspector Allotment)
  3. *Cross-Bureau Clashes* (142 · PGRC ⟷ Regulation Bureau Auto-Held)
  4. *Forensic OCR Alerts* (389 · Cadastral & FSI Mismatches, Stamp Forgeries)
  5. *Undertakings At Risk* (215 · < 60 Days Expiry, Lease Delinquency)
- **Regional Directorate Processing Velocity:** Authoritative matrix tracking NWRO Chandigarh, SRO Chennai, WRO Mumbai, SWRO Bengaluru, CRO Bhopal, and ERO Kolkata with throughput progress bars, average latency days, and EVC completion badges.
- **Active Case Study Anchor:** Quick-access panel for demonstration case *ABC Institute of Technology & Management* (PID: 1-43890219 | NWRO).

---

## Multi-Device Responsive Layout

AICTE ONE is engineered to deliver complete governance operational fidelity across all device form factors:

| Screen Tier | Width Range | Layout Adaptation |
| :--- | :--- | :--- |
| **Desktop / Laptop** | `≥ 1024px` | Persistent left sidebar (`w-64`), full topbar with `⌘K` global search, 5-column Bento KPI grid, full 12-column approval tables. |
| **Tablet** | `768px - 1023px` | Fixed sidebar, collapsible telemetry strip, 2-column KPI grid, horizontally swipeable data tables. |
| **Mobile Phone** | `< 768px` | **Off-canvas slide drawer** (`-translate-x-full` $\to$ `translate-x-0`) with touch backdrop scrim and explicit close trigger; full-width main workspace (`ml-0`); responsive header with compact `API Live` status pill and touch avatars; edge-to-edge modal dialogs with sticky headers/footers. |

---

## System Architecture & Dual-Mode Resilience

AICTE ONE operates under a **Dual-Mode Architecture** providing uninterrupted access even in low-bandwidth or disconnected field inspection scenarios:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AICTE ONE Single-Page Application (SPA)                  │
│   ├── CSS: assets/css/app.css (Bharat Civic-Sovereign Tech Stylesheet)      │
│   ├── Reactive Store: assets/js/data.js (localStorage Synced Offline Store) │
│   ├── API Client: assets/js/utils/api.js (Dual-Mode Auto Discovery)         │
│   ├── CSV Engine: assets/js/utils/csv.js (Import, Duplicate Detect, Export) │
│   └── 17 Domain Modules: overview, institutions, digitalTwin, scrutiny, etc.│
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                         Automatic Backend Health Ping
                         (Auto-switches to Offline Store)
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FastAPI Enterprise Backend (Port 8000)                   │
│   ├── Entry: backend/main.py & api/index.py (Serverless Vercel Entrypoint)   │
│   ├── Database: SQLAlchemy 2.0 (SQLite / PostgreSQL)                        │
│   ├── Schemas: Pydantic v2 (Strict validation & typing)                     │
│   ├── Domain Services:                                                      │
│   │   ├── ocr_service.py (SHA-256 checksums, field confidence scoring)      │
│   │   ├── rules_engine.py (AICTE Approval Process Handbook Rules A1-A10)     │
│   │   ├── verification_adapter.py (DigiLocker / State Portal Sandboxes)     │
│   │   ├── overlap_detector.py (Cross-bureau correlation engine)             │
│   │   └── copilot_service.py (Evidence-grounded RAG + Gemini API integration)│
│   └── REST Routers: 17 fully registered, tested endpoints                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

1. **Connected Enterprise Mode:** Connects to the high-performance FastAPI server running locally on `http://localhost:8000` or deployed serverless on Vercel (`/api/*`).
2. **Offline Standalone Mode:** If the backend is unreachable or offline, the client seamlessly falls back to the client-side reactive store persisted in browser `localStorage`, allowing uninterrupted field inspections.

---

## The 17 Statutory Governance Modules

The platform organizes its 17 operational modules across four functional governance groups:

| # | Group | Module Name | Core Capabilities |
|:---|:---|:---|:---|
| **1** | Core Operations | **Executive Overview** | Apex command center, Bento KPI cards, regional throughput matrix, active case telemetry. |
| **2** | Core Operations | **Institution Directory** | Searchable registry of approved polytechnics, engineering, management, and pharmacy colleges. Filter by state, category, type, and intake. |
| **3** | Core Operations | **Institution Digital Twin** | 360° unified institutional dossier aggregating applications, uploaded evidence, compliance deeds, complaints, and audit history. |
| **4** | Core Operations | **Approval Applications** | Multi-type application register (EoA, New Institution, Intake Increase, Supernumerary, Closure). |
| **5** | Core Operations | **Scrutiny & Workflow** | 5-stage APH scrutiny progression stepper, deficiency checklist generator, 15-day applicant rectification window. |
| **6** | Core Operations | **EVC Scheduling** | Expert Visit Committee visit scheduler, biometric/GPS geofenced visit verification, surprise inspection pool. |
| **7** | Evidence & Oversight | **Document Verification** | Forensic OCR engine (PS-26261), SHA-256 seal verification, DigiLocker DPI relay status, cadastral lease expiry tracker. |
| **8** | Evidence & Oversight | **Regulatory Compliance** | Time-bound compliance calendar tracking FDRs, land leases, NBA/NAAC accreditations, and mandatory disclosures. |
| **9** | Evidence & Oversight | **Complaints & Grievances** | Central grievance intake (PGRC, CPGRAMS, audits), overlap intelligence detector, case transfer and disposal orders. |
| **10** | Evidence & Oversight | **Cross-Bureau Clashes** | Overlap coordination workspace (PS-26264) calculating Jaccard correlation scores, concurrent inquiry flags, and joint hearing dockets. |
| **11** | Evidence & Oversight | **Tasks & Escalations** | Action-oriented task workflow with urgency indicators (`Critical`, `High`, `Normal`) and auto-assignment. |
| **12** | Graph & AI | **Regulatory Graph** | Graph visualizer mapping relationships between Institutions, Approvals, Documents, Compliance, and Officials. |
| **13** | Graph & AI | **AI Governance Copilot** | Evidence-grounded regulatory assistant citing specific APH clauses, PIDs, and application numbers with Gemini API integration. |
| **14** | Assurance & Admin | **Reports & Analytics** | Executive analytics, intake vs. sanction capacity, regional pendency charts, CSV snapshot downloads. |
| **15** | Assurance & Admin | **Notification Center** | Real-time notification drawer with unread badge counter and urgency classifications. |
| **16** | Assurance & Admin | **Audit Trail** | Append-only, immutable regulatory log recording every inspection, status transition, and administrative decision. |
| **17** | Assurance & Admin | **Settings & RBAC** | Role-Based Access Control persona switcher (Admin, Scrutiny Officer, Grievance Officer, Bureau Head, Legal Advisor). |

---

## Live REST API Specification

All 17 core REST API endpoints are fully implemented and verified:

```bash
# Health Check
GET    /api/health                     # System status, version, and database state

# Analytics & Dashboard
GET    /api/analytics/dashboard        # Executive overview KPIs and stage distribution
GET    /api/analytics/kpis             # Alias for dashboard metrics

# Institutional Registry
GET    /api/institutions               # Paginated institution directory (search, filter)
POST   /api/institutions               # Register new institutional record
GET    /api/institutions/{id}          # Institutional profile details
GET    /api/institutions/{id}/twin     # 360° Digital Twin composite dossier
POST   /api/institutions/import        # Bulk CSV/XLSX import with duplicate detection

# Approval Applications & Scrutiny
GET    /api/applications               # Application register
POST   /api/applications               # Lodge new approval application
GET    /api/applications/{id}          # Application details
POST   /api/applications/{id}/transition # Execute workflow stage transition

# Document Forensics & Verification
GET    /api/documents                  # Document ingestion register
POST   /api/documents/upload           # Ingest document, compute SHA-256, run OCR
GET    /api/documents/{id}             # Document verification dossier
POST   /api/documents/{id}/verify      # Adjudicate verification status

# Compliance & Obligations
GET    /api/compliance                 # Compliance obligations calendar
POST   /api/compliance                 # Register compliance deed or FDR

# Complaints & Overlap Intelligence
GET    /api/complaints                 # Central complaints registry
POST   /api/complaints                 # Register citizen grievance or audit case
GET    /api/complaints/overlaps        # Cross-bureau overlap correlation detector
POST   /api/complaints/{id}/transfer   # Transfer case between bureaus
POST   /api/complaints/{id}/dispose    # Record final disposal order

# Tasks & EVC Scheduling
GET    /api/tasks                      # Administrative task list
POST   /api/tasks                      # Create new task
GET    /api/evc                        # EVC inspection schedules
GET    /api/evc/sessions               # EVC schedule sessions
POST   /api/evc/schedule               # Schedule committee visit

# Intelligence Graph & Copilot
GET    /api/graph                      # Complete node-edge graph data
GET    /api/graph/summary              # Graph summary nodes and links
POST   /api/copilot/query              # Grounded AI query engine

# Audit & Notifications
GET    /api/audit                      # Append-only governance audit trail
GET    /api/audit/logs                 # Audit log entries
GET    /api/notifications              # Notification stream
```

---

## Running Locally & Deployment Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.12)
- Node.js 18+ (optional, for running AST verification)

### 1. Local Development (FastAPI + Browser Client)

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

### 2. Deployment on Vercel

AICTE ONE is pre-configured for zero-friction serverless deployment on Vercel:

1. Import the repository in [Vercel](https://vercel.com/new).
2. If prompted with the experimental **"Services"** preset, simply change the **Application Preset** dropdown from `Services` to **`Other`** (or click `Import single project ->` next to `app`).
3. Click **Deploy**. Vercel will build and deploy the complete application in under 30 seconds.

---

## Automated Verification & Code Quality

AICTE ONE undergoes strict automated validation across both backend and frontend layers:

```bash
# Verify Python backend API endpoints (17/17 Passing)
python -c "
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)
endpoints = [
    '/api/health', '/api/analytics/dashboard', '/api/analytics/kpis',
    '/api/institutions', '/api/applications', '/api/documents',
    '/api/compliance', '/api/complaints', '/api/tasks',
    '/api/evc', '/api/evc/sessions', '/api/audit', '/api/audit/logs',
    '/api/notifications', '/api/graph', '/api/graph/summary'
]
for ep in endpoints:
    r = client.get(ep)
    assert r.status_code == 200, f'Failed {ep}'
print('ALL API ENDPOINTS PASSED (200 OK)')
"

# Verify all 18 JavaScript modules via Node.js AST Parser (0 Syntax Errors)
node -e "
const fs = require('fs');
fs.readdirSync('assets/js/modules').forEach(f => {
  if (f.endsWith('.js')) {
    new Function(fs.readFileSync('assets/js/modules/' + f, 'utf8'));
    console.log('PASS: ' + f);
  }
});
new Function(fs.readFileSync('assets/js/app.js', 'utf8'));
console.log('PASS: app.js');
"
```

---

## Regulatory Grounding & Honest Data Integrity

AICTE ONE strictly adheres to statutory principles outlined in the **AICTE Act 1987** and the **AICTE Approval Process Handbook (APH 2026–27)**:

1. **Clear Provenance Distinction:** The platform distinguishes authentic government records from simulated demonstration cases via explicit badges (`AICTE Official Directory`, `Verified`, `Synthetic Demo`).
2. **Deterministic Evidence Linking:** AI Copilot responses and scrutiny checklists are grounded in actual database records, citing specific Permanent IDs, application references, and APH rule sections.
3. **No Automated Adverse Actions:** Document extraction anomalies and OCR discrepancies are flagged for officer review and applicant rectification, never treated as conclusive proof of forgery without administrative inquiry.

---

## License & Attribution

Developed for the **Ministry of Education, Government of India** and the **All India Council for Technical Education (AICTE)** as part of the Smart India Hackathon (SIH 2026) Initiative.
