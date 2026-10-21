"""
Complaint Intelligence & Case Overlap Detection Engine
"""
from typing import Dict, List, Any
import re

class OverlapDetector:
    KEYWORDS = {
        "intake": ["intake", "admission", "seat", "seats", "excess", "quota", "capitation"],
        "faculty": ["salary", "pay", "faculty", "scale", "7th cpc", "wages", "termination", "cadre"],
        "fees": ["fee", "refund", "overcharge", "caution", "deposit", "money", "receipt"],
        "infrastructure": ["lab", "building", "hostel", "fire", "library", "land", "campus"],
        "approval": ["approval", "eoa", "affiliation", "nomenclature", "unapproved", "fake"]
    }

    @classmethod
    def analyze_overlap(cls, case_a: Dict[str, Any], case_b: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes two complaints and computes similarity metrics.
        """
        if case_a.get("id") == case_b.get("id"):
            return {"score": 0, "match_type": "Same Case", "reason": "Self"}

        score = 0
        factors = []

        # Factor 1: Exact Institution ID match (Major factor: 50 points)
        inst_a = case_a.get("institution_id")
        inst_b = case_b.get("institution_id")
        if inst_a and inst_b and inst_a == inst_b:
            score += 50
            factors.append(f"Exact Institution ID match ({inst_a})")

        # Factor 2: Category match (20 points)
        cat_a = (case_a.get("category") or "").lower()
        cat_b = (case_b.get("category") or "").lower()
        if cat_a == cat_b:
            score += 20
            factors.append(f"Identical grievance category ('{case_a.get('category')}')")
        elif any(w in cat_b for w in cat_a.split()):
            score += 10
            factors.append("Partially matching grievance category")

        # Factor 3: Keyword/Subject matter overlap (up to 30 points)
        text_a = f"{case_a.get('summary', '')} {case_a.get('details', '')}".lower()
        text_b = f"{case_b.get('summary', '')} {case_b.get('details', '')}".lower()

        matched_topics = []
        for topic, words in cls.KEYWORDS.items():
            in_a = any(w in text_a for w in words)
            in_b = any(w in text_b for w in words)
            if in_a and in_b:
                matched_topics.append(topic)

        if matched_topics:
            topic_points = min(30, len(matched_topics) * 15)
            score += topic_points
            factors.append(f"Common subject matter topics: {', '.join(matched_topics)}")

        # Determine match classification
        if score >= 85:
            match_type = "Strong Potential Overlap"
        elif score >= 60:
            match_type = "Potential Match"
        elif score >= 40:
            match_type = "Weak Match"
        else:
            match_type = "Distinct"

        reason = "; ".join(factors) if factors else "No significant correlation detected."

        return {
            "score": min(100, score),
            "match_type": match_type,
            "factors": factors,
            "reason": reason,
            "requires_coordination": score >= 60
        }

    @classmethod
    def scan_all_complaints(cls, complaints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Scans a list of complaints and returns all potential overlap pairs.
        """
        results = []
        n = len(complaints)
        for i in range(n):
            for j in range(i + 1, n):
                res = cls.analyze_overlap(complaints[i], complaints[j])
                if res["requires_coordination"]:
                    results.append({
                        "case_a": complaints[i],
                        "case_b": complaints[j],
                        "score": res["score"],
                        "match_type": res["match_type"],
                        "reason": res["reason"]
                    })
        return results

overlap_detector = OverlapDetector()
