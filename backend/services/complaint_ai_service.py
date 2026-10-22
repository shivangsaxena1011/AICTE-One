"""
AI-Assisted Complaint Analysis & Triage Service for AICTE ONE
Implements transparent categorization, urgency scoring, missing entity detection,
case summarization, and duplicate case detection.
Never automatically alters regulatory status; supports authorized officers.
"""
import re
from typing import Dict, List, Any, Optional
from backend.services.overlap_detector import overlap_detector

class ComplaintAIService:
    CATEGORIES_CONFIG = {
        "Anti-Ragging": {
            "keywords": ["ragging", "senior", "hostel abuse", "harassment", "physical assault", "forced", "humiliation", "intro"],
            "default_bureau": "PGRC / Anti-Ragging Cell",
            "base_urgency": "Critical",
            "mandatory_fields": ["incident_date", "location", "victim_year", "approximate_time"]
        },
        "Capitation & Fee Overcharging": {
            "keywords": ["fee", "fees", "capitation", "donation", "overcharge", "receipt missing", "refund", "deposit", "extortion"],
            "default_bureau": "Finance & Bureau of Approval",
            "base_urgency": "High",
            "mandatory_fields": ["receipt_number", "amount_demanded", "academic_year", "fee_type"]
        },
        "Faculty & Staff Exploitation": {
            "keywords": ["salary", "pay scale", "7th cpc", "unpaid", "termination", "retention of certificates", "pf", "wages", "cadre"],
            "default_bureau": "Faculty Development & Grievance Cell",
            "base_urgency": "Medium",
            "mandatory_fields": ["designation", "department", "months_unpaid", "appointment_date"]
        },
        "Infrastructure & Safety Deficit": {
            "keywords": ["laboratory", "equipment", "building safety", "fire", "hostel hygiene", "library", "internet", "classroom"],
            "default_bureau": "Approval Bureau / EVC Scrutiny",
            "base_urgency": "Medium",
            "mandatory_fields": ["affected_facility", "campus_block", "programme_affected"]
        },
        "Academic & Examination Malpractice": {
            "keywords": ["exam", "hall ticket", "debarred", "attendance", "marks", "revaluation", "fake affiliation", "syllabus"],
            "default_bureau": "Policy & Academic Planning",
            "base_urgency": "High",
            "mandatory_fields": ["semester", "roll_number", "course_code", "exam_session"]
        }
    }

    @classmethod
    def analyze_complaint(
        cls,
        summary: str,
        details: Optional[str] = "",
        institution_name: Optional[str] = "",
        existing_cases: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes objective triage analysis:
        - Suggests category & bureau
        - Calculates urgency with transparent criteria
        - Identifies missing critical information
        - Detects correlated/duplicate cases
        - Distinguishes raw allegations from regulatory findings
        """
        full_text = f"{summary} {details or ''}".lower()

        # 1. Category Classification
        scores: Dict[str, int] = {}
        for cat, conf in cls.CATEGORIES_CONFIG.items():
            matches = sum(1 for kw in conf["keywords"] if kw in full_text)
            scores[cat] = matches

        best_cat = max(scores, key=scores.get) if any(scores.values()) else "General Grievance"
        conf_data = cls.CATEGORIES_CONFIG.get(best_cat, {
            "default_bureau": "Public Grievance Redressal Cell (PGRC)",
            "base_urgency": "Normal",
            "mandatory_fields": ["incident_date", "student_enrolment"]
        })

        # 2. Urgency Scoring
        urgency = conf_data["base_urgency"]
        urgency_reasons = []

        if "ragging" in full_text or "assault" in full_text or "suicide" in full_text or "threat" in full_text:
            urgency = "Critical"
            urgency_reasons.append("Safety hazard / immediate welfare concern reported in grievance text")
        elif "exam" in full_text and ("debarred" in full_text or "hall ticket" in full_text):
            urgency = "Critical"
            urgency_reasons.append("Imminent examination or academic debarment condition")
        elif any(w in full_text for w in ["fee", "donation", "overcharge"]):
            urgency = "High"
            urgency_reasons.append("Financial extortion / capitation fee violation alleged")
        else:
            urgency_reasons.append(f"Standard triage priority for {best_cat}")

        # 3. Missing Mandatory Information Detection
        missing_info = []
        if not re.search(r'\b(?:\d{4}-\d{2}-\d{2}|\d{2}[-/]\d{2}[-/]\d{4}|yesterday|today|month|week)\b', full_text):
            missing_info.append("Date or specific timeline of the alleged occurrence is not specified.")

        if "fee" in full_text and not re.search(r'\b(?:rs\.?|inr|\$|\d{4,7})\b', full_text):
            missing_info.append("Exact monetary amount or fee receipt reference number is missing.")

        if not re.search(r'\b(?:semester|sem|\d+(?:st|nd|rd|th)\s+year|b\.?tech|m\.?tech|mba|polytechnic)\b', full_text):
            missing_info.append("Academic year, semester, or enrolled degree programme is not identified.")

        if not re.search(r'\b(?:proof|evidence|receipt|screenshot|letter|audio|video|attachment)\b', full_text):
            missing_info.append("No supporting documentary evidence or attachment reference cited.")

        # 4. Extract Key Entities
        extracted_entities = {}
        # Amounts
        amounts = re.findall(r'(?:rs\.?|inr)\s*([\d,]+)', full_text)
        if amounts:
            extracted_entities["alleged_amounts"] = amounts
        # Dates
        dates = re.findall(r'\b(?:\d{4}-\d{2}-\d{2}|\d{2}[-/]\d{2}[-/]\d{4})\b', full_text)
        if dates:
            extracted_entities["timeline_dates"] = dates
        # Programmes
        progs = re.findall(r'\b(b\.?tech|m\.?tech|mba|mca|b\.?pharm|diploma)\b', full_text)
        if progs:
            extracted_entities["programmes_mentioned"] = list(set(progs))

        # 5. Duplicate / Overlapping Case Detection
        potential_duplicates = []
        if existing_cases:
            target_case = {"summary": summary, "details": details or "", "category": best_cat}
            for ec in existing_cases[:15]:
                analysis = overlap_detector.analyze_overlap(target_case, ec)
                if analysis["score"] >= 50:
                    potential_duplicates.append({
                        "case_id": ec.get("id"),
                        "case_number": ec.get("case_number", ec.get("id")),
                        "similarity_score": analysis["score"],
                        "match_type": analysis["match_type"],
                        "reason": analysis["reason"]
                    })

        # 6. Objective Case Summary
        objective_summary = (
            f"Complainant alleges {best_cat.lower()} at {institution_name or 'the institution'}. "
            f"Preliminary automated triage indicates {urgency.lower()} urgency due to: {', '.join(urgency_reasons)}. "
            f"{f'Identified {len(missing_info)} potential evidentiary gaps requiring follow-up.' if missing_info else 'Basic factual details appear complete.'}"
        )

        return {
            "suggested_bureau": conf_data["default_bureau"],
            "suggested_category": best_cat,
            "recommended_urgency": urgency,
            "urgency_reasoning": "; ".join(urgency_reasons),
            "extracted_entities": extracted_entities,
            "missing_mandatory_information": missing_info,
            "potential_duplicate_cases": potential_duplicates,
            "objective_summary": objective_summary,
            "statutory_disclaimer": (
                "AI Triage provides investigative prioritization recommendations and does NOT "
                "constitute an official adjudication, finding of misconduct, or regulatory order."
            )
        }

complaint_ai_service = ComplaintAIService()
