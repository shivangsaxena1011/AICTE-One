"""
Institutions Router: Directory, Digital Twin, Search, Pagination & CSV Import
"""
import io
import csv
import uuid
from typing import Optional, List
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from backend.database import get_db
from backend.models import (
    Institution, Application, Document, ComplianceObligation, Complaint, Task, AuditLog
)
from backend.schemas import (
    InstitutionResponse, InstitutionCreate, InstitutionImportSummary
)

router = APIRouter(prefix="/api/institutions", tags=["Institutions"])

@router.get("", response_model=dict)
def list_institutions(
    q: Optional[str] = Query(None, description="Search by name, permanent_id, or city"),
    state: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    institution_type: Optional[str] = Query(None),
    approval_status: Optional[str] = Query(None),
    sort_by: str = Query("name"),
    order: str = Query("asc"),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(Institution)

    if q:
        search_filter = or_(
            Institution.name.ilike(f"%{q}%"),
            Institution.permanent_id.ilike(f"%{q}%"),
            Institution.city.ilike(f"%{q}%"),
            Institution.district.ilike(f"%{q}%")
        )
        query = query.filter(search_filter)

    if state:
        query = query.filter(Institution.state == state)
    if category:
        query = query.filter(Institution.category == category)
    if institution_type:
        query = query.filter(Institution.institution_type == institution_type)
    if approval_status:
        query = query.filter(Institution.approval_status == approval_status)

    total = query.count()

    # Sorting
    sort_col = getattr(Institution, sort_by, Institution.name)
    query = query.order_by(asc(sort_col) if order == "asc" else desc(sort_col))

    offset = (page - 1) * limit
    institutions = query.offset(offset).limit(limit).all()

    # Format response
    data = []
    for inst in institutions:
        data.append({
            "id": inst.id,
            "permanent_id": inst.permanent_id,
            "name": inst.name,
            "state": inst.state,
            "district": inst.district,
            "city": inst.city,
            "address": inst.address,
            "category": inst.category,
            "institution_type": inst.institution_type,
            "affiliation": inst.affiliation,
            "website": inst.website,
            "approval_status": inst.approval_status,
            "approval_period": inst.approval_period,
            "programmes_count": inst.programmes_count,
            "total_intake": inst.total_intake,
            "data_source": inst.data_source,
            "verified_status": inst.verified_status,
            "last_verified": inst.last_verified.isoformat() if inst.last_verified else None,
            "applications_count": len(inst.applications),
            "documents_count": len(inst.documents),
            "compliance_count": len(inst.compliance_obligations),
            "complaints_count": len(inst.complaints)
        })

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "data": data
    }

@router.get("/{id}")
def get_institution_digital_twin(id: str, db: Session = Depends(get_db)):
    """
    Returns full Institution Digital Twin with all connected records.
    """
    inst = db.query(Institution).filter(or_(Institution.id == id, Institution.permanent_id == id)).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    apps = [{
        "id": a.id, "type": a.type, "category": a.category, "current_stage": a.current_stage,
        "status": a.status, "progress": a.progress, "owner": a.owner,
        "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
        "due_date": a.due_date.isoformat() if a.due_date else None,
        "deficiency_count": a.deficiency_count
    } for a in inst.applications]

    docs = [{
        "id": d.id, "name": d.name, "document_type": d.document_type, "status": d.status,
        "confidence": d.confidence, "findings": d.findings, "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
        "authority_ref": d.authority_ref, "verification_source": d.verification_source, "is_anomaly": d.is_anomaly
    } for d in inst.documents]

    comps = [{
        "id": c.id, "title": c.title, "category": c.category, "due_date": c.due_date.isoformat(),
        "status": c.status, "responsible_party": c.responsible_party, "evidence_file": c.evidence_file,
        "review_notes": c.review_notes
    } for c in inst.compliance_obligations]

    cases = [{
        "id": c.id, "case_number": c.case_number, "bureau": c.bureau, "category": c.category,
        "summary": c.summary, "status": c.status, "received_date": c.received_date.isoformat() if c.received_date else None,
        "assigned_to": c.assigned_to, "related_case_id": c.related_case_id, "overlap_score": c.overlap_score
    } for c in inst.complaints]

    tasks = [{
        "id": t.id, "title": t.title, "category": t.category, "priority": t.priority,
        "status": t.status, "due_date": t.due_date.isoformat() if t.due_date else None,
        "assigned_to": t.assigned_to, "bureau": t.bureau
    } for t in inst.tasks]

    # Recent Audit Logs for this institution and its linked records (True Digital Twin timeline)
    related_ids = [inst.id, inst.permanent_id] + [a.id for a in inst.applications] + [d.id for d in inst.documents] + [c.id for c in inst.compliance_obligations] + [c.id for c in inst.complaints]
    audits = db.query(AuditLog).filter(or_(
        AuditLog.entity_id.in_(related_ids),
        AuditLog.details.ilike(f"%{inst.name}%")
    )).order_by(desc(AuditLog.timestamp)).limit(15).all()

    audit_records = [{
        "id": a.id, "timestamp": a.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "actor": a.actor, "role": a.role, "action": a.action, "record": a.entity_id, "detail": a.details
    } for a in audits]

    return {
        "institution": {
            "id": inst.id,
            "permanent_id": inst.permanent_id,
            "name": inst.name,
            "state": inst.state,
            "district": inst.district,
            "city": inst.city,
            "address": inst.address,
            "category": inst.category,
            "institution_type": inst.institution_type,
            "affiliation": inst.affiliation,
            "website": inst.website,
            "approval_status": inst.approval_status,
            "approval_period": inst.approval_period,
            "programmes_count": inst.programmes_count,
            "total_intake": inst.total_intake,
            "data_source": inst.data_source,
            "verified_status": inst.verified_status,
            "last_verified": inst.last_verified.isoformat() if inst.last_verified else None
        },
        "applications": apps,
        "documents": docs,
        "compliance": comps,
        "complaints": cases,
        "tasks": tasks,
        "activity_timeline": audit_records
    }

@router.post("", response_model=InstitutionResponse)
def create_institution(payload: InstitutionCreate, db: Session = Depends(get_db)):
    # Validate unique permanent_id
    existing = db.query(Institution).filter(Institution.permanent_id == payload.permanent_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Institution with Permanent ID {payload.permanent_id} already exists.")

    new_id = payload.id or f"INST-{uuid.uuid4().hex[:6].upper()}"
    inst = Institution(
        id=new_id,
        name=payload.name,
        permanent_id=payload.permanent_id,
        state=payload.state,
        district=payload.district,
        city=payload.city,
        address=payload.address or "",
        category=payload.category,
        institution_type=payload.institution_type,
        affiliation=payload.affiliation,
        website=payload.website,
        approval_status=payload.approval_status,
        approval_period=payload.approval_period,
        programmes_count=payload.programmes_count,
        total_intake=payload.total_intake,
        data_source=payload.data_source,
        verified_status=payload.verified_status,
        last_verified=date.today()
    )
    db.add(inst)

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor="Admin Officer",
        role="Administrator",
        action="Created Institution Record",
        entity_type="Institution",
        entity_id=inst.id,
        details=f"Added {inst.name} ({inst.permanent_id}) to institutional directory."
    )
    db.add(audit)
    db.commit()
    db.refresh(inst)
    return inst

@router.post("/import-csv", response_model=InstitutionImportSummary)
async def import_institutions_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Imports institutions from CSV with data validation and duplicate detection.
    """
    content = await file.read()
    decoded = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))

    created = 0
    updated = 0
    skipped = 0
    rejected = 0
    errors = []
    total = 0

    for idx, row in enumerate(reader, start=2):
        total += 1
        perm_id = (row.get("Permanent ID") or row.get("permanent_id") or "").strip()
        name = (row.get("Institution Name") or row.get("name") or "").strip()
        state = (row.get("State") or row.get("state") or "").strip()
        district = (row.get("District") or row.get("district") or "").strip()
        category = (row.get("Category") or row.get("category") or "Engineering and Technology").strip()
        inst_type = (row.get("Institution Type") or row.get("institution_type") or "Private-Self Financed").strip()

        if not perm_id or not name or not state:
            rejected += 1
            errors.append(f"Row {idx}: Missing mandatory fields (Permanent ID, Name, or State).")
            continue

        existing = db.query(Institution).filter(Institution.permanent_id == perm_id).first()
        if existing:
            skipped += 1
            continue

        new_inst = Institution(
            id=f"INST-{uuid.uuid4().hex[:6].upper()}",
            name=name,
            permanent_id=perm_id,
            state=state,
            district=district or state,
            city=(row.get("City") or row.get("city") or district or state).strip(),
            address=(row.get("Address") or row.get("address") or "").strip(),
            category=category,
            institution_type=inst_type,
            affiliation=(row.get("Affiliation") or row.get("affiliation") or "").strip(),
            website=(row.get("Website") or row.get("website") or "").strip(),
            approval_status=(row.get("Status") or row.get("approval_status") or "Approved").strip(),
            approval_period=(row.get("Approval Period") or row.get("approval_period") or "2026-2027").strip(),
            programmes_count=int(row.get("Programmes") or row.get("programmes_count") or 0),
            total_intake=int(row.get("Intake") or row.get("total_intake") or 0),
            data_source="CSV Import",
            verified_status="Imported / Unverified",
            last_verified=date.today()
        )
        db.add(new_inst)
        created += 1

    if created > 0:
        audit = AuditLog(
            id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
            actor="Admin Officer",
            role="Administrator",
            action="Batch CSV Import",
            entity_type="Institution",
            entity_id=f"BATCH-{created}",
            details=f"Imported {created} records, skipped {skipped} duplicates, rejected {rejected} errors."
        )
        db.add(audit)
        db.commit()

    return InstitutionImportSummary(
        total_rows=total,
        created=created,
        updated=updated,
        skipped_duplicates=skipped,
        rejected_errors=rejected,
        errors=errors[:10]
    )

@router.get("/export-csv")
def export_institutions_csv(db: Session = Depends(get_db)):
    """
    Exports all current institution records as a formatted CSV.
    """
    institutions = db.query(Institution).order_by(Institution.name).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Institution ID", "Permanent ID", "Institution Name", "State", "District",
        "City", "Category", "Institution Type", "Affiliation", "Approval Status",
        "Approval Period", "Programmes", "Total Intake", "Data Source", "Verified Status"
    ])
    for inst in institutions:
        writer.writerow([
            inst.id, inst.permanent_id, inst.name, inst.state, inst.district,
            inst.city, inst.category, inst.institution_type, inst.affiliation or "",
            inst.approval_status, inst.approval_period, inst.programmes_count,
            inst.total_intake, inst.data_source, inst.verified_status
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=aicte_institutions_directory.csv"}
    )
