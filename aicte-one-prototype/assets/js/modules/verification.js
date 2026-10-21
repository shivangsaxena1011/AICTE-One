/**
 * Module 7: AI-Powered Document Verification & Intelligence
 */
const VerificationModule = {
  selectedDocId: "DOC-7812",

  async render(params = {}) {
    const docs = await API.getDocuments();
    if (params.id) {
      this.selectedDocId = params.id;
    }
    const activeDoc = docs.find(d => d.id === this.selectedDocId) || docs[0];

    const rows = docs.map(d => `
      <tr style="cursor:pointer;background:${d.id === activeDoc.id ? '#eff6ff' : ''}" onclick="VerificationModule.selectDoc('${d.id}')">
        <td>
          <div class="primary-cell-text">${escapeHtml(d.name)}</div>
          <div class="secondary-cell-text">${d.id} · ${escapeHtml(d.document_type)}</div>
        </td>
        <td>
          <div class="primary-cell-text">${escapeHtml(d.institution_name)}</div>
        </td>
        <td><b>${d.confidence}</b></td>
        <td>${renderPill(d.status)}</td>
        <td>
          <button class="btn sm" onclick="event.stopPropagation();VerificationModule.openReportModal('${d.id}')">Report</button>
        </td>
      </tr>
    `).join("");

    const extracted = activeDoc.extracted_fields || {};

    return `
      <div class="page-header">
        <div>
          <div class="page-eyebrow">Document Intelligence & Forensic Review</div>
          <h1>AI-Powered Document Verification</h1>
          <p>Extract fields with optical recognition, cross-verify against issuing authorities, and flag statutory discrepancies.</p>
        </div>
        <div class="header-action-group">
          <button class="btn" onclick="VerificationModule.openReportModal('${activeDoc.id}')">⎙ Printable Validation Report</button>
          <button class="btn primary" onclick="VerificationModule.openUploadModal()">＋ Ingest Document for Verification</button>
        </div>
      </div>

      <!-- Quick Metrics -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-header"><span>DOCUMENTS INGESTED</span><span>◈</span></div>
          <div class="stat-number">${docs.length}</div>
          <div class="stat-subtext">Across all applications</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>VERIFIED AUTHENTIC</span><span style="color:#15803d">✓</span></div>
          <div class="stat-number">${docs.filter(d => /verified/i.test(d.status)).length}</div>
          <div class="stat-subtext">Verified with issuing source</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>DISCREPANCIES FLAGGED</span><span style="color:#b91c1c">!</span></div>
          <div class="stat-number">${docs.filter(d => /mismatch|expiry|anomal/i.test(d.status)).length}</div>
          <div class="stat-subtext">Require human adjudication</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>PENDING CHECK</span><span>◷</span></div>
          <div class="stat-number">${docs.filter(d => /pending/i.test(d.status)).length}</div>
          <div class="stat-subtext">Authority synchronization</div>
        </div>
      </div>

      <!-- Main Layout -->
      <div class="grid-2">
        <!-- Verification Inspector Panel for Active Document -->
        <div class="panel">
          <div class="panel-header">
            <div>
              <h3>Document Verification Dossier · ${activeDoc.id}</h3>
              <p>${escapeHtml(activeDoc.name)} (${escapeHtml(activeDoc.document_type)})</p>
            </div>
            ${renderPill(activeDoc.status)}
          </div>
          <div class="panel-body">
            <!-- Alert Banner if Discrepancy -->
            <div style="background:${activeDoc.is_anomaly || /mismatch|expiry/i.test(activeDoc.status) ? '#fef2f2' : '#f0fdf4'};border:1px solid ${activeDoc.is_anomaly || /mismatch|expiry/i.test(activeDoc.status) ? '#fecaca' : '#bbf7d0'};border-radius:8px;padding:12px;margin-bottom:16px">
              <strong style="color:${activeDoc.is_anomaly || /mismatch|expiry/i.test(activeDoc.status) ? '#b91c1c' : '#15803d'};font-size:12px">
                ${activeDoc.is_anomaly || /mismatch|expiry/i.test(activeDoc.status) ? 'Regulatory Discrepancy Identified' : 'Regulatory Consistency Satisfied'}
              </strong>
              <p style="font-size:11.5px;color:#334155;margin-top:3px">${escapeHtml(activeDoc.findings)}</p>
            </div>

            <!-- OCR Extracted Fields Table -->
            <div style="margin-bottom:18px">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                <h4 style="font-size:12.5px;font-weight:700">Extracted Metadata (Confidence: ${activeDoc.confidence})</h4>
                <button class="btn sm" onclick="VerificationModule.openCorrectionModal('${activeDoc.id}')">✎ Correct Fields</button>
              </div>
              <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px;display:grid;grid-template-columns:1fr 1fr;gap:12px;font-size:11.5px">
                ${Object.entries(extracted).map(([k, v]) => `
                  <div>
                    <span class="muted" style="text-transform:capitalize">${k.replace(/_/g, ' ')}:</span>
                    <strong style="display:block;color:#0f172a">${escapeHtml(String(v))}</strong>
                  </div>
                `).join("") || '<p class="muted">No extracted fields available.</p>'}
              </div>
            </div>

            <!-- Issuing Authority Section -->
            <div style="border-top:1px solid #f1f5f9;padding-top:14px;margin-bottom:18px">
              <h4 style="font-size:12.5px;font-weight:700;margin-bottom:8px">Issuing-Authority Verification Gateway</h4>
              <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:8px;padding:12px;font-size:11.5px">
                <div><span class="muted">Authority:</span> <b>${escapeHtml(activeDoc.issuing_authority || 'State / Central Authority')}</b></div>
                <div style="margin-top:4px"><span class="muted">Authority Reference:</span> <code>${escapeHtml(activeDoc.authority_ref || '—')}</code></div>
                <div style="margin-top:4px"><span class="muted">Source Adapter:</span> <span class="pill gray">${escapeHtml(activeDoc.verification_source || 'AICTE Adapter')}</span></div>
                <div style="margin-top:4px"><span class="muted">Verification Response:</span> <i>${escapeHtml(activeDoc.verification_response || 'Pending check')}</i></div>
              </div>
            </div>

            <!-- Actions -->
            <div style="display:flex;gap:10px;flex-wrap:wrap">
              <button class="btn primary" onclick="VerificationModule.triggerAuthorityCheck('${activeDoc.id}')">⚡ Synchronize Issuing Authority Adapter</button>
              <button class="btn" onclick="VerificationModule.openReportModal('${activeDoc.id}')">View Formal Report</button>
            </div>
          </div>
        </div>

        <!-- Document Queue List -->
        <div class="panel">
          <div class="panel-header">
            <h3>Document Verification Queue</h3>
            <span class="pill gray">${docs.length} Documents</span>
          </div>
          <div class="table-responsive">
            <table class="data-table">
              <thead>
                <tr>
                  <th>DOCUMENT NAME</th>
                  <th>INSTITUTION</th>
                  <th>OCR CONFIDENCE</th>
                  <th>STATUS</th>
                  <th>ACTION</th>
                </tr>
              </thead>
              <tbody>
                ${rows}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `;
  },

  selectDoc(id) {
    this.selectedDocId = id;
    App.refresh();
  },

  openUploadModal() {
    App.openModal(
      "Ingest Document for Verification",
      `
        <form id="upload-doc-form" class="form-grid">
          <div class="form-group full">
            <label class="form-label">Institution *</label>
            <select class="form-control" id="doc-inst-id" required>
              ${localStore.db.institutions.map(i => `<option value="${i.id}">${escapeHtml(i.name)} (${i.permanent_id})</option>`).join("")}
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Document Category *</label>
            <select class="form-control" id="doc-type" required>
              <option>Land Lease Agreement</option>
              <option>Fire & Life Safety Certificate</option>
              <option>Faculty Declaration</option>
              <option>Accreditation Certificate</option>
              <option>State Government NOC</option>
              <option>Building Occupancy Certificate</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Issuing Authority Reference (if known)</label>
            <input class="form-control" id="doc-ref" placeholder="e.g. REG-GBN-4421/2016" />
          </div>
          <div class="form-group full">
            <label class="form-label">Upload File (PDF / Images)</label>
            <div class="file-dropzone" onclick="document.getElementById('doc-file-input').click()">
              <div style="font-size:28px;color:#2563eb;margin-bottom:6px">⇧</div>
              <strong style="font-size:12.5px;color:#0f172a">Select document file or drop here</strong>
              <p style="font-size:11px;color:#64748b">PDF, JPG, PNG accepted. File integrity SHA-256 will be calculated.</p>
              <input type="file" id="doc-file-input" accept=".pdf,.png,.jpg,.jpeg" style="display:none" onchange="document.getElementById('selected-file-name').textContent = this.files[0]?.name || ''" />
            </div>
            <div id="selected-file-name" style="font-size:11.5px;font-weight:600;color:#2563eb;margin-top:6px"></div>
          </div>
        </form>
      `,
      `
        <button class="btn" onclick="App.closeModal()">Cancel</button>
        <button class="btn primary" onclick="VerificationModule.confirmUpload()">Ingest & Run OCR</button>
      `
    );
  },

  async confirmUpload() {
    const instId = document.getElementById("doc-inst-id").value;
    const inst = localStore.db.institutions.find(i => i.id === instId);
    const docType = document.getElementById("doc-type").value;
    const ref = document.getElementById("doc-ref").value;
    const fileInput = document.getElementById("doc-file-input");
    const fname = fileInput.files[0]?.name || `${docType.replace(/\s+/g, '_')}_2026.pdf`;

    const newDoc = {
      id: "DOC-" + Math.floor(1000 + Math.random() * 9000),
      institution_id: instId,
      institution_name: inst ? inst.name : "Institution",
      application_id: "APP-2026-0842",
      name: fname,
      document_type: docType,
      file_size: 450200,
      file_hash: "SHA-" + Math.random().toString(36).slice(2, 18).toUpperCase(),
      uploaded_at: new Date().toISOString().slice(0, 10),
      status: "Verification pending",
      confidence: "95%",
      extracted_fields: {
        institution_name: inst ? inst.name : "Institution",
        permanent_id: inst ? inst.permanent_id : "1-000000",
        issuing_authority: "State / Central Authority",
        reference_no: ref || "REF-2026",
        issue_date: new Date().toISOString().slice(0, 10),
        expiry_date: "2027-06-30"
      },
      findings: "Document ingested into repository. Automated field extraction complete. Ready for authority verification.",
      authority_ref: ref || "REF-2026",
      issuing_authority: "State Technical Board / Directorate",
      verification_source: "AICTE Regulatory Rules Engine",
      verification_response: "Preliminary format and checksum validation passed.",
      is_anomaly: false
    };

    localStore.db.documents.unshift(newDoc);
    localStore.log("Document Officer", "Verification Specialist", "Document Ingested", "Document", newDoc.id, `Uploaded ${fname} for ${newDoc.institution_name}.`);
    localStore.save();
    this.selectedDocId = newDoc.id;
    App.closeModal();
    App.toast("Document uploaded and processed successfully.");
    App.refresh();
  },

  async triggerAuthorityCheck(id) {
    await API.verifyDocumentAuthority(id);
    App.toast("Authority verification gateway checked. Result updated.");
    App.refresh();
  },

  openCorrectionModal(id) {
    const doc = localStore.db.documents.find(d => d.id === id);
    App.openModal(
      `Human Field Correction · ${doc.id}`,
      `
        <div class="form-group full">
          <label class="form-label">Issuing Authority Reference</label>
          <input class="form-control" id="correct-ref" value="${escapeHtml(doc.authority_ref || '')}" />
        </div>
        <div class="form-group full" style="margin-top:10px">
          <label class="form-label">Reviewer Finding & Adjudication Notes</label>
          <textarea class="form-control" id="correct-findings">${escapeHtml(doc.findings || '')}</textarea>
        </div>
        <div class="form-group full" style="margin-top:10px">
          <label class="form-label">Verification Verdict</label>
          <select class="form-control" id="correct-status">
            <option ${doc.status === 'Verified (demo)' ? 'selected' : ''}>Verified (demo)</option>
            <option ${doc.status === 'Mismatch detected' ? 'selected' : ''}>Mismatch detected</option>
            <option ${doc.status === 'Expiry detected' ? 'selected' : ''}>Expiry detected</option>
            <option ${doc.status === 'Manual review required' ? 'selected' : ''}>Manual review required</option>
          </select>
        </div>
      `,
      `
        <button class="btn" onclick="App.closeModal()">Cancel</button>
        <button class="btn primary" onclick="VerificationModule.saveCorrection('${id}')">Save Adjudication</button>
      `
    );
  },

  saveCorrection(id) {
    const doc = localStore.db.documents.find(d => d.id === id);
    if (doc) {
      doc.authority_ref = document.getElementById("correct-ref").value;
      doc.findings = document.getElementById("correct-findings").value;
      doc.status = document.getElementById("correct-status").value;
      doc.confidence = "100% (Human Verified)";
      localStore.log("Verification Officer", "Adjudicator", "Human Field Correction", "Document", doc.id, `Corrected fields in ${doc.name}. Status: ${doc.status}`);
      localStore.save();
    }
    App.closeModal();
    App.toast("Human correction saved and recorded in audit trail.");
    App.refresh();
  },

  openReportModal(id) {
    const doc = localStore.db.documents.find(d => d.id === id) || localStore.db.documents[0];
    const inst = localStore.db.institutions.find(i => i.id === doc.institution_id) || localStore.db.institutions[0];

    App.openModal(
      `Statutory Validation Report · ${doc.id}`,
      `
        <div style="font-size:12px;line-height:1.6;color:#1e293b" id="printable-report">
          <div style="display:flex;justify-content:space-between;border-bottom:2px solid #0c1a30;padding-bottom:12px;margin-bottom:16px">
            <div>
              <h2 style="font-size:16px;font-weight:800;color:#0c1a30">AICTE ONE — DOCUMENT VALIDATION REPORT</h2>
              <p style="font-size:11px;color:#64748b">Unified Institutional Intelligence & Governance System</p>
            </div>
            <div style="text-align:right">
              <b>Dossier Ref: ${doc.id}</b>
              <div class="secondary-cell-text">Date: ${new Date().toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' })}</div>
            </div>
          </div>

          <table style="width:100%;margin-bottom:16px;border-collapse:collapse;font-size:11.5px">
            <tr><td style="padding:4px;color:#64748b"><b>Institution Name:</b></td><td style="padding:4px"><b>${escapeHtml(inst.name)}</b></td></tr>
            <tr><td style="padding:4px;color:#64748b"><b>Permanent ID:</b></td><td style="padding:4px">${inst.permanent_id}</td></tr>
            <tr><td style="padding:4px;color:#64748b"><b>State / District:</b></td><td style="padding:4px">${inst.state} / ${inst.district}</td></tr>
            <tr><td style="padding:4px;color:#64748b"><b>Document Name:</b></td><td style="padding:4px"><b>${escapeHtml(doc.name)}</b> (${doc.document_type})</td></tr>
            <tr><td style="padding:4px;color:#64748b"><b>File SHA-256:</b></td><td style="padding:4px"><code>${doc.file_hash || 'SHA-99214A'}</code></td></tr>
            <tr><td style="padding:4px;color:#64748b"><b>Issuing Authority:</b></td><td style="padding:4px">${escapeHtml(doc.issuing_authority || 'State Authority')}</td></tr>
            <tr><td style="padding:4px;color:#64748b"><b>Authority Ref:</b></td><td style="padding:4px">${doc.authority_ref || '—'}</td></tr>
            <tr><td style="padding:4px;color:#64748b"><b>Status:</b></td><td style="padding:4px">${renderPill(doc.status)}</td></tr>
          </table>

          <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px;margin-bottom:16px">
            <b>Validation Findings & Evidence Summary:</b>
            <p style="margin-top:4px">${escapeHtml(doc.findings)}</p>
          </div>

          <div style="font-size:10.5px;color:#64748b;border-top:1px dashed #cbd5e1;padding-top:10px">
            * Official AICTE regulatory disclaimer: Automated OCR extraction and sandbox gateway responses represent diagnostic signals. Final approval determinations are executed by competent regulatory bodies under the AICTE Act 1987.
          </div>
        </div>
      `,
      `
        <button class="btn" onclick="App.closeModal()">Close</button>
        <button class="btn primary" onclick="window.print()">⎙ Print / Save as PDF</button>
      `
    );
  }
};

window.VerificationModule = VerificationModule;
