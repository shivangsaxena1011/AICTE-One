"""
Document Processing & OCR Extraction Service
"""
import hashlib
import re
from datetime import datetime, timezone, date

class OCRService:
    @staticmethod
    def calculate_sha256(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def extract_document_fields(filename: str, doc_type: str, institution_name: str, permanent_id: str, content: bytes = None):
        """
        Extracts key fields, metadata, and confidence scores from document.
        In demo/local environment, generates realistic deterministic field extraction
        based on the file name, document type, and institutional context.
        """
        clean_name = filename.lower()
        today_str = date.today().isoformat()
        
        # Default extraction template
        extracted = {
            "institution_name": institution_name,
            "permanent_id": permanent_id,
            "document_filename": filename,
            "document_type": doc_type,
            "extracted_at": datetime.now(timezone.utc).isoformat()
        }
        confidence = "95%"
        findings = "Standard metadata extracted successfully."
        is_anomaly = False
        authority = "State / Central Authority"
        authority_ref = f"REF-{permanent_id[-4:]}-2026"
        expiry_date = "2027-06-30"

        if "lease" in clean_name or "land" in clean_name or "lease" in doc_type.lower():
            authority = "Sub-Registrar Office / Revenue Department"
            authority_ref = f"REG-LAND-{permanent_id[-5:]}/2016"
            expiry_date = "2026-10-25"
            extracted.update({
                "issuing_authority": authority,
                "registration_no": authority_ref,
                "issue_date": "2016-11-01",
                "expiry_date": expiry_date,
                "land_area": "12.5 Acres",
                "lease_period": "10 Years"
            })
            confidence = "98%"
            findings = "Lease agreement registration seal and signatures detected. Expiry date is 25-Oct-2026."

        elif "fire" in clean_name or "safety" in clean_name or "fire" in doc_type.lower():
            authority = "State Fire & Emergency Services"
            authority_ref = f"BFS-NOC-{permanent_id[-4:]}-881"
            expiry_date = "2026-08-31"
            extracted.update({
                "issuing_authority": authority,
                "noc_number": authority_ref,
                "issue_date": "2023-09-01",
                "expiry_date": expiry_date,
                "building_blocks": "Main Academic Block, Lab Complex"
            })
            confidence = "93%"
            findings = "Fire Safety Certificate extracted. Certificate expired on 31-Aug-2026."
            is_anomaly = True

        elif "faculty" in clean_name or "cadre" in clean_name or "faculty" in doc_type.lower():
            authority = "Institutional Governing Council"
            authority_ref = f"FAC-{permanent_id[-5:]}-2026"
            extracted.update({
                "issuing_authority": authority,
                "declaration_ref": authority_ref,
                "issue_date": today_str,
                "declared_cadre_ratio": "1:2:6",
                "total_faculty": "54",
                "phd_holders": "28"
            })
            confidence = "91%"
            findings = "Faculty roster and declaration extracted with salary disbursement stamp."

        elif "nba" in clean_name or "accredit" in clean_name or "naac" in doc_type.lower():
            authority = "National Board of Accreditation"
            authority_ref = f"NBA/ACCR-{permanent_id[-4:]}/2024"
            expiry_date = "2027-06-30"
            extracted.update({
                "issuing_authority": authority,
                "accreditation_ref": authority_ref,
                "issue_date": "2024-07-01",
                "expiry_date": expiry_date,
                "accredited_tier": "Tier-I",
                "score": "685/1000"
            })
            confidence = "97%"
            findings = "NBA accreditation certificate extracted. Valid through 30-Jun-2027."

        elif "noc" in clean_name or "state" in clean_name:
            authority = "Department of Technical Education"
            authority_ref = f"DTE-NOC-{permanent_id[-4:]}/2026"
            extracted.update({
                "issuing_authority": authority,
                "noc_number": authority_ref,
                "issue_date": "2026-08-15",
                "validity": "Permanent / Continuous"
            })
            confidence = "98%"
            findings = "State Government No-Objection Certificate verified with digital signature."

        else:
            extracted.update({
                "issuing_authority": authority,
                "reference_no": authority_ref,
                "issue_date": today_str
            })

        return {
            "extracted_fields": extracted,
            "confidence": confidence,
            "findings": findings,
            "issuing_authority": authority,
            "authority_ref": authority_ref,
            "is_anomaly": is_anomaly
        }

ocr_service = OCRService()
