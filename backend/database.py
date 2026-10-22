"""
Database Connection and Session Management
"""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initializes database schema and safely executes non-destructive column migrations.
    """
    from backend import models  # Ensure all models are registered
    Base.metadata.create_all(bind=engine)

    # For SQLite, check and add missing columns if upgrading an existing file
    if settings.DATABASE_URL.startswith("sqlite"):
        inspector = inspect(engine)
        with engine.connect() as conn:
            # Check users columns
            if "users" in inspector.get_table_names():
                user_cols = {col["name"] for col in inspector.get_columns("users")}
                missing_user_cols = {
                    "password_hash": "VARCHAR(255) DEFAULT ''",
                    "institution_id": "VARCHAR(50)",
                    "phone": "VARCHAR(50)",
                    "is_mfa_enabled": "BOOLEAN DEFAULT 0",
                    "mfa_secret": "VARCHAR(100)",
                    "passkey_credential_id": "VARCHAR(255)",
                    "passkey_public_key": "TEXT",
                    "failed_login_attempts": "INTEGER DEFAULT 0",
                    "locked_until": "TIMESTAMP",
                    "updated_at": "TIMESTAMP"
                }
                for col_name, col_type in missing_user_cols.items():
                    if col_name not in user_cols:
                        try:
                            conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                            conn.commit()
                        except Exception:
                            pass

            # Check complaints columns
            if "complaints" in inspector.get_table_names():
                cplt_cols = {col["name"] for col in inspector.get_columns("complaints")}
                missing_cplt_cols = {
                    "complainant_id": "VARCHAR(50)",
                    "is_confidential": "BOOLEAN DEFAULT 0",
                    "ragging_flag": "BOOLEAN DEFAULT 0",
                    "ai_triage_json": "TEXT",
                    "triage_urgency": "VARCHAR(20) DEFAULT 'Normal'",
                    "missing_info_flags": "TEXT"
                }
                for col_name, col_type in missing_cplt_cols.items():
                    if col_name not in cplt_cols:
                        try:
                            conn.execute(text(f"ALTER TABLE complaints ADD COLUMN {col_name} {col_type}"))
                            conn.commit()
                        except Exception:
                            pass

            # Check documents columns
            if "documents" in inspector.get_table_names():
                doc_cols = {col["name"] for col in inspector.get_columns("documents")}
                missing_doc_cols = {
                    "confidentiality_level": "VARCHAR(50) DEFAULT 'Internal'",
                    "uploaded_by": "VARCHAR(100)",
                    "review_status": "VARCHAR(50) DEFAULT 'Pending Human Review'",
                    "reviewed_by": "VARCHAR(100)",
                    "reviewed_at": "TIMESTAMP",
                    "review_notes": "TEXT",
                    "human_overridden_fields": "TEXT",
                    "forensic_report_json": "TEXT"
                }
                for col_name, col_type in missing_doc_cols.items():
                    if col_name not in doc_cols:
                        try:
                            conn.execute(text(f"ALTER TABLE documents ADD COLUMN {col_name} {col_type}"))
                            conn.commit()
                        except Exception:
                            pass

            # Check institutions columns for Phase 3
            if "institutions" in inspector.get_table_names():
                inst_cols = {col["name"] for col in inspector.get_columns("institutions")}
                missing_inst_cols = {
                    "aicte_id": "VARCHAR(50)",
                    "women_only": "BOOLEAN DEFAULT 0",
                    "minority": "BOOLEAN DEFAULT 0",
                    "is_demo_record": "BOOLEAN DEFAULT 0"
                }
                for col_name, col_type in missing_inst_cols.items():
                    if col_name not in inst_cols:
                        try:
                            conn.execute(text(f"ALTER TABLE institutions ADD COLUMN {col_name} {col_type}"))
                            conn.commit()
                        except Exception:
                            pass

            # Check audit_logs columns
            if "audit_logs" in inspector.get_table_names():
                audit_cols = {col["name"] for col in inspector.get_columns("audit_logs")}
                missing_audit_cols = {
                    "ip_address": "VARCHAR(50)",
                    "user_id": "VARCHAR(50)"
                }
                for col_name, col_type in missing_audit_cols.items():
                    if col_name not in audit_cols:
                        try:
                            conn.execute(text(f"ALTER TABLE audit_logs ADD COLUMN {col_name} {col_type}"))
                            conn.commit()
                        except Exception:
                            pass

            # Check applications columns for Phase 2 workflow engine
            if "applications" in inspector.get_table_names():
                app_cols = {col["name"] for col in inspector.get_columns("applications")}
                missing_app_cols = {
                    "workflow_definition_id": "VARCHAR(50)",
                    "workflow_version": "INTEGER DEFAULT 1",
                    "route_type": "VARCHAR(50) DEFAULT 'SCRUTINY_EVC'",
                    "stage_code": "VARCHAR(50) DEFAULT 'PRELIMINARY_VALIDATION'",
                    "assigned_role": "VARCHAR(50) DEFAULT 'POLICY_COMPLIANCE_OFFICER'",
                    "assigned_user_id": "VARCHAR(50)",
                    "stage_entered_at": "TIMESTAMP",
                    "stage_due_date": "DATE",
                    "is_paused": "BOOLEAN DEFAULT 0",
                    "paused_at": "TIMESTAMP",
                    "total_pause_days": "INTEGER DEFAULT 0",
                    "resubmission_count": "INTEGER DEFAULT 0",
                    "is_escalated": "BOOLEAN DEFAULT 0",
                    "escalation_level": "INTEGER DEFAULT 0",
                    "last_idempotency_key": "VARCHAR(100)"
                }
                for col_name, col_type in missing_app_cols.items():
                    if col_name not in app_cols:
                        try:
                            conn.execute(text(f"ALTER TABLE applications ADD COLUMN {col_name} {col_type}"))
                            conn.commit()
                        except Exception:
                            pass

            # Check application_stages columns
            if "application_stages" in inspector.get_table_names():
                stg_cols = {col["name"] for col in inspector.get_columns("application_stages")}
                missing_stg_cols = {
                    "stage_code": "VARCHAR(50)",
                    "from_stage": "VARCHAR(100)",
                    "to_stage": "VARCHAR(100)",
                    "action": "VARCHAR(50) DEFAULT 'ADVANCE'",
                    "time_spent_hours": "FLOAT DEFAULT 0.0",
                    "sla_breached": "BOOLEAN DEFAULT 0",
                    "idempotency_key": "VARCHAR(100)"
                }
                for col_name, col_type in missing_stg_cols.items():
                    if col_name not in stg_cols:
                        try:
                            conn.execute(text(f"ALTER TABLE application_stages ADD COLUMN {col_name} {col_type}"))
                            conn.commit()
                        except Exception:
                            pass

            # Check evc_schedules columns
            if "evc_schedules" in inspector.get_table_names():
                evc_cols = {col["name"] for col in inspector.get_columns("evc_schedules")}
                missing_evc_cols = {
                    "convener": "VARCHAR(100)",
                    "expert_members_json": "TEXT",
                    "conflicts_declared": "BOOLEAN DEFAULT 0",
                    "geo_latitude": "FLOAT",
                    "geo_longitude": "FLOAT",
                    "recommendation": "VARCHAR(50)",
                    "checklist_findings_json": "TEXT"
                }
                for col_name, col_type in missing_evc_cols.items():
                    if col_name not in evc_cols:
                        try:
                            conn.execute(text(f"ALTER TABLE evc_schedules ADD COLUMN {col_name} {col_type}"))
                            conn.commit()
                        except Exception:
                            pass

            # Check login_history columns
            if "login_history" in inspector.get_table_names():
                lh_cols = {col["name"] for col in inspector.get_columns("login_history")}
                missing_lh_cols = {
                    "username_attempted": "VARCHAR(100)",
                    "success": "BOOLEAN DEFAULT 0",
                    "created_at": "TIMESTAMP"
                }
                for col_name, col_type in missing_lh_cols.items():
                    if col_name not in lh_cols:
                        try:
                            conn.execute(text(f"ALTER TABLE login_history ADD COLUMN {col_name} {col_type}"))
                            conn.commit()
                        except Exception:
                            pass

            # Check user_sessions columns
            if "user_sessions" in inspector.get_table_names():
                us_cols = {col["name"] for col in inspector.get_columns("user_sessions")}
                if "token_hash" not in us_cols:
                    try:
                        conn.execute(text("ALTER TABLE user_sessions ADD COLUMN token_hash VARCHAR(128)"))
                        conn.commit()
                    except Exception:
                        pass

            # Check password_reset_tokens columns
            if "password_reset_tokens" in inspector.get_table_names():
                prt_cols = {col["name"] for col in inspector.get_columns("password_reset_tokens")}
                if "token_hash" not in prt_cols:
                    try:
                        conn.execute(text("ALTER TABLE password_reset_tokens ADD COLUMN token_hash VARCHAR(128)"))
                        conn.commit()
                    except Exception:
                        pass

            # Check role_permissions columns
            if "role_permissions" in inspector.get_table_names():
                rp_cols = {col["name"] for col in inspector.get_columns("role_permissions")}
                for col_name in ["role_id", "permission_id"]:
                    if col_name not in rp_cols:
                        try:
                            conn.execute(text(f"ALTER TABLE role_permissions ADD COLUMN {col_name} VARCHAR(50)"))
                            conn.commit()
                        except Exception:
                            pass
