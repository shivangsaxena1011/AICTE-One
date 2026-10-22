# AICTE ONE (SHANKH) — PHASE 1 AUDIT REPORT
**Platform:** AICTE ONE / Project SHANKH — Integrated Institutional Monitoring, Approval Verification, Complaint Management, Regulatory Compliance & Workflow Automation  
**Target Milestone:** Smart India Hackathon (SIH) 2026  
**Auditor / Roles:** Senior Full-Stack Engineer, Backend Architect, Database Engineer, Application Security Specialist  
**Document Path:** `docs/implementation/phase-1-audit.md`  
**Date:** October 2026  
**Security Status:** Remediation in Progress (Phase 1 Baseline)  

---

## 1. Executive Summary

This audit assesses the core foundation, security posture, database architecture, and backend service readiness of the **AICTE ONE (SHANKH)** platform. AICTE ONE is designed as a unified government-grade institutional governance and monitoring system serving eight primary stakeholder personas across the Ministry of Education and AICTE bureaus.

### Key Audit Findings:
1. **Critical Authentication Vulnerability (Broken Access Control & Spoofing):**
   - The original implementation lacked real password verification and individual session management.
   - Authentication relied on client-supplied HTTP headers (`X-Role` and `X-Actor`), defaulting to `ADMIN` (`admin@aicte-india.org`) when omitted.
   - Any unauthenticated client or script could execute administrative and disposal operations simply by supplying or omitting arbitrary headers.
   - In Settings, a client-side "Persona Switcher" stored selected roles in browser `localStorage`, granting instant simulated privileges without cryptographic tokens or server verification.

2. **Absence of Tenant and Case-Level Data Isolation:**
   - Institutional users (`INSTITUTION_USER` / Institute Principal) could query and view approval applications, compliance obligations, and complaints of all other institutions across India.
   - Students and complainants had no individual account association (`complainant_id` missing in the schema), creating risk of unauthorized viewing of confidential grievance notes, whistleblower records, or cross-student filings.

3. **Database Normalization & Security Gaps:**
   - The `User` table lacked password hashing (`password_hash`), multi-factor authentication (MFA) metadata, account lockouts, failed login tracking, and institutional foreign-key constraints.
   - Sessions, password reset tokens, and login history were nonexistent in the database schema.
   - Missing tables for explicit Role-Based Access Control (RBAC) definitions (`roles`, `permissions`, `role_permissions`).

4. **Public vs. Protected Boundaries Undefined:**
   - Public institutional directory searches and landing pages had no distinction from protected officer workflows in backend routing.
   - No rate limiting existed on critical endpoints (login, password reset, search).

5. **Secrets and Configuration Hygiene:**
   - Configuration relied on loose environment defaults (`SECRET_KEY=aicte-one-super-secret-governance-key-2024`, `CORS_ORIGINS=*`).
   - Static mock records in `seed_records.json` were mixed with runtime state without explicit environment separation.

---

## 2. Architecture & Technology Stack Inventory

| Component | Technology / Library | Current State | Target State (Phase 1) |
| :--- | :--- | :--- | :--- |
| **Backend Framework** | FastAPI (Python 3.12/3.14) + Uvicorn | Partially Implemented (Missing Auth Middleware) | Hardened FastAPI with Security Headers, Rate Limiting, Cookie/Bearer Auth |
| **Database Engine** | SQLite (Dev/Demo) / PostgreSQL (Prod) via SQLAlchemy 2.0 | Normalized core tables; missing Auth/RBAC/Session entities | Fully normalized relational schema with User/Role/Session/Token models |
| **Password Hashing** | Bcrypt (via passlib / native bcrypt) | Missing (Plaintext/None) | Bcrypt (cost factor 12) with salted individual passwords |
| **Session & Tokens** | Cryptographic JWT (HS256) + HttpOnly Cookies + Bearer Header | Missing (X-Role mock header spoofable) | Server-issued JWT, session revocation table, single-use reset tokens |
| **Frontend Architecture** | Vanilla ES6+ Modular SPA (Tailwind CSS, Plus Jakarta Sans, Inter) | Working modern UI; mock-driven role switching | Real API integration, individual login flow, tenant-filtered UI |
| **Hosting & Deployment** | Vercel Serverless (`api/index.py` ASGI handler) + Local Standalone | Functional routing; lacks secret isolation | Validated Vercel serverless + local standalone compatibility |

---

## 3. Prioritized Feature Inventory & Defect Classification

Features are classified into six rigorous engineering states:
- **Complete and verified**
- **Partially implemented**
- **Frontend-only or mock-driven**
- **Broken**
- **Missing**
- **Blocked by an unavailable external dependency**

---

### Category A: Identity, Authentication & Session Security

#### 1. Individual User Authentication & Password Verification
- **Classification:** Broken / Insecure.
- **Affected Files:** `backend/auth.py`, `backend/routes/institutions.py`, `backend/routes/complaints.py`, `assets/js/utils/api.js`.
- **Root Cause:** In the initial code, `get_current_user` in `backend/auth.py` inspected only `x_role` and `x_actor` HTTP headers, with a fallback default to `ROLE_ADMIN`. Password hashing was completely absent.
- **Required Changes:**
  1. Add `password_hash`, `failed_login_attempts`, `locked_until`, `mfa_enabled`, `mfa_secret`, and `institution_id` to `User` entity.
  2. Implement bcrypt password verification.
  3. Create `/api/auth/login`, `/api/auth/logout`, `/api/auth/me`, and `/api/auth/refresh` endpoints.
  4. Implement brute-force protection (lockout after 5 consecutive failures).
- **Risk:** Critical (CVSS 9.8). Total authentication bypass and administrative takeover.
- **Proposed Verification Test:** Submit login requests with invalid password, valid password, and verify that omitting tokens returns `401 Unauthorized`.

#### 2. Session Management & Invalidation
- **Classification:** Missing.
- **Affected Files:** `backend/models.py`, `backend/auth.py`, `backend/routes/auth.py`.
- **Root Cause:** No server-side session tracking or token revocation existed.
- **Required Changes:**
  1. Create `UserSession` table tracking active cryptographic tokens, device metadata, and expiration.
  2. Provide explicit server-side `/api/auth/logout` invalidation.
- **Risk:** High. Sessions could not be terminated upon logout.
- **Proposed Verification Test:** Test login, capture token, call `/api/auth/logout`, then verify token is rejected on subsequent requests.

#### 3. Password Recovery Flow
- **Classification:** Missing.
- **Affected Files:** `backend/models.py`, `backend/routes/auth.py`.
- **Root Cause:** No password reset token model or recovery workflow existed.
- **Required Changes:**
  1. Create `PasswordResetToken` table with single-use, time-limited cryptographic tokens (15-minute expiry).
  2. Add `/api/auth/password-reset-request` and `/api/auth/password-reset-confirm`.
- **Risk:** Medium. Users unable to recover compromised or lost credentials.
- **Proposed Verification Test:** Issue reset token, use it once, verify success; attempt replay and verify token is rejected.

#### 4. Role Switching on Login / Settings
- **Classification:** Broken / Insecure (Mock-Driven).
- **Affected Files:** `assets/js/modules/settings.js`, `assets/js/app.js`, `assets/js/utils/api.js`.
- **Root Cause:** `SettingsModule.switchRole` permitted client-side selection of `ADMIN`, `SCRUTINY_OFFICER`, etc., stored directly in `localStorage` without credential verification.
- **Required Changes:**
  1. Remove client-side role privilege escalation.
  2. Replace with real demonstration login quick-switcher that submits actual user credentials to `/api/auth/login`.
- **Risk:** Critical. Role picker directly bypassed backend security.
- **Proposed Verification Test:** Verify that selecting a persona in the UI triggers server authentication and rejects unauthenticated role assumption.

---

### Category B: Role-Based Access Control (RBAC) & Data Isolation

#### 5. Eight-Category Role Matrix Backend Enforcement
- **Classification:** Missing / Partially Implemented.
- **Affected Files:** `backend/auth.py`, `backend/routes/*.py`.
- **Root Cause:** Only `backend/routes/complaints.py:227` contained any role check, and it only checked the spoofable header. The other 11 route files had no role checks.
- **Required Changes:**
  1. Define explicit role categories:
     - `SUPER_ADMIN`
     - `SECURITY_OFFICER`
     - `COMPLIANCE_OFFICER`
     - `COMPLAINT_OFFICER`
     - `ANTI_RAGGING_OFFICER`
     - `INSTITUTE_HEAD`
     - `STUDENT_COMPLAINANT`
     - `PUBLIC_VISITOR`
  2. Create granular permissions system (`require_permission`, `require_role`).
  3. Enforce deny-by-default on all administrative and mutation operations.
- **Risk:** Critical. Broken Access Control (OWASP Top 10 #1).
- **Proposed Verification Test:** Execute test suite checking all 8 roles against restricted endpoints.

#### 6. Cross-Tenant / Institution Data Isolation (IDOR Prevention)
- **Classification:** Broken / Missing.
- **Affected Files:** `backend/routes/institutions.py`, `backend/routes/applications.py`, `backend/routes/compliance.py`, `backend/routes/documents.py`.
- **Root Cause:** Endpoints accepted queries without scoping to the caller's authorized `institution_id`.
- **Required Changes:**
  1. Add `check_tenant_access(user, institution_id)` dependency.
  2. Enforce query filters so `INSTITUTE_HEAD` cannot view or mutate other institutions' non-public records.
- **Risk:** High. Insecure Direct Object References (IDOR) leaking confidential financial, land, and approval filings.
- **Proposed Verification Test:** Attempt to access Institution B's detailed twin and applications using Institution A's token; verify `403 Forbidden`.

#### 7. Complainant & Anti-Ragging Investigation Isolation
- **Classification:** Missing / Partially Implemented.
- **Affected Files:** `backend/models.py`, `backend/routes/complaints.py`.
- **Root Cause:** Complaints lacked a `complainant_id` foreign key and confidentiality flags.
- **Required Changes:**
  1. Add `complainant_id`, `is_confidential`, and `ragging_flag` columns to `complaints`.
  2. Students can only view complaints where `complainant_id == user.id`.
  3. Anti-Ragging officers only view ragging/safety grievances unless explicitly delegated.
- **Risk:** High. Breach of student whistleblower confidentiality.
- **Proposed Verification Test:** Verify student cannot query complaints submitted by other students or internal officer resolution notes.

---

### Category C: Core API & Database Foundation

#### 8. Database Schema Normalization & Migrations
- **Classification:** Partially Implemented.
- **Affected Files:** `backend/models.py`, `backend/database.py`, `backend/seed.py`.
- **Root Cause:** Core tables (`institutions`, `applications`, `complaints`, `documents`) were defined, but user accounts, security roles, sessions, and recovery tables were absent from the ORM models and seeder.
- **Required Changes:**
  1. Add `User`, `Role`, `Permission`, `RolePermission`, `UserSession`, `PasswordResetToken`, and `LoginHistory` ORM entities.
  2. Add foreign keys and indices for `institution_id`, `complainant_id`, `status`, and timestamps.
  3. Implement safe database migration / upgrade routine in `database.py`.
- **Risk:** High. System cannot store individual credentials or audit access.
- **Proposed Verification Test:** Verify database schema creation and ensure existing records in `aicte_one.db` are preserved.

#### 9. Public Institution Directory & Public Search
- **Classification:** Complete and Verified.
- **Affected Files:** `backend/routes/institutions.py`, `index.html`.
- **Root Cause:** Public directory endpoint `/api/institutions` works well for unauthenticated users, supporting query filters by name, state, category, and approval status.
- **Required Changes:** Ensure public search remains open to unauthenticated visitors (`PUBLIC_VISITOR`) while protecting sensitive internal fields.
- **Risk:** Low.
- **Proposed Verification Test:** Call `GET /api/institutions?q=Technology` without credentials and verify `200 OK`.

#### 10. Audit Logging & Security Event Recording
- **Classification:** Partially Implemented.
- **Affected Files:** `backend/routes/audit.py`, `backend/models.py`.
- **Root Cause:** `AuditLog` table recorded some manual actions, but failed to log logins, password resets, authorization failures, or IP addresses.
- **Required Changes:**
  1. Integrate audit logging into authentication events (login, logout, lockout).
  2. Restrict `GET /api/audit` to `SUPER_ADMIN` and `SECURITY_OFFICER`.
- **Risk:** Medium. Inability to trace security incidents or insider threats.
- **Proposed Verification Test:** Trigger failed login and verify corresponding audit record is written.

---

### Category D: External Dependencies & Advanced Modules

#### 11. AI Governance Copilot & Regulatory Graph
- **Classification:** Partially Implemented (Deterministic fallback active; Gemini live call optional).
- **Affected Files:** `backend/routes/copilot.py`, `backend/services/copilot_service.py`, `backend/routes/graph.py`.
- **Root Cause:** Copilot works deterministically using built-in APH rules knowledge base; live LLM generation depends on `GEMINI_API_KEY`.
- **Status:** Functional fallback verified; live external API is optional and gracefully degraded if key is omitted.
- **Risk:** Low. Deterministic rules engine ensures 100% test pass without external cloud keys.

#### 12. Digilocker & NAD Sandbox Integration
- **Classification:** Blocked by Unavailable External Dependency / Simulated.
- **Affected Files:** `backend/services/verification_adapter.py`, `backend/routes/documents.py`.
- **Root Cause:** Official DigiLocker/NAD production API requires government bureau-issued client credentials and IP whitelisting.
- **Status:** Clean simulation adapter provided; external live call blocked by external agency SLA.

---

## 4. Security Vulnerability Matrix (Baseline Audit)

| Vulnerability ID | Vulnerability Category | Severity | Root Cause | Remediated in Phase 1? |
| :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | Broken Authentication | **Critical** | Insecure `X-Role` header assumption; no passwords | **Yes (Bcrypt + Sessions + Auth API)** |
| **SEC-02** | Broken Access Control / IDOR | **Critical** | Missing authorization middleware on routes | **Yes (RBAC + Tenant Isolation Guard)** |
| **SEC-03** | Privilege Escalation | **High** | Client-side role switcher in UI | **Yes (Server-derived permissions only)** |
| **SEC-04** | Missing Brute Force Protection | **Medium** | No rate limiting or lockout on login attempts | **Yes (Account lockout + failed counter)** |
| **SEC-05** | Lack of Cross-Tenant Isolation | **High** | Institutional users could view any institution's twin | **Yes (Institution-scoped filtering)** |
| **SEC-06** | Insecure Security Headers | **Medium** | Missing CSP, HSTS, X-Frame-Options, X-Content-Type | **Yes (Security Headers Middleware)** |
| **SEC-07** | Permissive CORS Configuration | **Medium** | `CORS_ORIGINS=*` allowed arbitrary web origins | **Yes (Scoped origin controls)** |

---

## 5. Phase 1 Remediation Plan & Execution Steps

1. **Step 1:** Extend database models (`backend/models.py`) with `User`, `Role`, `Permission`, `RolePermission`, `UserSession`, `PasswordResetToken`, and `LoginHistory`. Update `Complaint` and `Document` for isolation.
2. **Step 2:** Implement hardened security and auth service (`backend/auth.py`) with bcrypt password hashing, JWT generation, session tracking, permission verification, and tenant isolation dependencies.
3. **Step 3:** Implement complete authentication routes (`backend/routes/auth.py`) supporting login, logout, me, refresh, password reset, and MFA verification.
4. **Step 4:** Seed standard roles, permissions, and 8 individual user accounts in `backend/seed.py` with individual bcrypt-hashed passwords.
5. **Step 5:** Protect all backend routes (`backend/routes/*.py`) with granular role/permission checks and tenant isolation.
6. **Step 6:** Add Security Headers middleware, rate limiting, and CORS restrictions to `backend/main.py`.
7. **Step 7:** Update frontend API bridge (`assets/js/utils/api.js`) and UI (`index.html`, `assets/js/app.js`, `assets/js/modules/settings.js`) to support real authentication, token headers, login modal, and public browsing.
8. **Step 8:** Develop automated test suite (`tests/test_auth.py`, `tests/test_rbac_and_isolation.py`, `tests/test_database_and_security.py`) validating all 8 role categories, direct bypass prevention, and data isolation.
9. **Step 9:** Execute test suite, verify 100% pass rate (30/30 tests passed), and document Phase 1 deliverables and remaining Phase 2 roadmap.

---

## 6. Documented Statutory Permission Matrix

The platform enforces a granular permission model across the eight statutory user categories:

| Statutory Role | Code | Permitted Operations | Restricted / Prohibited Operations |
| :--- | :--- | :--- | :--- |
| **Super Administrator** | `SUPER_ADMIN` | `*` (Full System Oversight: User & Role Management, System Configuration, Cross-Bureau Actions, Audit Log View & Export) | Cannot bypass audit logging; destructive migrations prohibited |
| **Security Officer** | `SECURITY_OFFICER` | `security:view`, `security:manage`, `audit:view`, `audit:export`, `document:view_all`, `document:verify`, `institution:view_all`, `complaint:view_all`, `task:view`, `task:manage` | Cannot grant role promotions or alter system configuration without recorded administrative reason |
| **Policy & Compliance Officer** | `POLICY_COMPLIANCE_OFFICER` | `compliance:view_all`, `compliance:review`, `compliance:manage`, `institution:view_all`, `application:view_all`, `document:view_all`, `task:view`, `task:manage`, `audit:view` | Cannot close or dispose vigilance/complaint cases |
| **Complaint & Vigilance Officer** | `COMPLAINT_OFFICER` | `complaint:view_all`, `complaint:manage`, `complaint:transfer`, `complaint:dispose`, `complaint:link`, `institution:view_all`, `task:view`, `task:manage`, `audit:view` | Cannot grant institutional approvals or review compliance filings |
| **Anti-Ragging Committee** | `ANTI_RAGGING_OFFICER` | `complaint:view_ragging`, `complaint:manage_ragging`, `complaint:hearing`, `institution:view_all`, `task:view`, `task:manage`, `audit:view` | Restricted strictly to ragging/harassment cases; cannot view unrelated commercial/land filings |
| **Institute Principal / Head** | `INSTITUTE_HEAD` | `institution:view_own`, `institution:edit_own`, `application:view_own`, `application:submit`, `compliance:view_own`, `compliance:submit`, `document:view_own`, `document:upload`, `complaint:view_own`, `task:view` | **Strictly Tenant-Isolated.** Cannot view or mutate another institution's applications, compliance, or digital twin (`403 Forbidden`) |
| **Student / Complainant** | `STUDENT_COMPLAINANT` | `complaint:submit`, `complaint:view_own`, `document:upload`, `institution:view_public` | **Whistleblower Isolated.** Cannot view internal officer notes, other students' filings, or officer dashboards (`403 Forbidden`) |
| **Public Visitor** | `PUBLIC_VISITOR` | `institution:view_public`, `report:view_public`, `health:view` | Anonymous. Cannot access any internal application, complaint, task, or audit route (`401/403 Forbidden`) |

---

## 7. Automated Test Results (Phase 1 Baseline)

Test execution executed using `pytest` against an isolated in-memory relational database:

```
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
collected 30 items

tests/test_auth.py::test_login_success PASSED                            [  3%]
tests/test_auth.py::test_login_failure_invalid_credentials PASSED        [  6%]
tests/test_auth.py::test_login_failure_nonexistent_user PASSED           [ 10%]
tests/test_auth.py::test_account_lockout_protection PASSED               [ 13%]
tests/test_auth.py::test_authenticated_profile_endpoint PASSED           [ 16%]
tests/test_auth.py::test_unauthenticated_request_rejected PASSED         [ 20%]
tests/test_auth.py::test_spoofed_headers_rejected PASSED                 [ 23%]
tests/test_auth.py::test_logout_session_invalidation PASSED              [ 26%]
tests/test_auth.py::test_password_recovery_flow PASSED                   [ 30%]
tests/test_auth.py::test_privileged_mfa_verification PASSED              [ 33%]
tests/test_database_and_security.py::test_passwords_are_hashed_never_plaintext PASSED [ 36%]
tests/test_database_and_security.py::test_user_unique_constraints PASSED [ 40%]
tests/test_database_and_security.py::test_institution_unique_permanent_id PASSED [ 43%]
tests/test_database_and_security.py::test_security_headers_present PASSED [ 46%]
tests/test_database_and_security.py::test_audit_trail_recorded_on_sensitive_action PASSED [ 50%]
tests/test_database_and_security.py::test_system_health_check PASSED     [ 53%]
tests/test_rbac_and_isolation.py::test_public_visitor_can_search_institutions PASSED [ 56%]
tests/test_rbac_and_isolation.py::test_public_visitor_denied_internal_applications PASSED [ 60%]
tests/test_rbac_and_isolation.py::test_public_visitor_denied_audit_logs PASSED [ 63%]
tests/test_rbac_and_isolation.py::test_public_visitor_denied_complaint_registry PASSED [ 66%]
tests/test_rbac_and_isolation.py::test_student_can_lodge_and_view_own_complaint_only PASSED [ 70%]
tests/test_rbac_and_isolation.py::test_student_cannot_access_internal_officer_dashboards PASSED [ 73%]
tests/test_rbac_and_isolation.py::test_institute_head_can_access_own_institution PASSED [ 76%]
tests/test_rbac_and_isolation.py::test_institute_head_cross_tenant_access_denied PASSED [ 80%]
tests/test_rbac_and_isolation.py::test_institute_head_cannot_access_other_institutions_applications PASSED [ 83%]
tests/test_rbac_and_isolation.py::test_institute_head_cannot_create_institution_or_access_audit PASSED [ 86%]
tests/test_rbac_and_isolation.py::test_anti_ragging_officer_ragging_cases PASSED [ 90%]
tests/test_rbac_and_isolation.py::test_complaint_officer_can_transfer_and_dispose PASSED [ 93%]
tests/test_rbac_and_isolation.py::test_compliance_officer_create_and_review PASSED [ 96%]
tests/test_rbac_and_isolation.py::test_superadmin_full_access PASSED     [100%]

============================= 30 passed in 15.79s =============================
```

**Result:** **30 passed, 0 failed (100% pass rate).**

---

## 8. Unresolved External Dependencies & Phase 2 Readiness

| Dependency / Integration | Current Status | Blocker / SLA Requirement | Planned for Phase |
| :--- | :--- | :--- | :--- |
| **DigiLocker / NAD API Gateway** | High-fidelity simulated adapter | Awaiting official production API credentials and static IP whitelisting from the National Informatics Centre (NIC) | Phase 2 |
| **Land Geo-Coordinate Satellite Verification (Bhuvan/ISRO)** | Simulated geo-fencing | Awaiting Bhuvan/ISRO spatial API token agreement | Phase 2 |
| **Live SMS/Email OTP Gateway** | In-app token & PIN delivery | Production SMS gateway provider (e.g. CDAC/NIC SMS) setup pending | Phase 2 |
| **Live AI Copilot (Gemini API)** | Deterministic heuristic rules engine active; live LLM enabled when `GEMINI_API_KEY` set | Optional API key configuration; zero degradation when unset | Production Ready |

### Readiness Status:
- **Core Security Baseline:** **VERIFIED**
- **Authentication & Sessions:** **VERIFIED**
- **Role-Based Access Control:** **VERIFIED**
- **Multi-Tenant Isolation:** **VERIFIED**
- **Database Normalization & Seed:** **VERIFIED**
- **Automated Regression Suite:** **VERIFIED (30/30 Tests Passing)**
- **Overall Readiness:** **Ready to proceed to Phase 2 (Deep Workflow Engine & Evidence Verification Pipeline)**
