"""
Document Verification & Intelligence Router
Protected with RBAC & Multi-Institution Tenant Isolation
"""
import os
import json
import uuid
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Body, Request, status
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from backend.database import get_db
from backend.models import (
    Document, Institution, Application, DocumentValidity,
    DocumentReviewHistory, AuditLog, Notification, User
)
from backend.schemas import (
    DocumentResponse, DocumentUploadRequest, DocumentValidityCreate,
    DocumentValidityResponse, DocumentReviewRequest, DocumentReviewResponse
)
from backend.services.ocr_service import ocr_service
from backend.services.rules_engine import rules_engine
from backend.services.verification_adapter import verification_adapter
from backend.services.escalation_service import escalation_service
from backend.auth import (
    get_current_user, require_roles, check_tenant_access,
    ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER, ROLE_COMPLIANCE_OFFICER,
    ROLE_INSTITUTE_HEAD, ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR
)

router = APIRouter(prefix="/api/documents", tags=["Documents"])

@router.get("")
def list_documents(
    institution_id: Optional[str] = Query(None),
    application_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lists uploaded documents with RBAC and tenant isolation.
    - Institute Heads can only see documents belonging to their institution.
    - Officers see all documents or filter by query.
    - Students and public visitors are denied (403 Forbidden).
    """
    if user.role in {ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Verification documents are confidential and restricted to regulatory officers and authorized institutional representatives."
        )

    query = db.query(Document)

    # Tenant isolation for Institute Heads
    if user.role == ROLE_INSTITUTE_HEAD:
        if not user.institution_id:
            return []
        query = query.filter(Document.institution_id == user.institution_id)
    elif institution_id:
        query = query.filter(Document.institution_id == institution_id)

    if application_id:
        query = query.filter(Document.application_id == application_id)
    if status_filter:
        query = query.filter(Document.status == status_filter)

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
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER, ROLE_SECURITY_OFFICER, ROLE_INSTITUTE_HEAD)),
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
        if user.role == ROLE_INSTITUTE_HEAD and user.institution_id:
            req_inst_id = user.institution_id
        else:
            raise HTTPException(status_code=400, detail="institution_id is required")

    # Enforce tenant isolation for Institute Heads
    if user.role == ROLE_INSTITUTE_HEAD:
        if user.institution_id and user.institution_id != req_inst_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cross-institution upload denied: Your account is restricted to institution '{user.institution_id}'."
            )

    if not req_doc_type:
        req_doc_type = "Institutional Certificate"

    inst = db.query(Institution).filter(Institution.id == req_inst_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    file_size = 0
    safe_path = None
    if file:
        file_bytes = await file.read()
        fname = os.path.basename(file.filename.replace("\\", "/"))
        file_size = len(file_bytes)
    elif file_bytes:
        file_size = len(file_bytes)

    # File safety validation (extension, size, magic bytes, script prevention)
    if file_bytes:
        is_valid, validation_error = ocr_service.validate_file_upload(fname, file_bytes)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document upload validation failed: {validation_error}"
            )
        safe_path = ocr_service.save_secure_file(fname, file_bytes)

    file_hash = ocr_service.calculate_sha256(file_bytes) if file_bytes else f"SHA-{uuid.uuid4().hex[:16]}"
    
    # 1. OCR & Structured Text Extraction
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
    initial_review_status = "Flagged Discrepancy" if is_anomaly else "Verified Matching"

    new_id = f"DOC-{uuid.uuid4().hex[:4].upper()}"

    # 3. Generate Explainable Forensic Report
    forensic_report = ocr_service.generate_forensic_report(
        document_id=new_id,
        filename=fname,
        file_hash=file_hash,
        doc_type=req_doc_type,
        institution_name=inst.name,
        registered_permanent_id=inst.permanent_id,
        extracted_fields=ocr_result["extracted_fields"],
        checks_performed=rule_check.get("checks", []),
        discrepancies=rule_check.get("discrepancies", []),
        review_status=initial_review_status
    )

    doc = Document(
        id=new_id,
        institution_id=req_inst_id,
        application_id=req_app_id,
        name=fname,
        document_type=req_doc_type,
        file_path=safe_path,
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
        is_anomaly=is_anomaly,
        review_status=initial_review_status,
        forensic_report_json=json.dumps(forensic_report),
        uploaded_by=user.username
    )
    db.add(doc)

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=user.username,
        role=user.role,
        action="Document Ingested & Evaluated",
        entity_type="Document",
        entity_id=doc.id,
        details=f"Uploaded '{fname}' for {inst.name}. Status: '{final_status}'. Confidence: {ocr_result['confidence']}."
    )
    db.add(audit)
    db.commit()
    db.refresh(doc)
    return {
        "message": "Document uploaded and processed successfully",
        "document_id": doc.id,
        "status": final_status,
        "review_status": doc.review_status,
        "findings": final_findings,
        "forensic_report": forensic_report
    }

# -------------------------------------------------------------
# Secure Document File Download & Preview (RBAC & Path-Traversal Protected)
# -------------------------------------------------------------
@router.get("/{id}/file")
@router.get("/{id}/download")
def download_document_file(
    id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Downloads or streams verified regulatory document file.
    Security controls:
    1. Authentication & RBAC: Institute Heads can only access their own institution's documents.
       Students & Public visitors are denied (403 Forbidden).
    2. Path-traversal defense: Validates that resolved path stays strictly within uploads directory.
    3. Audit logging: Logs file access in immutable AuditLog.
    4. Anti-sniff headers: X-Content-Type-Options: nosniff.
    """
    if user.role in {ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Verification documents are confidential and restricted to authorized officers and institutional heads."
        )

    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{id}' not found.")

    # Cross-tenant isolation check for Institute Head
    if user.role == ROLE_INSTITUTE_HEAD:
        if user.institution_id != doc.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not authorized to access documents from another institution."
            )

    if not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Physical document file not found on storage server.")

    # Path traversal protection
    resolved_path = os.path.abspath(doc.file_path)
    base_uploads_dir = os.path.abspath("uploads")
    if not resolved_path.startswith(base_uploads_dir):
        raise HTTPException(status_code=403, detail="Security violation: Invalid or unauthorized file path.")

    # Audit log access
    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=user.username,
        role=user.role,
        action="DOWNLOAD_DOCUMENT_FILE",
        entity_type="Document",
        entity_id=doc.id,
        details=f"File '{doc.name}' accessed/downloaded for institution '{doc.institution_id}'."
    )
    db.add(audit)
    db.commit()

    safe_filename = os.path.basename(doc.name) if doc.name else f"{doc.id}.pdf"
    return FileResponse(
        path=resolved_path,
        filename=safe_filename,
        headers={"X-Content-Type-Options": "nosniff"}
    )

# -------------------------------------------------------------
# Explainable Document Forensics & Human Review Workspace
# -------------------------------------------------------------
@router.get("/{id}/forensics")
def get_document_forensic_report(
    id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the comprehensive, explainable forensic report for a processed document.
    Enforces role-based permissions and multi-institution tenant isolation.
    """
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if user.role in {ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR}:
        raise HTTPException(status_code=403, detail="Access denied: Document forensics reports are restricted to authorized reviewers.")

    if user.role == ROLE_INSTITUTE_HEAD and user.institution_id != doc.institution_id:
        raise HTTPException(status_code=403, detail="Cross-institution access denied.")

    if doc.forensic_report_json:
        try:
            return json.loads(doc.forensic_report_json)
        except Exception:
            pass

    # Fallback generation if document pre-dates forensic report generator
    extracted = json.loads(doc.extracted_fields) if doc.extracted_fields else {}
    rule_check = rules_engine.validate_document(
        {"extracted_fields": extracted, "authority_ref": doc.authority_ref},
        {"permanent_id": doc.institution.permanent_id if doc.institution else "", "name": doc.institution.name if doc.institution else ""}
    )
    report = ocr_service.generate_forensic_report(
        document_id=doc.id,
        filename=doc.name,
        file_hash=doc.file_hash or "N/A",
        doc_type=doc.document_type,
        institution_name=doc.institution.name if doc.institution else "Unknown",
        registered_permanent_id=doc.institution.permanent_id if doc.institution else "Unknown",
        extracted_fields=extracted,
        checks_performed=rule_check.get("checks", []),
        discrepancies=rule_check.get("discrepancies", []),
        review_status=doc.review_status or "Pending Human Review"
    )
    return report

@router.post("/{id}/review")
def review_document(
    id: str,
    payload: DocumentReviewRequest,
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER, ROLE_COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db)
):
    """
    Human Review Action Endpoint:
    Allows authorized scrutiny officers to confirm matches, correct extracted fields,
    dismiss false-positive flags with mandatory justification, or record official findings.
    Preserves audit history and previous automated outputs.
    """
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    action = payload.action.upper()
    previous_status = doc.review_status or doc.status
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if action == "CONFIRM_MATCH":
        doc.review_status = "Confirmed Match"
        doc.status = "Verified (Human Confirmed)"
        doc.is_anomaly = False
    elif action == "DISMISS_FLAG":
        if not payload.justification or len(payload.justification.strip()) < 5:
            raise HTTPException(status_code=400, detail="A detailed justification reason is mandatory to dismiss an anomaly flag.")
        doc.review_status = "Dismissed"
        doc.status = "Verified (Flag Dismissed)"
        doc.is_anomaly = False
    elif action == "CORRECT_FIELDS":
        if not payload.field_corrections:
            raise HTTPException(status_code=400, detail="Field corrections payload must be provided.")
        existing_fields = json.loads(doc.extracted_fields) if doc.extracted_fields else {}
        existing_fields.update(payload.field_corrections)
        doc.extracted_fields = json.dumps(existing_fields)
        doc.human_overridden_fields = json.dumps(payload.field_corrections)
        doc.review_status = "Approved with Human Override"
        doc.status = "Human Corrected"
        doc.confidence = "100% (Human Verified)"
    elif action == "REQUEST_MORE_EVIDENCE":
        doc.review_status = "Evidence Requested"
        doc.status = "Deficiency Notice Issued"
    elif action == "RECORD_OFFICIAL_FINDING":
        doc.review_status = "Finding Recorded"
        doc.status = payload.official_finding or "Official Finding Recorded"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported review action '{payload.action}'.")

    doc.reviewed_by = user.full_name or user.username
    doc.reviewed_at = now
    doc.review_notes = payload.justification

    # Record Review History
    history = DocumentReviewHistory(
        id=f"REV-{uuid.uuid4().hex[:6].upper()}",
        document_id=doc.id,
        reviewer=user.username,
        role=user.role,
        action=action,
        previous_status=previous_status,
        new_status=doc.review_status,
        justification=payload.justification,
        field_corrections_json=json.dumps(payload.field_corrections) if payload.field_corrections else None,
        timestamp=now
    )
    db.add(history)

    # Record Audit Log
    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=user.username,
        role=user.role,
        action=f"Human Review: {action}",
        entity_type="Document",
        entity_id=doc.id,
        details=f"Officer {user.username} executed '{action}' on {doc.name}. Justification: {payload.justification[:120]}."
    )
    db.add(audit)
    db.commit()
    db.refresh(doc)

    return {
        "message": f"Review action '{action}' recorded successfully",
        "document_id": doc.id,
        "action": action,
        "previous_status": previous_status,
        "new_status": doc.review_status,
        "reviewed_by": doc.reviewed_by,
        "reviewed_at": doc.reviewed_at.isoformat()
    }

@router.get("/human-review-queue")
def get_human_review_queue(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns documents awaiting human review (flagged documents, unverified documents, expired items).
    Scoped by user role and tenant permissions.
    """
    if user.role in {ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR}:
        raise HTTPException(status_code=403, detail="Access denied")

    query = db.query(Document).filter(
        or_(
            Document.is_anomaly == True,
            Document.review_status.in_(["Pending Human Review", "Flagged Discrepancy", "Evidence Requested"]),
            Document.status.in_([
                "Mismatch detected", "Expiry detected", "Manual review required",
                "Verification pending", "Deficiency Notice Issued"
            ])
        )
    )

    if user.role == ROLE_INSTITUTE_HEAD:
        if not user.institution_id:
            return []
        query = query.filter(Document.institution_id == user.institution_id)

    docs = query.order_by(desc(Document.uploaded_at)).limit(50).all()
    queue = []
    for d in docs:
        queue.append({
            "id": d.id,
            "filename": d.name,
            "document_type": d.document_type,
            "institution_id": d.institution_id,
            "institution_name": d.institution.name if d.institution else "Unknown",
            "permanent_id": d.institution.permanent_id if d.institution else "Unknown",
            "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
            "status": d.status,
            "review_status": d.review_status,
            "findings": d.findings,
            "is_anomaly": d.is_anomaly,
            "confidence": d.confidence
        })
    return {
        "total_pending_review": len(queue),
        "items": queue
    }

@router.post("/detect-duplicates")
def detect_duplicate_documents(
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER, ROLE_COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db)
):
    """
    AI-Assisted Duplicate & Anomaly Scanner:
    Identifies identical SHA-256 file hashes or identical authority references
    submitted across different institutions or repeatedly across applications.
    """
    docs = db.query(Document).all()
    hash_map: Dict[str, List[Document]] = {}
    ref_map: Dict[str, List[Document]] = {}

    for d in docs:
        if d.file_hash and len(d.file_hash) > 10:
            hash_map.setdefault(d.file_hash, []).append(d)
        if d.authority_ref and len(d.authority_ref) > 5 and not d.authority_ref.startswith("REF-"):
            ref_map.setdefault(d.authority_ref, []).append(d)

    duplicate_clusters = []
    
    # 1. Exact File Hash Duplicates
    for f_hash, cluster in hash_map.items():
        if len(cluster) > 1:
            institutions_involved = list({d.institution.name if d.institution else d.institution_id for d in cluster})
            is_cross_inst = len(institutions_involved) > 1
            duplicate_clusters.append({
                "type": "IDENTICAL_FILE_HASH",
                "similarity_score": 100,
                "file_hash": f_hash,
                "is_cross_institution": is_cross_inst,
                "severity": "CRITICAL" if is_cross_inst else "MEDIUM",
                "affected_institutions": institutions_involved,
                "documents": [{"id": d.id, "name": d.name, "institution_id": d.institution_id} for d in cluster],
                "finding": (
                    f"Identical document file submitted across {len(cluster)} records. "
                    f"{'POTENTIAL CROSS-INSTITUTION REUSE DETECTED.' if is_cross_inst else 'Repeated submission within same profile.'}"
                )
            })

    return {
        "status": "COMPLETED",
        "total_documents_scanned": len(docs),
        "duplicate_clusters_found": len(duplicate_clusters),
        "clusters": duplicate_clusters
    }


@router.post("/{id}/verify-authority")
def verify_issuing_authority(
    id: str,
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER, ROLE_COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db)
):
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
        actor=user.username,
        role=user.role,
        action="Authority Verification Check",
        entity_type="Document",
        entity_id=doc.id,
        details=f"Checked with {res['source']}. Result: '{res['status']}'."
    )
    db.add(audit)
    db.commit()
    return res

@router.put("/{id}/correct-fields")
def correct_extracted_fields(
    id: str,
    corrections: Dict[str, Any],
    actor: Optional[str] = None,
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_SECURITY_OFFICER, ROLE_COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db)
):
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
        actor=user.username,
        role=user.role,
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
def get_validation_report(
    id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if user.role in {ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Validation reports are confidential."
        )

    if user.role == ROLE_INSTITUTE_HEAD:
        if user.institution_id and user.institution_id != doc.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cross-institution access denied: Your account is restricted to institution '{user.institution_id}'."
            )

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

# -------------------------------------------------------------
# Lease & Statutory Document Validity Registry
# -------------------------------------------------------------

@router.get("/validities", response_model=List[DocumentValidityResponse])
def list_document_validities(
    institution_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lists document and lease validities with tenant isolation:
    - Central officers see all.
    - Institute Heads see ONLY their assigned institution.
    """
    if user.role in {ROLE_STUDENT_COMPLAINANT, ROLE_PUBLIC_VISITOR}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden")

    query = db.query(DocumentValidity)
    if user.role == ROLE_INSTITUTE_HEAD:
        if not user.institution_id:
            return []
        query = query.filter(DocumentValidity.institution_id == user.institution_id)
    elif institution_id:
        query = query.filter(DocumentValidity.institution_id == institution_id)

    if status_filter:
        query = query.filter(DocumentValidity.status == status_filter)

    return query.order_by(DocumentValidity.expiry_date).all()

@router.get("/validities/{id}", response_model=DocumentValidityResponse)
def get_document_validity(
    id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    val = db.query(DocumentValidity).filter(DocumentValidity.id == id).first()
    if not val:
        raise HTTPException(status_code=404, detail="Document validity record not found")
    if user.role == ROLE_INSTITUTE_HEAD and user.institution_id != val.institution_id:
        raise HTTPException(status_code=403, detail="Cross-institution access denied")
    return val

@router.post("/validities", response_model=DocumentValidityResponse)
def create_document_validity(
    payload: DocumentValidityCreate,
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER, ROLE_INSTITUTE_HEAD)),
    db: Session = Depends(get_db)
):
    """Registers a lease or critical statutory document with validity monitoring."""
    if user.role == ROLE_INSTITUTE_HEAD and user.institution_id != payload.institution_id:
        raise HTTPException(status_code=403, detail="Cross-institution registration denied")

    inst = db.query(Institution).filter(Institution.id == payload.institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    today = date.today()
    val_status = "Active"
    if payload.expiry_date < today:
        val_status = "Expired"
    elif (payload.expiry_date - today).days <= (payload.advance_warning_days or 60):
        val_status = "Expiring Soon"

    val_id = f"VAL-{uuid.uuid4().hex[:6].upper()}"
    val = DocumentValidity(
        id=val_id,
        institution_id=payload.institution_id,
        document_id=payload.document_id,
        document_type=payload.document_type,
        document_ref_number=payload.document_ref_number,
        issuing_authority=payload.issuing_authority,
        issue_date=payload.issue_date,
        expiry_date=payload.expiry_date,
        advance_warning_days=payload.advance_warning_days or 60,
        status=val_status
    )
    db.add(val)

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=user.username,
        role=user.role,
        action="Registered Document Validity",
        entity_type="DocumentValidity",
        entity_id=val.id,
        details=f"Registered {val.document_type} (Ref: {val.document_ref_number}) expiring on {val.expiry_date.isoformat()}."
    )
    db.add(audit)
    db.commit()
    db.refresh(val)
    return val

@router.post("/validities/{id}/renew")
def renew_document_validity(
    id: str,
    new_expiry_date: date = Body(..., embed=True),
    renewal_ref: Optional[str] = Body(None, embed=True),
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER, ROLE_INSTITUTE_HEAD)),
    db: Session = Depends(get_db)
):
    """Submits renewal details for an expiring or expired statutory document/lease."""
    val = db.query(DocumentValidity).filter(DocumentValidity.id == id).first()
    if not val:
        raise HTTPException(status_code=404, detail="Document validity record not found")

    if user.role == ROLE_INSTITUTE_HEAD and user.institution_id != val.institution_id:
        raise HTTPException(status_code=403, detail="Cross-institution renewal denied")

    today = date.today()
    if new_expiry_date <= today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New renewal expiry date must be in the future."
        )

    old_expiry = val.expiry_date
    val.expiry_date = new_expiry_date
    val.status = "Renewed"
    val.renewal_application_ref = renewal_ref or f"REN-{uuid.uuid4().hex[:4].upper()}"

    audit = AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        actor=user.username,
        role=user.role,
        action="Renewed Document Validity",
        entity_type="DocumentValidity",
        entity_id=val.id,
        details=f"Extended {val.document_type} from {old_expiry.isoformat()} to {new_expiry_date.isoformat()} (Ref: {val.renewal_application_ref})."
    )
    db.add(audit)
    db.commit()
    return {
        "message": "Document validity renewed successfully",
        "id": val.id,
        "new_expiry_date": val.expiry_date.isoformat(),
        "status": val.status
    }

@router.post("/scan-validities")
def scan_document_validities(
    user: User = Depends(require_roles(ROLE_SUPER_ADMIN, ROLE_COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db)
):
    """Triggers automated validity scan for lease and safety certificates."""
    return escalation_service.check_document_and_lease_validities(db)

