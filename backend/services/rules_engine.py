"""
Evidence-Linked Regulatory Rules Engine
"""
from datetime import date, datetime
from typing import Dict, List, Any

class RulesEngine:
    MANDATORY_DOCS = {
        "Extension of Approval (EoA)": [
            "Land Lease Agreement / Ownership Deed",
            "Fire & Life Safety Certificate",
            "Building Plan Approval / Occupancy Certificate",
            "Faculty Declaration",
            "Anti-Ragging Undertaking"
        ],
        "Introduction of New Programme": [
            "State Government NOC",
            "University Affiliation Letter",
            "Detailed Project Report (DPR)",
            "Laboratory Equipment Invoices",
            "Faculty Requirement Plan"
        ],
        "Increase in Intake": [
            "NBA Accreditation Certificate",
            "Faculty Cadre Ratio Certificate",
            "Classroom & Lab Area Compliance Deed",
            "Audited Financial Statements"
        ]
    }

    @classmethod
    def validate_document(cls, document_data: Dict[str, Any], institution_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs regulatory validation checks on a document against institution record.
        Returns structured checks and discrepancies for forensic reporting.
        """
        findings = []
        checks = []
        discrepancies = []
        status = "Verified Matching"
        is_anomaly = False

        extracted = document_data.get("extracted_fields") or {}
        extracted_perm_id = extracted.get("permanent_id")
        inst_perm_id = institution_data.get("permanent_id")
        inst_name = institution_data.get("name", "")

        # -------------------------------------------------------------
        # Rule 1: Permanent ID Validation
        # -------------------------------------------------------------
        if extracted_perm_id and inst_perm_id:
            if extracted_perm_id != inst_perm_id:
                disc = {
                    "code": "PERMANENT_ID_MISMATCH",
                    "title": "Permanent ID Discrepancy",
                    "severity": "CRITICAL",
                    "evidence": f"Document references '{extracted_perm_id}', but institution master record is '{inst_perm_id}'.",
                    "remedy": "Submit rectified certificate bearing the verified institutional permanent ID."
                }
                discrepancies.append(disc)
                findings.append(disc["evidence"])
                status = "Mismatch detected"
                is_anomaly = True
                checks.append({
                    "rule_id": "RULE-PID-01",
                    "rule_name": "Permanent ID Alignment",
                    "status": "FAIL",
                    "reference": f"Master ID: {inst_perm_id}",
                    "detail": disc["evidence"]
                })
            else:
                checks.append({
                    "rule_id": "RULE-PID-01",
                    "rule_name": "Permanent ID Alignment",
                    "status": "PASS",
                    "reference": f"Master ID: {inst_perm_id}",
                    "detail": f"Exact match verified ({inst_perm_id})."
                })
        else:
            checks.append({
                "rule_id": "RULE-PID-01",
                "rule_name": "Permanent ID Alignment",
                "status": "INFO",
                "reference": f"Master ID: {inst_perm_id or 'Not specified'}",
                "detail": "Permanent ID not detectable in raw text stream."
            })

        # -------------------------------------------------------------
        # Rule 2: Expiry Date Validation
        # -------------------------------------------------------------
        expiry_str = extracted.get("expiry_date")
        if expiry_str and str(expiry_str).lower() != "permanent":
            try:
                exp_date = datetime.strptime(str(expiry_str)[:10], "%Y-%m-%d").date()
                today = date.today()
                if exp_date < today:
                    disc = {
                        "code": "DOCUMENT_EXPIRED",
                        "title": "Expired Statutory Document",
                        "severity": "CRITICAL",
                        "evidence": f"Document validity expired on {exp_date.isoformat()} (before today {today.isoformat()}).",
                        "remedy": "Upload renewed statutory certificate or registered extension deed."
                    }
                    discrepancies.append(disc)
                    findings.append(disc["evidence"])
                    status = "Expiry detected"
                    is_anomaly = True
                    checks.append({
                        "rule_id": "RULE-EXP-02",
                        "rule_name": "Statutory Validity Period",
                        "status": "FAIL",
                        "reference": f"Today: {today.isoformat()}",
                        "detail": disc["evidence"]
                    })
                elif (exp_date - today).days <= 30:
                    disc = {
                        "code": "EXPIRY_IMMINENT",
                        "title": "Document Expiry Approaching",
                        "severity": "MEDIUM",
                        "evidence": f"Document expires on {exp_date.isoformat()} (within {(exp_date - today).days} days).",
                        "remedy": "Initiate renewal proceedings before approval period conclusion."
                    }
                    discrepancies.append(disc)
                    findings.append(disc["evidence"])
                    if status != "Mismatch detected":
                        status = "Expiry detected"
                    checks.append({
                        "rule_id": "RULE-EXP-02",
                        "rule_name": "Statutory Validity Period",
                        "status": "WARNING",
                        "reference": f"Today: {today.isoformat()}",
                        "detail": disc["evidence"]
                    })
                else:
                    checks.append({
                        "rule_id": "RULE-EXP-02",
                        "rule_name": "Statutory Validity Period",
                        "status": "PASS",
                        "reference": f"Expiry: {exp_date.isoformat()}",
                        "detail": f"Document is active and valid through {exp_date.isoformat()}."
                    })
            except ValueError:
                checks.append({
                    "rule_id": "RULE-EXP-02",
                    "rule_name": "Statutory Validity Period",
                    "status": "INFO",
                    "reference": "Date parser",
                    "detail": f"Unparsed date format '{expiry_str}'."
                })
        else:
            checks.append({
                "rule_id": "RULE-EXP-02",
                "rule_name": "Statutory Validity Period",
                "status": "PASS",
                "reference": "Continuous / Permanent",
                "detail": "Document has permanent statutory validity."
            })

        # -------------------------------------------------------------
        # Rule 3: Issuing Authority Reference
        # -------------------------------------------------------------
        auth_ref = document_data.get("authority_ref") or extracted.get("authority_ref") or extracted.get("registration_no") or extracted.get("noc_number")
        if not auth_ref:
            disc = {
                "code": "MISSING_AUTHORITY_REF",
                "title": "Missing Registration Reference Number",
                "severity": "LOW",
                "evidence": "Document lacks a verifiable authority dispatch, registration, or gazette number.",
                "remedy": "Confirm authority dispatch reference number during scrutiny."
            }
            discrepancies.append(disc)
            findings.append(disc["evidence"])
            if status == "Verified Matching":
                status = "Manual review required"
            checks.append({
                "rule_id": "RULE-AUTH-03",
                "rule_name": "Authority Reference Verification",
                "status": "WARNING",
                "reference": "Statutory Dispatch Header",
                "detail": disc["evidence"]
            })
        else:
            checks.append({
                "rule_id": "RULE-AUTH-03",
                "rule_name": "Authority Reference Verification",
                "status": "PASS",
                "reference": auth_ref,
                "detail": f"Dispatch / Registration reference verified: '{auth_ref}'."
            })

        # -------------------------------------------------------------
        # Rule 4: Institutional Name Consistency
        # -------------------------------------------------------------
        extracted_name = extracted.get("institution_name", "")
        if extracted_name and inst_name:
            if extracted_name.lower() != inst_name.lower():
                # Allow partial acronym or substring match
                if not any(token in extracted_name.lower() for token in inst_name.lower().split() if len(token) > 3):
                    disc = {
                        "code": "NAME_VARIANCE",
                        "title": "Institution Name Mismatch",
                        "severity": "HIGH",
                        "evidence": f"Document text specifies '{extracted_name}', differing from registered name '{inst_name}'.",
                        "remedy": "Provide legal name-change notification or rectified deed."
                    }
                    discrepancies.append(disc)
                    findings.append(disc["evidence"])
                    is_anomaly = True
                    checks.append({
                        "rule_id": "RULE-NAME-04",
                        "rule_name": "Institutional Name Concordance",
                        "status": "FAIL",
                        "reference": f"Master Name: {inst_name}",
                        "detail": disc["evidence"]
                    })
                else:
                    checks.append({
                        "rule_id": "RULE-NAME-04",
                        "rule_name": "Institutional Name Concordance",
                        "status": "PASS",
                        "reference": f"Master Name: {inst_name}",
                        "detail": "Name concordant with master registry."
                    })
            else:
                checks.append({
                    "rule_id": "RULE-NAME-04",
                    "rule_name": "Institutional Name Concordance",
                    "status": "PASS",
                    "reference": f"Master Name: {inst_name}",
                    "detail": "Exact institutional name alignment verified."
                })

        if not findings:
            findings.append("All deterministic regulatory format and identifier checks passed.")

        return {
            "status": status,
            "findings": " | ".join(findings),
            "is_anomaly": is_anomaly,
            "checks": checks,
            "discrepancies": discrepancies
        }

    @classmethod
    def evaluate_application_deficiencies(cls, application_type: str, submitted_documents: List[Dict[str, Any]]) -> List[str]:
        """
        Determines missing mandatory documents and application deficiencies.
        """
        required = cls.MANDATORY_DOCS.get(application_type, cls.MANDATORY_DOCS["Extension of Approval (EoA)"])
        submitted_types = [(doc.get("document_type") or "") for doc in submitted_documents]

        missing = []
        for req in required:
            matched = any(req.lower() in st.lower() or st.lower() in req.lower() for st in submitted_types)
            if not matched:
                missing.append(f"Missing mandatory document: {req}")

        for doc in submitted_documents:
            if doc.get("status") in ["Mismatch detected", "Expired according to source", "Expiry detected"]:
                missing.append(f"Deficiency in {doc.get('name')}: {doc.get('findings')}")

        return missing

rules_engine = RulesEngine()
