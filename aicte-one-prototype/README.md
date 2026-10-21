# AICTE ONE — Working Prototype

A polished, responsive, browser-based prototype of **AICTE ONE: Unified Institution Intelligence, Approval, Compliance & Document Verification Platform**.

## Run it

**Fastest:** unzip the package and open `index.html` in a modern browser (Chrome, Edge, Firefox, Safari). No installation, account, server, or internet connection is required.

**Optional local server** (recommended if your browser restricts local file behavior):

```bash
python -m http.server 8000
```

Then open http://localhost:8000/aicte-one-prototype/ if launched from the parent directory, or http://localhost:8000 if launched inside this folder.

## Included modules

- Overview dashboard and priority alerts
- Institution registry and Institution Digital Twin profiles
- Approval workflow register with editable stage, owner, due date, status, and progress
- Document intelligence queue, review findings, and upload metadata capture
- Compliance obligations, evidence references, and deadline status tracking
- Complaint registry and cross-Bureau relationship review / coordination linking
- Rule-based demo copilot that summarizes local synthetic records
- Reports and CSV / JSON exports
- Audit trail of actions made in the prototype
- Workspace settings and demo-data reset
- Responsive desktop/mobile navigation
- Local persistence through browser `localStorage`

## Try these flows

1. Open **Approval workflows → New application** and add an application.
2. Open an application row, update the stage/status/owner, and save. Check **Audit trail**.
3. Open **Document intelligence → Verify document** to add a review record and optional filename metadata. Inspect the record and change its review state.
4. Open **Complaint intelligence** and review the suggested relationship between `PGRC-26-01842` and `RB-26-00917`. Confirming it preserves both separate case IDs.
5. Open **AI copilot** and ask “Summarize ABC Institute of Technology” or “Which compliance deadlines need attention?”
6. Export a dataset from **Reports & analytics** or export a full JSON backup from the header/settings.

## Important prototype boundaries

This package is a functional **front-end prototype**, not a production-certified government application. It uses fictional sample records and browser-local storage. It does not connect to AICTE systems, a backend database, real authentication, official APH/regulatory rule sources, external issuing-authority verification, OCR/LLM services, background schedulers, email/SMS notifications, or tamper-proof audit storage. Uploaded files are not sent to a server or truly processed; only metadata / filenames are recorded. The copilot is rule-based and operates on the local demo records. “Verified (demo)” is explicitly not official authentication.

Before a real deployment, implement a secured backend, approved identity provider, server-enforced role-based permissions, PostgreSQL, private document storage, official authorized integrations, OCR and source-grounded AI services, scheduled jobs, observability, privacy/retention controls, security testing, and append-only audit infrastructure. Regulatory decisions must remain with competent human authorities.

All sample institutions and records are fictional placeholders for demonstration.
