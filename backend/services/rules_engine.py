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
        """
        findings = []
        status = "Verified (demo)"
        is_anomaly = False

        extracted = document_data.get("extracted_fields") or {}
        extracted_perm_id = extracted.get("permanent_id")
        inst_perm_id = institution_data.get("permanent_id")

        # Rule 1: Permanent ID Match
        if extracted_perm_id and inst_perm_id:
            if extracted_perm_id != inst_perm_id:
                findings.append(
                    f"Permanent ID Mismatch: Extracted ID '{extracted_perm_id}' does not match registered Institution Permanent ID '{inst_perm_id}'."
                )
                status = "Mismatch detected"
                is_anomaly = True

        # Rule 2: Expiry Date Validation
        expiry_str = extracted.get("expiry_date")
        if expiry_str and expiry_str.lower() != "permanent":
            try:
                exp_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                today = date.today()
                if exp_date < today:
                    findings.append(
                        f"Document Expired: Document expired on {exp_date.isoformat()} (before today {today.isoformat()}). Valid renewal mandatory."
                    )
                    status = "Expiry detected"
                    is_anomaly = True
                elif (exp_date - today).days <= 30:
                    findings.append(
                        f"Expiry Approaching: Document expires on {exp_date.isoformat()} (within {(exp_date - today).days} days)."
                    )
                    if status != "Mismatch detected":
                        status = "Expiry detected"
            except ValueError:
                pass

        # Rule 3: Issuing Authority Verification
        if not document_data.get("authority_ref"):
            findings.append("Missing Authority Reference: Document does not contain a verifiable registration or dispatch number.")
            if status == "Verified (demo)":
                status = "Manual review required"

        if not findings:
            findings.append("All deterministic regulatory format and identifier checks passed.")

        return {
            "status": status,
            "findings": " | ".join(findings),
            "is_anomaly": is_anomaly
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
            # Check if any submitted document satisfies the requirement
            matched = any(req.lower() in st.lower() or st.lower() in req.lower() for st in submitted_types)
            if not matched:
                missing.append(f"Missing mandatory document: {req}")

        # Check if any submitted document has a mismatch or expiry
        for doc in submitted_documents:
            if doc.get("status") in ["Mismatch detected", "Expired according to source", "Expiry detected"]:
                missing.append(f"Deficiency in {doc.get('name')}: {doc.get('findings')}")

        return missing

rules_engine = RulesEngine()
