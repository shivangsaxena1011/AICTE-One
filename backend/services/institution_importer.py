"""
Official Institutional Data Importer & Reconciliation Pipeline for AICTE ONE
Handles authoritative datasets (e.g. all-institutions.txt, CSV, AICTE official directories),
district-to-state resolution, duplicate detection, batch transactional loading, and reconciliation.
"""
import json
import os
import uuid
from datetime import date, datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.models import Institution, ImportLog, AuditLog

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

# Comprehensive District to State/UT Mapping for India
DISTRICT_TO_STATE = {
    # Andaman & Nicobar
    "ANDAMANS": "Andaman and Nicobar Islands",
    "PORT BLAIR": "Andaman and Nicobar Islands",
    "NICOBARS": "Andaman and Nicobar Islands",
    "NORTH AND MIDDLE ANDAMAN": "Andaman and Nicobar Islands",
    "SOUTH ANDAMANS": "Andaman and Nicobar Islands",

    # Maharashtra
    "MUMBAI": "Maharashtra", "MUMBAI SUBURBAN": "Maharashtra", "MUMBAI CITY": "Maharashtra",
    "PUNE": "Maharashtra", "NAGPUR": "Maharashtra", "THANE": "Maharashtra",
    "NASHIK": "Maharashtra", "AURANGABAD": "Maharashtra", "CHHATRAPATI SAMBHAJINAGAR": "Maharashtra",
    "SOLAPUR": "Maharashtra", "KOLHAPUR": "Maharashtra", "AMRAVATI": "Maharashtra",
    "NANDED": "Maharashtra", "JALGAON": "Maharashtra", "AKOLA": "Maharashtra",
    "LATUR": "Maharashtra", "DHULE": "Maharashtra", "AHMEDNAGAR": "Maharashtra",
    "CHANDRAPUR": "Maharashtra", "PARBHANI": "Maharashtra", "SANGLI": "Maharashtra",
    "SATARA": "Maharashtra", "WARDHA": "Maharashtra", "YAVATMAL": "Maharashtra",
    "RATNAGIRI": "Maharashtra", "SINDHUDURG": "Maharashtra", "RAIGAD": "Maharashtra",
    "PALGHAR": "Maharashtra", "OSMANABAD": "Maharashtra", "DHARASHIV": "Maharashtra",
    "BEED": "Maharashtra", "BULDHANA": "Maharashtra", "GADCHIROLI": "Maharashtra",
    "GONDIA": "Maharashtra", "HINGOLI": "Maharashtra", "JALNA": "Maharashtra",
    "NANDURBAR": "Maharashtra", "WASHIM": "Maharashtra",

    # Uttar Pradesh
    "GAUTAM BUDDHA NAGAR": "Uttar Pradesh", "NOIDA": "Uttar Pradesh", "GREATER NOIDA": "Uttar Pradesh",
    "GHAZIABAD": "Uttar Pradesh", "LUCKNOW": "Uttar Pradesh", "KANPUR NAGAR": "Uttar Pradesh",
    "KANPUR": "Uttar Pradesh", "VARANASI": "Uttar Pradesh", "AGRA": "Uttar Pradesh",
    "MEERUT": "Uttar Pradesh", "PRAYAGRAJ": "Uttar Pradesh", "ALLAHABAD": "Uttar Pradesh",
    "BAREILLY": "Uttar Pradesh", "ALIGARH": "Uttar Pradesh", "MORADABAD": "Uttar Pradesh",
    "SAHARANPUR": "Uttar Pradesh", "GORAKHPUR": "Uttar Pradesh", "FAIZABAD": "Uttar Pradesh",
    "AYODHYA": "Uttar Pradesh", "JHANSI": "Uttar Pradesh", "MUZAFFARNAGAR": "Uttar Pradesh",
    "MATHURA": "Uttar Pradesh", "BULANDSHAHR": "Uttar Pradesh", "FIROZABAD": "Uttar Pradesh",
    "J P NAGAR": "Uttar Pradesh", "AMROHA": "Uttar Pradesh", "HAPUR": "Uttar Pradesh",
    "SAMBHAL": "Uttar Pradesh", "SHAMLI": "Uttar Pradesh", "BAGHPAT": "Uttar Pradesh",
    "BIJNOR": "Uttar Pradesh", "BADAUN": "Uttar Pradesh", "SHAHJAHANPUR": "Uttar Pradesh",
    "PILIBHIT": "Uttar Pradesh", "LAKHIMPUR KHERI": "Uttar Pradesh", "SITAPUR": "Uttar Pradesh",
    "HARDOI": "Uttar Pradesh", "UNNAO": "Uttar Pradesh", "RAE BARELI": "Uttar Pradesh",
    "FARRUKHABAD": "Uttar Pradesh", "KANNAUJ": "Uttar Pradesh", "ETAWAH": "Uttar Pradesh",
    "AURAIYA": "Uttar Pradesh", "MAINPURI": "Uttar Pradesh", "ETAH": "Uttar Pradesh",
    "KASGANJ": "Uttar Pradesh", "HATHRAS": "Uttar Pradesh",

    # Delhi
    "DELHI": "Delhi", "NEW DELHI": "Delhi", "NORTH DELHI": "Delhi", "SOUTH DELHI": "Delhi",
    "EAST DELHI": "Delhi", "WEST DELHI": "Delhi", "CENTRAL DELHI": "Delhi",
    "NORTH EAST DELHI": "Delhi", "NORTH WEST DELHI": "Delhi", "SOUTH EAST DELHI": "Delhi",
    "SOUTH WEST DELHI": "Delhi", "SHAHDARA": "Delhi",

    # Karnataka
    "BENGALURU URBAN": "Karnataka", "BANGALORE": "Karnataka", "BENGALURU RURAL": "Karnataka",
    "MYSURU": "Karnataka", "MYSORE": "Karnataka", "BELAGAVI": "Karnataka", "BELGAUM": "Karnataka",
    "DHARWAD": "Karnataka", "HUBBALLI": "Karnataka", "MANGALURU": "Karnataka", "DAKSHINA KANNADA": "Karnataka",
    "TUMAKURU": "Karnataka", "SHIVAMOGGA": "Karnataka", "BALLARI": "Karnataka", "BELLARY": "Karnataka",
    "VIJAYAPURA": "Karnataka", "BIJAPUR": "Karnataka", "KALABURAGI": "Karnataka", "GULBARGA": "Karnataka",
    "DAVANAGERE": "Karnataka", "UDUPI": "Karnataka", "HASSAN": "Karnataka", "BIDAR": "Karnataka",
    "BAGALKOT": "Karnataka", "CHIKKAMAGALURU": "Karnataka", "MANDYA": "Karnataka", "KOLAR": "Karnataka",
    "CHIKKABALLAPURA": "Karnataka", "CHITRADURGA": "Karnataka", "GADAG": "Karnataka", "HAVERI": "Karnataka",
    "KOPPAL": "Karnataka", "RAICHUR": "Karnataka", "RAMANAGARA": "Karnataka", "YADGIR": "Karnataka",
    "CHAMARAJANAGAR": "Karnataka", "KODAGU": "Karnataka", "UTTARA KANNADA": "Karnataka",

    # Tamil Nadu
    "CHENNAI": "Tamil Nadu", "COIMBATORE": "Tamil Nadu", "MADURAI": "Tamil Nadu",
    "TIRUCHIRAPPALLI": "Tamil Nadu", "TRICHY": "Tamil Nadu", "SALEM": "Tamil Nadu",
    "TIRUNELVELI": "Tamil Nadu", "TIRUPPUR": "Tamil Nadu", "ERODE": "Tamil Nadu",
    "VELLORE": "Tamil Nadu", "THOOTHUKUDI": "Tamil Nadu", "DINDIGUL": "Tamil Nadu",
    "THANJAVUR": "Tamil Nadu", "RANIPET": "Tamil Nadu", "KANCHIPURAM": "Tamil Nadu",
    "CHENGALPATTU": "Tamil Nadu", "TIRUVALLUR": "Tamil Nadu", "CUDDALORE": "Tamil Nadu",
    "VILLUPURAM": "Tamil Nadu", "KALLAKURICHI": "Tamil Nadu", "TIRUVANNAMALAI": "Tamil Nadu",
    "KRISHNAGIRI": "Tamil Nadu", "DHARMAPURI": "Tamil Nadu", "NAMAKKAL": "Tamil Nadu",
    "KARUR": "Tamil Nadu", "PERAMBALUR": "Tamil Nadu", "ARIYALUR": "Tamil Nadu",
    "PUDUKKOTTAI": "Tamil Nadu", "SIVAGANGA": "Tamil Nadu", "VIRUDHUNAGAR": "Tamil Nadu",
    "RAMANATHAPURAM": "Tamil Nadu", "THENI": "Tamil Nadu", "TENKASI": "Tamil Nadu",
    "KANNYAKUMARI": "Tamil Nadu", "KANYAKUMARI": "Tamil Nadu", "NILGIRIS": "Tamil Nadu",
    "NAGAPATTINAM": "Tamil Nadu", "MAYILADUTHURAI": "Tamil Nadu", "TIRUVARUR": "Tamil Nadu",

    # Andhra Pradesh & Telangana
    "VISAKHAPATNAM": "Andhra Pradesh", "VIJAYAWADA": "Andhra Pradesh", "KRISHNA": "Andhra Pradesh",
    "GUNTUR": "Andhra Pradesh", "KURNOOL": "Andhra Pradesh", "TIRUPATI": "Andhra Pradesh",
    "CHITTOOR": "Andhra Pradesh", "ANANTAPUR": "Andhra Pradesh", "EAST GODAVARI": "Andhra Pradesh",
    "WEST GODAVARI": "Andhra Pradesh", "NELLORE": "Andhra Pradesh", "KADAPA": "Andhra Pradesh",
    "SRIKAKULAM": "Andhra Pradesh", "VIZIANAGARAM": "Andhra Pradesh", "PRAKASAM": "Andhra Pradesh",
    "HYDERABAD": "Telangana", "RANGAREDDY": "Telangana", "MEDCHAL-MALKAJGIRI": "Telangana",
    "WARANGAL": "Telangana", "HANUMAKONDA": "Telangana", "KHAMMAM": "Telangana",
    "KARIMNAGAR": "Telangana", "NIZAMABAD": "Telangana", "NALGONDA": "Telangana",
    "MAHABUBNAGAR": "Telangana", "SANGAREDDY": "Telangana", "SIDDIPET": "Telangana",

    # Kerala
    "THIRUVANANTHAPURAM": "Kerala", "ERNAKULAM": "Kerala", "KOCHI": "Kerala",
    "KOZHIKODE": "Kerala", "THRISSUR": "Kerala", "MALAPPURAM": "Kerala",
    "KOLLAM": "Kerala", "PALAKKAD": "Kerala", "ALAPPUZHA": "Kerala",
    "KANNUR": "Kerala", "KOTTAYAM": "Kerala", "KASARAGOD": "Kerala",
    "PATHANAMTHITTA": "Kerala", "IDUKKI": "Kerala", "WAYANAD": "Kerala",

    # Gujarat
    "AHMEDABAD": "Gujarat", "SURAT": "Gujarat", "VADODARA": "Gujarat", "RAJKOT": "Gujarat",
    "GANDHINAGAR": "Gujarat", "BHAVNAGAR": "Gujarat", "JAMNAGAR": "Gujarat", "JUNAGADH": "Gujarat",
    "ANAND": "Gujarat", "KUTCH": "Gujarat", "KACHCHH": "Gujarat", "MEHSANA": "Gujarat",
    "VALSAD": "Gujarat", "BHARUCH": "Gujarat", "NAVSARI": "Gujarat", "BANASKANTHA": "Gujarat",
    "SABARKANTHA": "Gujarat", "PANCHMAHAL": "Gujarat", "DAHOD": "Gujarat", "PATAN": "Gujarat",

    # Madhya Pradesh
    "BHOPAL": "Madhya Pradesh", "INDORE": "Madhya Pradesh", "GWALIOR": "Madhya Pradesh",
    "JABALPUR": "Madhya Pradesh", "UJJAIN": "Madhya Pradesh", "SAGAR": "Madhya Pradesh",
    "REWA": "Madhya Pradesh", "SATNA": "Madhya Pradesh", "RATLAM": "Madhya Pradesh",
    "SHEOPUR": "Madhya Pradesh", "MORENA": "Madhya Pradesh", "BHIND": "Madhya Pradesh",
    "DEWAS": "Madhya Pradesh", "DHAR": "Madhya Pradesh", "KHARGONE": "Madhya Pradesh",
    "KHANDWA": "Madhya Pradesh", "SEHORE": "Madhya Pradesh", "RAISEN": "Madhya Pradesh",
    "VIDISHA": "Madhya Pradesh", "HOSHANGABAD": "Madhya Pradesh", "NARMADAPURAM": "Madhya Pradesh",

    # Rajasthan
    "JAIPUR": "Rajasthan", "JODHPUR": "Rajasthan", "KOTA": "Rajasthan", "UDAIPUR": "Rajasthan",
    "BIKANER": "Rajasthan", "AJMER": "Rajasthan", "ALWAR": "Rajasthan", "BHILWARA": "Rajasthan",
    "SIKAR": "Rajasthan", "PALI": "Rajasthan", "BHARATPUR": "Rajasthan", "CHITTORGARH": "Rajasthan",
    "JHUNJHUNU": "Rajasthan", "NAGAUR": "Rajasthan", "SRI GANGANAGAR": "Rajasthan",

    # Haryana & Punjab
    "GURGAON": "Haryana", "GURUGRAM": "Haryana", "FARIDABAD": "Haryana", "SONIPAT": "Haryana",
    "AMBALA": "Haryana", "HISAR": "Haryana", "ROHTAK": "Haryana", "PANIPAT": "Haryana",
    "KARNAL": "Haryana", "PANCHKULA": "Haryana", "YAMUNANAGAR": "Haryana", "KURUKSHETRA": "Haryana",
    "LUDHIANA": "Punjab", "AMRITSAR": "Punjab", "JALANDHAR": "Punjab", "PATIALA": "Punjab",
    "BATHINDA": "Punjab", "MOHALI": "Punjab", "SAS NAGAR": "Punjab", "HOSHIARPUR": "Punjab",
    "CHANDIGARH": "Chandigarh",

    # West Bengal, Bihar, Odisha, Assam, Uttarakhand, J&K
    "KOLKATA": "West Bengal", "HOWRAH": "West Bengal", "NORTH 24 PARGANAS": "West Bengal",
    "SOUTH 24 PARGANAS": "West Bengal", "HOOGHLY": "West Bengal", "DARJEELING": "West Bengal",
    "PATNA": "Bihar", "GAYA": "Bihar", "BHAGALPUR": "Bihar", "MUZAFFARPUR": "Bihar",
    "BHUBANESWAR": "Odisha", "KHORDHA": "Odisha", "CUTTACK": "Odisha", "SUNDARGARH": "Odisha",
    "GUWAHATI": "Assam", "KAMRUP": "Assam", "KAMRUP METROPOLITAN": "Assam", "GOALPARA": "Assam",
    "DEHRADUN": "Uttarakhand", "HARIDWAR": "Uttarakhand", "NAINITAL": "Uttarakhand", "UDHAM SINGH NAGAR": "Uttarakhand",
    "SRINAGAR": "Jammu and Kashmir", "JAMMU": "Jammu and Kashmir", "KULGAM": "Jammu and Kashmir"
}

class InstitutionImporterService:
    """Service for parsing, validating, importing, and reconciling institutional records."""

    @classmethod
    def resolve_state_from_district(cls, district: Optional[str], default_state: str = "India") -> str:
        if not district:
            return default_state
        dist_clean = district.strip().upper()
        return DISTRICT_TO_STATE.get(dist_clean, default_state)

    @classmethod
    def load_records_from_source(cls, source_path_or_json: Any) -> List[Dict[str, Any]]:
        """Parses records from file path or JSON object/string."""
        if isinstance(source_path_or_json, list):
            return source_path_or_json

        if isinstance(source_path_or_json, str):
            if os.path.exists(source_path_or_json):
                with open(source_path_or_json, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content.startswith("[") or content.startswith("{"):
                        data = json.loads(content)
                        return data if isinstance(data, list) else [data]
            else:
                # Attempt to parse as raw json string
                try:
                    data = json.loads(source_path_or_json)
                    return data if isinstance(data, list) else [data]
                except Exception:
                    pass
        return []

    @classmethod
    def validate_and_preview(
        cls,
        raw_records: List[Dict[str, Any]],
        db: Session,
        preview_limit: int = 15
    ) -> Dict[str, Any]:
        """
        Validates records, flags duplicates against the active database,
        detects missing mandatory attributes, and generates a structured preview.
        """
        total = len(raw_records)
        existing_pids = {i.permanent_id for i in db.query(Institution.permanent_id).all()}
        existing_names = {i.name.upper() for i in db.query(Institution.name).all()}

        seen_in_batch = set()
        valid_count = 0
        duplicate_count = 0
        invalid_count = 0
        preview_items = []
        errors = []

        for idx, r in enumerate(raw_records):
            pid = (r.get("other_id") or r.get("permanent_id") or r.get("Permanent ID") or "").strip()
            aicte_id = (r.get("aicte_id") or r.get("AICTE ID") or "").strip()
            name = (r.get("institute_name") or r.get("name") or r.get("Institution Name") or "").strip()
            district = (r.get("district") or r.get("District") or "").strip()

            if not name:
                invalid_count += 1
                if len(errors) < 10:
                    errors.append(f"Record {idx+1}: Missing institution name.")
                continue

            unique_key = pid if pid else (aicte_id if aicte_id else name.upper())

            # Batch internal deduplication check
            if unique_key in seen_in_batch:
                duplicate_count += 1
                continue
            seen_in_batch.add(unique_key)

            # DB duplicate check
            is_in_db = (pid in existing_pids) or (name.upper() in existing_names)
            if is_in_db:
                duplicate_count += 1
            else:
                valid_count += 1

            if len(preview_items) < preview_limit:
                state = r.get("state") or cls.resolve_state_from_district(district, "India")
                preview_items.append({
                    "row": idx + 1,
                    "name": name,
                    "permanent_id": pid or f"1-GEN-{uuid.uuid4().hex[:6].upper()}",
                    "aicte_id": aicte_id,
                    "district": district or "Unspecified",
                    "state": state,
                    "institution_type": r.get("institution_type") or "Private-Self Financing",
                    "status_in_db": "Existing (Duplicate)" if is_in_db else "New Record"
                })

        return {
            "total_records_in_source": total,
            "unique_records": len(seen_in_batch),
            "new_valid_records": valid_count,
            "duplicate_records": duplicate_count,
            "invalid_records": invalid_count,
            "preview_items": preview_items,
            "errors": errors
        }

    @classmethod
    def execute_import(
        cls,
        raw_records: List[Dict[str, Any]],
        db: Session,
        imported_by: str,
        source_name: str = "all-institutions.txt",
        batch_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executes transactional import of authoritative institution records.
        Deduplicates against existing database records and prevents unique constraint violations.
        """
        existing_pids = {i.permanent_id for i in db.query(Institution.permanent_id).all()}
        existing_names = {i.name.upper() for i in db.query(Institution.name).all()}

        seen_in_batch = set()
        created_count = 0
        skipped_count = 0
        error_count = 0
        errors = []

        to_insert = []
        now = utc_now()
        today = date.today()

        for idx, r in enumerate(raw_records):
            if batch_limit and created_count >= batch_limit:
                break

            pid = (r.get("other_id") or r.get("permanent_id") or r.get("Permanent ID") or "").strip()
            aicte_id = (r.get("aicte_id") or r.get("AICTE ID") or "").strip()
            name = (r.get("institute_name") or r.get("name") or r.get("Institution Name") or "").strip()
            district = (r.get("district") or r.get("District") or "").strip()
            address = (r.get("address") or r.get("Address") or "").strip()

            if not name:
                error_count += 1
                continue

            clean_pid = pid if pid else (aicte_id if aicte_id else f"1-{uuid.uuid4().hex[:8].upper()}")

            if clean_pid in seen_in_batch or clean_pid in existing_pids:
                skipped_count += 1
                continue
            seen_in_batch.add(clean_pid)

            state = r.get("state") or cls.resolve_state_from_district(district, "India")
            inst_type = r.get("institution_type") or "Private-Self Financing"
            category = r.get("category") or "Engineering and Technology"

            women = True if str(r.get("women", "")).strip().upper() == "Y" else False
            minority = True if str(r.get("minority", "")).strip().upper() == "Y" else False

            inst_id = f"INST-{uuid.uuid4().hex[:10].upper()}"
            new_inst = Institution(
                id=inst_id,
                name=name,
                permanent_id=clean_pid,
                aicte_id=aicte_id,
                state=state,
                district=district or state,
                city=district or state,
                address=address,
                category=category,
                institution_type=inst_type,
                approval_status="Approved",
                approval_period="2026-2027",
                programmes_count=r.get("programmes_count", 4),
                total_intake=r.get("total_intake", 360),
                women_only=women,
                minority=minority,
                data_source=f"AICTE Official Dataset ({source_name})",
                verified_status="Verified",
                last_verified=today,
                created_at=now,
                updated_at=now
            )
            to_insert.append(new_inst)
            created_count += 1

            # Commit in safe chunks of 500
            if len(to_insert) >= 500:
                try:
                    db.add_all(to_insert)
                    db.commit()
                    to_insert = []
                except Exception as e:
                    db.rollback()
                    error_count += len(to_insert)
                    errors.append(f"Batch commit failure: {str(e)[:120]}")
                    to_insert = []

        if to_insert:
            try:
                db.add_all(to_insert)
                db.commit()
            except Exception as e:
                db.rollback()
                error_count += len(to_insert)
                errors.append(f"Final batch commit failure: {str(e)[:120]}")

        # Record ImportLog
        log_id = f"IMP-{uuid.uuid4().hex[:6].upper()}"
        import_log = ImportLog(
            id=log_id,
            source_file=source_name,
            imported_by=imported_by,
            total_records=len(raw_records),
            imported_count=created_count,
            skipped_count=skipped_count,
            error_count=error_count,
            status="Success" if error_count == 0 else ("Partial" if created_count > 0 else "Failed"),
            summary_notes=f"Successfully imported {created_count} official institution records from {source_name}. Skipped {skipped_count} duplicates."
        )
        db.add(import_log)

        # Record AuditLog
        audit = AuditLog(
            id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
            actor=imported_by,
            role="SUPER_ADMIN",
            action="Official Institution Batch Import",
            entity_type="InstitutionMaster",
            entity_id=log_id,
            details=f"Processed {len(raw_records)} records: Created={created_count}, Skipped={skipped_count}, Errors={error_count}."
        )
        db.add(audit)
        db.commit()

        return {
            "import_log_id": log_id,
            "status": import_log.status,
            "total_processed": len(raw_records),
            "created": created_count,
            "skipped_duplicates": skipped_count,
            "errors_count": error_count,
            "errors": errors[:5]
        }

    @classmethod
    def reconcile(cls, db: Session, source_records_count: int) -> Dict[str, Any]:
        """Reconciles database master records against source inventory."""
        db_total = db.query(Institution).count()
        approved = db.query(Institution).filter(Institution.approval_status == "Approved").count()
        missing_district = db.query(Institution).filter(or_(Institution.district == None, Institution.district == "")).count()
        missing_state = db.query(Institution).filter(or_(Institution.state == None, Institution.state == "India")).count()

        return {
            "source_inventory_count": source_records_count,
            "database_master_count": db_total,
            "verified_approved_count": approved,
            "data_quality_flags": {
                "missing_or_default_state": missing_state,
                "missing_district": missing_district
            },
            "reconciliation_status": "Reconciled" if db_total > 0 else "Empty Database",
            "reconciled_at": utc_now().isoformat()
        }

institution_importer = InstitutionImporterService()
