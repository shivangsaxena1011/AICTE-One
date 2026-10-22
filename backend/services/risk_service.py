"""
AI-Supported Regulatory Risk & Workload Insights Service for AICTE ONE
Analyzes real database records to identify SLA breach risks, repeated deficiencies,
workflow bottlenecks, and officer workload concentration.
Allows authorized users to Accept, Dismiss, or Correct recommendations.
"""
from datetime import date, datetime, timezone
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_

from backend.models import (
    Application, ComplianceObligation, Document, Complaint,
    RiskRecommendation, AuditLog, EVCSchedule, User
)

class RiskService:
    @classmethod
    def scan_and_generate_recommendations(cls, db: Session) -> List[Dict[str, Any]]:
        """
        Scans production database records and updates the active RiskRecommendation table.
        """
        today = date.today()
        recommendations = []

        # -----------------------------------------------------------------
        # 1. Cases Likely to Miss Configured Deadlines (Deadline Breach Risk)
        # -----------------------------------------------------------------
        active_apps = db.query(Application).filter(
            Application.status.notin_(["Approved", "Rejected", "Disposed", "Closed"])
        ).all()

        for a in active_apps:
            if a.due_date:
                days_left = (a.due_date - today).days
                sub_date = a.submitted_at or today
                days_spent = (today - sub_date).days
                # Risk: > 14 days spent and <= 5 days remaining, or overdue
                if days_left <= 5:
                    rec_id = f"RISK-APP-DEADLINE-{a.id}"
                    existing = db.query(RiskRecommendation).filter(RiskRecommendation.id == rec_id).first()
                    if not existing:
                        rec = RiskRecommendation(
                            id=rec_id,
                            entity_type="Application",
                            entity_id=a.id,
                            institution_id=a.institution_id,
                            category="Deadline Breach Risk",
                            severity="Critical" if days_left < 0 else "High",
                            title=f"Application {a.id} Approaching/Exceeding SLA Deadline",
                            explanation=(
                                f"Application {a.id} ({a.type}) for {a.institution.name if a.institution else 'Institution'} "
                                f"has been in stage '{a.current_stage}' for {days_spent} days. "
                                f"{'SLA deadline breached by ' + str(abs(days_left)) + ' days' if days_left < 0 else f'Only {days_left} days remaining before configured SLA deadline ({a.due_date.isoformat()})'}."
                            ),
                            supporting_indicators_json=str({
                                "days_spent": days_spent,
                                "days_left": days_left,
                                "current_stage": a.current_stage,
                                "owner": a.owner,
                                "statutory_deadline": a.due_date.isoformat()
                            }),
                            status="Active"
                        )
                        db.add(rec)
                        db.commit()

        # -----------------------------------------------------------------
        # 2. Repeated Documentation Deficiencies
        # -----------------------------------------------------------------
        resub_apps = db.query(Application).filter(Application.resubmission_count >= 2).all()
        for a in resub_apps:
            rec_id = f"RISK-APP-RESUB-{a.id}"
            existing = db.query(RiskRecommendation).filter(RiskRecommendation.id == rec_id).first()
            if not existing:
                rec = RiskRecommendation(
                    id=rec_id,
                    entity_type="Application",
                    entity_id=a.id,
                    institution_id=a.institution_id,
                    category="Repeated Documentation Deficiency",
                    severity="High",
                    title=f"Persistent Deficiencies in Application {a.id}",
                    explanation=(
                        f"Application {a.id} has undergone {a.resubmission_count} clarification resubmission cycles. "
                        f"Repeated deficiencies detected in mandatory scrutiny documentation. "
                        f"Recommend scheduling SAC/SHC specialized hearing or direct officer clarification."
                    ),
                    supporting_indicators_json=str({
                        "resubmission_count": a.resubmission_count,
                        "deficiency_count": a.deficiency_count,
                        "owner": a.owner
                    }),
                    status="Active"
                )
                db.add(rec)
                db.commit()

        # -----------------------------------------------------------------
        # 3. Workload Concentration
        # -----------------------------------------------------------------
        workload = db.query(
            Application.owner,
            func.count(Application.id).label("active_count")
        ).filter(
            Application.status.notin_(["Approved", "Rejected", "Disposed", "Closed"])
        ).group_by(Application.owner).all()

        total_active = sum(w[1] for w in workload)
        for owner, count in workload:
            if owner and owner != "Unassigned" and total_active > 0:
                share = (count / total_active) * 100.0
                if share >= 35.0 and count >= 3:
                    rec_id = f"RISK-WORKLOAD-{owner.replace(' ', '_')}"
                    existing = db.query(RiskRecommendation).filter(RiskRecommendation.id == rec_id).first()
                    if not existing:
                        rec = RiskRecommendation(
                            id=rec_id,
                            entity_type="Officer",
                            entity_id=owner,
                            category="Workload Imbalance",
                            severity="Medium",
                            title=f"Workload Concentration Alert for {owner}",
                            explanation=(
                                f"Officer {owner} is currently assigned {count} active cases "
                                f"({share:.1f}% of national queue). "
                                f"Recommend dynamic queue rebalancing to prevent bottleneck escalation."
                            ),
                            supporting_indicators_json=str({
                                "officer": owner,
                                "active_cases": count,
                                "queue_share_pct": round(share, 1)
                            }),
                            status="Active"
                        )
                        db.add(rec)
                        db.commit()

        # Fetch all active recommendations
        active_recs = db.query(RiskRecommendation).filter(RiskRecommendation.status == "Active").all()
        return [
            {
                "id": r.id,
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "institution_id": r.institution_id,
                "category": r.category,
                "severity": r.severity,
                "title": r.title,
                "explanation": r.explanation,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in active_recs
        ]

    @classmethod
    def apply_user_action(
        cls,
        rec_id: str,
        action: str,  # ACCEPT, DISMISS, CORRECT
        notes: str,
        actor: str,
        role: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Records human decision on an AI risk recommendation with reason and audit log.
        """
        rec = db.query(RiskRecommendation).filter(RiskRecommendation.id == rec_id).first()
        if not rec:
            return {"error": "Recommendation not found"}

        action_clean = action.upper()
        if action_clean == "ACCEPT":
            rec.status = "Accepted"
        elif action_clean == "DISMISS":
            rec.status = "Dismissed"
        elif action_clean == "CORRECT":
            rec.status = "Corrected"
        else:
            rec.status = action_clean

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        rec.action_taken_by = actor
        rec.action_notes = notes
        rec.action_timestamp = now

        audit = AuditLog(
            id=f"AUD-{rec.id[-8:]}",
            actor=actor,
            role=role,
            action=f"AI Risk Recommendation: {action_clean}",
            entity_type="RiskRecommendation",
            entity_id=rec.id,
            details=f"Officer {actor} {action_clean.lower()}ed risk recommendation '{rec.title}'. Notes: {notes[:100]}."
        )
        db.add(audit)
        db.commit()
        db.refresh(rec)

        return {
            "id": rec.id,
            "status": rec.status,
            "action_taken_by": rec.action_taken_by,
            "action_notes": rec.action_notes,
            "action_timestamp": rec.action_timestamp.isoformat()
        }

risk_service = RiskService()
