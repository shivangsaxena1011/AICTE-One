-- AICTE ONE: Unified Institution Intelligence, Approval, Compliance & Document Verification Platform
-- Relational Database Schema (ANSI SQL / SQLite / PostgreSQL compatible)

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    department VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS institutions (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    permanent_id VARCHAR(50) UNIQUE NOT NULL,
    state VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    address TEXT,
    category VARCHAR(100) NOT NULL,
    institution_type VARCHAR(100) NOT NULL,
    affiliation VARCHAR(255),
    website VARCHAR(255),
    approval_status VARCHAR(50) NOT NULL DEFAULT 'Approved',
    approval_period VARCHAR(50) DEFAULT '2026-2027',
    programmes_count INTEGER DEFAULT 0,
    total_intake INTEGER DEFAULT 0,
    data_source VARCHAR(100) DEFAULT 'Official AICTE Directory',
    verified_status VARCHAR(50) DEFAULT 'Verified',
    last_verified DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS applications (
    id VARCHAR(50) PRIMARY KEY,
    institution_id VARCHAR(50) NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    type VARCHAR(100) NOT NULL,
    academic_year VARCHAR(50) DEFAULT '2026-2027',
    current_stage VARCHAR(100) NOT NULL DEFAULT 'Preliminary validation',
    status VARCHAR(50) NOT NULL DEFAULT 'New submission',
    owner VARCHAR(100) DEFAULT 'Unassigned',
    progress INTEGER DEFAULT 10,
    submitted_at DATE DEFAULT CURRENT_DATE,
    due_date DATE,
    deficiency_count INTEGER DEFAULT 0,
    last_action TEXT,
    next_action TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS application_stages (
    id VARCHAR(50) PRIMARY KEY,
    application_id VARCHAR(50) NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    stage_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    actor VARCHAR(100) NOT NULL,
    remarks TEXT,
    deficiencies TEXT,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evc_schedules (
    id VARCHAR(50) PRIMARY KEY,
    application_id VARCHAR(50) NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    institution_id VARCHAR(50) NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    visit_type VARCHAR(50) DEFAULT 'Physical Visit',
    scheduled_date DATE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Scheduled',
    committee_chair VARCHAR(100) NOT NULL,
    committee_members TEXT,
    report_submitted BOOLEAN DEFAULT FALSE,
    observations TEXT,
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(50) PRIMARY KEY,
    institution_id VARCHAR(50) NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    application_id VARCHAR(50) REFERENCES applications(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    document_type VARCHAR(100) NOT NULL,
    file_path VARCHAR(255),
    file_size INTEGER DEFAULT 0,
    file_hash VARCHAR(100),
    uploaded_at DATE DEFAULT CURRENT_DATE,
    status VARCHAR(50) NOT NULL DEFAULT 'Verification pending',
    confidence VARCHAR(20) DEFAULT 'Not processed',
    extracted_fields TEXT,
    findings TEXT,
    issuing_authority VARCHAR(255),
    authority_ref VARCHAR(100),
    verification_source VARCHAR(100) DEFAULT 'Not verified',
    verification_response TEXT,
    is_anomaly BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS compliance_obligations (
    id VARCHAR(50) PRIMARY KEY,
    institution_id VARCHAR(50) NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    due_date DATE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Upcoming',
    responsible_party VARCHAR(100) DEFAULT 'Institution',
    evidence_file VARCHAR(255),
    review_notes TEXT,
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS complaints (
    id VARCHAR(50) PRIMARY KEY,
    institution_id VARCHAR(50) NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    case_number VARCHAR(100),
    bureau VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,
    summary TEXT NOT NULL,
    details TEXT,
    channel VARCHAR(100) DEFAULT 'Online Portal',
    status VARCHAR(50) NOT NULL DEFAULT 'Received',
    assigned_to VARCHAR(100) DEFAULT 'Unassigned',
    received_date DATE DEFAULT CURRENT_DATE,
    due_date DATE,
    related_case_id VARCHAR(50),
    overlap_score INTEGER DEFAULT 0,
    overlap_reason TEXT,
    resolution_notes TEXT,
    closed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS coordination_links (
    id VARCHAR(50) PRIMARY KEY,
    case_a_id VARCHAR(50) NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
    case_b_id VARCHAR(50) NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'Proposed',
    confidence_score INTEGER NOT NULL DEFAULT 85,
    matching_factors TEXT,
    rationale TEXT,
    coordinating_bureau VARCHAR(100),
    coordinating_officer VARCHAR(100),
    confirmed_by VARCHAR(100),
    confirmed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    priority VARCHAR(50) NOT NULL DEFAULT 'Medium',
    status VARCHAR(50) NOT NULL DEFAULT 'Pending',
    due_date DATE,
    assigned_to VARCHAR(100) NOT NULL,
    bureau VARCHAR(100) NOT NULL,
    institution_id VARCHAR(50) REFERENCES institutions(id) ON DELETE CASCADE,
    application_id VARCHAR(50) REFERENCES applications(id) ON DELETE SET NULL,
    complaint_id VARCHAR(50) REFERENCES complaints(id) ON DELETE SET NULL,
    document_id VARCHAR(50) REFERENCES documents(id) ON DELETE SET NULL,
    obligation_id VARCHAR(50) REFERENCES compliance_obligations(id) ON DELETE SET NULL,
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    category VARCHAR(50) NOT NULL DEFAULT 'System',
    urgency VARCHAR(50) NOT NULL DEFAULT 'Info',
    link_type VARCHAR(50),
    link_id VARCHAR(50),
    is_read BOOLEAN DEFAULT FALSE,
    user_id VARCHAR(50) DEFAULT 'all',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR(50) PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actor VARCHAR(100) NOT NULL,
    role VARCHAR(100) NOT NULL,
    action VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    details TEXT,
    changes_json TEXT
);

-- Indexing for performance and rapid search
CREATE INDEX IF NOT EXISTS idx_inst_perm_id ON institutions(permanent_id);
CREATE INDEX IF NOT EXISTS idx_inst_state_dist ON institutions(state, district);
CREATE INDEX IF NOT EXISTS idx_inst_category ON institutions(category);
CREATE INDEX IF NOT EXISTS idx_app_inst ON applications(institution_id);
CREATE INDEX IF NOT EXISTS idx_app_stage ON applications(current_stage);
CREATE INDEX IF NOT EXISTS idx_doc_inst ON documents(institution_id);
CREATE INDEX IF NOT EXISTS idx_doc_app ON documents(application_id);
CREATE INDEX IF NOT EXISTS idx_comp_inst ON compliance_obligations(institution_id);
CREATE INDEX IF NOT EXISTS idx_cplt_inst ON complaints(institution_id);
CREATE INDEX IF NOT EXISTS idx_task_assign ON tasks(assigned_to, status);
CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_logs(timestamp);
