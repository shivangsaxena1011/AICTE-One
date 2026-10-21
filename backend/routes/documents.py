"""
Document Verification & Intelligence Router
"""
import json
import uuid
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models import Document, Institution, Application, AuditLog
from backend.schemas import DocumentResponse, DocumentUploadRequest
from backend.services.ocr_service import ocr_service
from backend.services.rules_engine import rules_engine
from backend.services.verification_adapter import verification_adapter

router = APIRouter(prefix="/api/documents", tags=["Documents"])

@router.get("")
def list_documents(
    institution_id: Optional[str] = Query(None),
    application_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Document)
    if institution_id:
        query = query.filter(Document.institution_id == institution_id)
    if application_id:
        query = query.filter(Document.application_id == application_id)
    if status:
        query = query.filter(Document.status == status)

    docs = query.order_by(desc(Document.uploaded_at)).all()
    results = []
    for d in docs:
        extracted = {}
        if d.extracted_fields:
            try:
                extracted = json.loads(d.extracted_fields)
            except Exception:
                extracted = {"raw": d.extracted_fields}

        results.append({
            "id": d.id,
            "institution_id": d.institution_id,
            "institution_name": d.institution.name if d.institution else "Unknown",
            "permanent_id": d.institution.permanent_id if d.institution else "Unknown",
            "application_id": d.application_id,
            "name": d.name,
            "document_type": d.document_type,
            "file_size": d.file_size,
            "file_hash": d.file_hash,
            "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
            "status": d.status,
            "confidence": d.confidence,
            "extracted_fields": extracted,
            "findings": d.findings,
            "issuing_authority": d.issuing_authority,
            "authority_ref": d.authority_ref,
            "verification_source": d.verification_source,
            "verification_response": d.verification_response,
            "is_anomaly": d.is_anomaly
        })
    return results

@router.post("/upload")
@router.post("/ingest")
async def upload_document(
    request: Request,
    institution_id: Optional[str] = Form(None),
    application_id: Optional[str] = Form(None),
    document_type: Optional[str] = Form(None),
    authority_ref: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    filename: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    content_type = request.headers.get("content-type", "")
    req_inst_id = institution_id
    req_app_id = application_id
    req_doc_type = document_type
    req_auth_ref = authority_ref
    fname = filename or "Document.pdf"
    file_bytes = b""

    if "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict):
                req_inst_id = body.get("institution_id") or req_inst_id
                req_app_id = body.get("application_id") or req_app_id
                req_doc_type = body.get("document_type") or req_doc_type
                req_auth_ref = body.get("authority_ref") or req_auth_ref
                fname = body.get("name") or body.get("filename") or fname
                if body.get("file_base64"):
                    import base64
                    try:
                        file_bytes = base64.b64decode(body["file_base64"])
                    except Exception:
                        pass
        except Exception:
            pass

    if not req_inst_id:
        raise HTTPException(status_code=400, detail="institution_id is required")
    if not req_doc_type:
        req_doc_type = "Institutional Certificate"

    inst = db.query(Institution).filter(Institution.id == req_inst_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    file_size = 0
    if file:
        file_bytes = await file.read()
        fname = file.filename
        file_size = len(file_bytes)
    elif file_bytes:
        file_size = len(file_bytes)

    file_hash = ocr_service.calculate_sha256(file_bytes) if file_bytes else f"SHA-{uuid.uuid4().hex[:16]}"
    
    # 1. OCR Extraction
    ocr_result = ocr_service.extract_document_fields(
        filename=fname,
        doc_type=req_doc_type,
        institution_name=inst.name,
        permanent_id=inst.permanent_id,
        content=file_bytes
    )

    if req_auth_ref:
        ocr_result["authority_ref"] = req_auth_ref

    # 2. Regulatory Rules Engine Check
    doc_dict = {
        "extracted_fields": ocr_result["extracted_fields"],
        "authority_ref": ocr_result["authority_ref"]
    }
    inst_dict = {
        "permanent_id": inst.permanent_id,
        "name": inst.name
    }
    rule_check = rules_engine.validate_document(doc_dict, inst_dict)

    final_status = rule_check["status"]
    final_findings = f"{ocr_result['findings']} | {rule_check['findings']}"
    is_anomaly = ocr_result["is_anomaly"] or rule_check["is_anomaly"]

    new_id = f"DOC-{uuid.uuid4().hex[:4].upper()}"
    doc = Document(
        id=new_id,
        institution_id=req_inst_id,
        application_id=req_app_id,
        name=fname,
        document_type=req_doc_type,
        file_size=file_size,
        file_hash=file_hash,
        uploaded_at=date.today(),
        status=final_status,
        confidence=ocr_result["confidence"],
        extracted_fields=json.dumps(ocr_result["extracted_fields"]),
        findings=final_findings,
        issuing_authority=ocr_result["issuing_authority"],
        authority_ref=ocr_result["authority_ref"],
        verification_source="AICTE Regulatory Rules Engine",
        verification_response="Preliminary automated extraction and consistency check completed.",
        is_anomaly=is_anomaly
    )
    db.add(doc)

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor="Document Officer",
        role="Verification Specialist",
        action="Document Ingested & Evaluated",
        entity_type="Document",
        entity_id=doc.id,
        details=f"Uploaded '{fname}' for {inst.name}. Status: '{final_status}'. Confidence: {ocr_result['confidence']}."
    )
    db.add(audit)
    db.commit()
    db.refresh(doc)
    return {"message": "Document uploaded and processed successfully", "document_id": doc.id, "status": final_status, "findings": final_findings}

@router.post("/{id}/verify-authority")
def verify_issuing_authority(id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    res = verification_adapter.verify_document_with_authority(
        doc_type=doc.document_type,
        authority_ref=doc.authority_ref or doc.id,
        permanent_id=doc.institution.permanent_id if doc.institution else "1-000000"
    )

    doc.status = res["status"]
    doc.verification_source = res["source"]
    doc.verification_response = f"{res['evidence']} {res['notes']}"

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor="Verification Adapter",
        role="Authority Gateway",
        action="Authority Verification Check",
        entity_type="Document",
        entity_id=doc.id,
        details=f"Checked with {res['source']}. Result: '{res['status']}'."
    )
    db.add(audit)
    db.commit()
    return res

@router.put("/{id}/correct-fields")
def correct_extracted_fields(id: str, corrections: Dict[str, Any], actor: str = "Verification Officer", db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    existing_fields = {}
    if doc.extracted_fields:
        try:
            existing_fields = json.loads(doc.extracted_fields)
        except Exception:
            pass

    existing_fields.update(corrections)
    doc.extracted_fields = json.dumps(existing_fields)
    doc.confidence = "100% (Human Verified)"

    # Re-evaluate with rules engine
    rule_check = rules_engine.validate_document(
        {"extracted_fields": existing_fields, "authority_ref": doc.authority_ref},
        {"permanent_id": doc.institution.permanent_id if doc.institution else "", "name": doc.institution.name if doc.institution else ""}
    )
    doc.status = rule_check["status"]
    doc.findings = f"Human verified: {rule_check['findings']}"

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=actor,
        role="Verification Officer",
        action="Human Correction of Fields",
        entity_type="Document",
        entity_id=doc.id,
        details=f"Human officer corrected fields in {doc.name}. Status updated to '{doc.status}'."
    )
    db.add(audit)
    db.commit()
    return {"message": "Fields updated and re-validated", "status": doc.status}

@router.get("/{id}/validation-report")
@router.get("/{id}/report")
def get_validation_report(id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    inst = doc.institution
    app = doc.application

    report = {
        "report_id": f"REP-DOC-{doc.id}",
        "generated_at": datetime.now(timezone.utc).strftime("%d-%b-%Y %H:%M:%S UTC"),
        "institution": {
            "name": inst.name,
            "permanent_id": inst.permanent_id,
            "state": inst.state,
            "district": inst.district,
            "category": inst.category
        },
        "application": {
            "id": app.id if app else "Direct Document Submission",
            "type": app.type if app else "Institutional Compliance Document",
            "stage": app.current_stage if app else "N/A"
        },
        "document": {
            "id": doc.id,
            "filename": doc.name,
            "document_type": doc.document_type,
            "file_hash": doc.file_hash,
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            "extraction_confidence": doc.confidence,
            "issuing_authority": doc.issuing_authority,
            "authority_reference": doc.authority_ref,
            "verification_status": doc.status,
            "verification_source": doc.verification_source,
            "verification_response": doc.verification_response,
            "findings_and_evidence": doc.findings,
            "is_anomaly": doc.is_anomaly
        },
        "extracted_fields": json.loads(doc.extracted_fields) if doc.extracted_fields else {},
        "official_disposition": "Requires authorized administrative sign-off prior to approval advancement."
    }
    return report
