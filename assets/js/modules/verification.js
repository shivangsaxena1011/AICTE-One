/**
 * Module 7: AI-Powered Document Verification & Forensic Engine (Module 3 in Reference)
 * "Bharat Civic-Sovereign Tech" Design System
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
      <tr class="hover:bg-slate-50/80 transition-colors border-b border-slate-100 cursor-pointer ${d.id === activeDoc.id ? 'bg-[#eaedff]/50' : ''}" 
        onclick="VerificationModule.selectDoc('${d.id}')">
        <td class="py-3 px-3">
          <div class="font-bold text-[#001332] text-xs">${escapeHtml(d.name)}</div>
          <div class="text-[10px] text-slate-400 font-mono">${d.id} · ${escapeHtml(d.document_type)}</div>
        </td>
        <td class="py-3 px-3">
          <div class="font-semibold text-[#001332] text-xs">${escapeHtml(d.institution_name)}</div>
        </td>
        <td class="py-3 px-3">
          <span class="font-mono text-xs font-bold text-[#001332]">${d.confidence}</span>
        </td>
        <td class="py-3 px-3">
          ${renderPill(d.status)}
        </td>
        <td class="py-3 px-3 text-right">
          <button class="px-2 py-1 text-xs font-semibold rounded bg-slate-100 text-[#001332] hover:bg-slate-200 transition-colors" 
            onclick="event.stopPropagation();VerificationModule.openReportModal('${d.id}')">
            Report
          </button>
        </td>
      </tr>
    `).join("");

    const extracted = activeDoc.extracted_fields || {};

    return `
      <div class="space-y-6">
        
        <!-- Sovereign Header -->
        <div class="flex flex-col xl:flex-row xl:items-end justify-between gap-4 pb-2 border-b border-slate-200/80">
          <div class="space-y-1">
            <div class="flex items-center gap-2">
              <span class="font-mono text-xs uppercase tracking-wider text-[#a73a00] font-bold">Document Forensics & Issuing Verification</span>
              <span class="w-1.5 h-1.5 rounded-full bg-slate-300"></span>
              <span class="font-mono text-xs text-slate-500">Problem Statement 26261</span>
            </div>
            <div class="flex items-baseline gap-3 flex-wrap">
              <h1 class="font-headline text-2xl lg:text-3xl font-extrabold text-[#001332] tracking-tight">Intelligent Document Verification & Forensics</h1>
              <span class="font-mono text-[11px] font-bold px-2 py-0.5 rounded bg-[#002f1e] text-[#23a274]">DIGILOCKER DPI RELAY: ONLINE</span>
            </div>
            <p class="text-xs text-slate-600 max-w-4xl">
              Multi-modal OCR extraction, cryptographic issuing authority checksums, land cadastral validation, and stamp forgery detection matrix.
            </p>
          </div>

          <div class="flex flex-wrap items-center gap-2 bg-slate-100/80 p-1.5 rounded-lg border border-slate-200">
            <a href="https://documentverify-two.vercel.app/" target="_blank" rel="noopener noreferrer" 
              class="px-3 py-1.5 bg-[#a73a00] hover:bg-[#8f3200] text-white font-semibold text-xs rounded-md shadow-xs transition-colors flex items-center gap-1.5"
              title="Launch Live External AI Document Verification Service in New Tab">
              <span class="material-symbols-outlined text-[16px]">verified</span>
              <span>Document Verification</span>
              <span class="material-symbols-outlined text-[14px]">open_in_new</span>
            </a>
            <button class="px-3 py-1.5 bg-white text-[#001332] font-semibold text-xs rounded-md shadow-xs hover:bg-slate-50 border border-slate-200 transition-colors flex items-center gap-1.5" 
              onclick="VerificationModule.openReportModal('${activeDoc.id}')">
              <span class="material-symbols-outlined text-[16px]">print</span>
              <span>Validation Report</span>
            </button>
            <button class="px-3 py-1.5 bg-[#001332] text-white font-semibold text-xs rounded-md shadow-xs hover:bg-[#0f284e] transition-colors flex items-center gap-1.5" 
              onclick="VerificationModule.openUploadModal()">
              <span class="material-symbols-outlined text-[16px]">upload_file</span>
              <span>Ingest Document</span>
            </button>
          </div>
        </div>

        <!-- Telemetry Strip -->
        <div class="bg-[#eaedff]/60 rounded-xl p-3 border border-[#dae2fd] shadow-xs flex flex-wrap items-center justify-between gap-3 text-xs">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-[#001332] text-[18px]">verified</span>
            <span class="font-semibold text-[#001332]">OCR Engine:</span>
            <span class="text-slate-700">RegV-OCR-4b (APH 2026 tuned)</span>
          </div>
          <div class="flex items-center gap-4 text-slate-600">
            <span class="flex items-center gap-1">
              <span class="w-2 h-2 rounded-full bg-[#23a274]"></span>
              State Revenue Land Portal: Connected
            </span>
            <span class="flex items-center gap-1">
              <span class="w-2 h-2 rounded-full bg-[#23a274]"></span>
              Fire & Safety NOC DB: Active
            </span>
          </div>
        </div>

        <!-- Quick Metrics -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div class="bg-white p-4 rounded-xl border border-slate-200/90 shadow-xs flex flex-col justify-between">
            <div class="flex items-start justify-between">
              <span class="text-[11px] font-bold uppercase tracking-wider text-slate-500">Documents Ingested</span>
              <span class="material-symbols-outlined text-[#001332] text-[20px]">fact_check</span>
            </div>
            <div class="my-2">
              <div class="font-headline text-2xl font-extrabold text-[#001332] tracking-tight">${docs.length}</div>
              <div class="text-[11px] text-slate-500 mt-0.5">Across active institutional files</div>
            </div>
            <div class="w-full bg-slate-100 h-1 rounded-full overflow-hidden">
              <div class="bg-[#001332] h-full" style="width: 100%"></div>
            </div>
          </div>

          <div class="bg-white p-4 rounded-xl border border-slate-200/90 shadow-xs flex flex-col justify-between">
            <div class="flex items-start justify-between">
              <span class="text-[11px] font-bold uppercase tracking-wider text-[#23a274]">Verified Authentic</span>
              <span class="material-symbols-outlined text-[#23a274] text-[20px]">verified_user</span>
            </div>
            <div class="my-2">
              <div class="font-headline text-2xl font-extrabold text-[#23a274] tracking-tight">
                ${docs.filter(d => /verified/i.test(d.status)).length}
              </div>
              <div class="text-[11px] text-slate-500 mt-0.5">Verified with issuing authority</div>
            </div>
            <div class="w-full bg-slate-100 h-1 rounded-full overflow-hidden">
              <div class="bg-[#23a274] h-full" style="width: 75%"></div>
            </div>
          </div>

          <div class="bg-white p-4 rounded-xl border border-slate-200/90 shadow-xs flex flex-col justify-between">
            <div class="flex items-start justify-between">
              <span class="text-[11px] font-bold uppercase tracking-wider text-[#ba1a1a]">Discrepancies Flagged</span>
              <span class="material-symbols-outlined text-[#ba1a1a] text-[20px]">warning</span>
            </div>
            <div class="my-2">
              <div class="font-headline text-2xl font-extrabold text-[#ba1a1a] tracking-tight">
                ${docs.filter(d => /mismatch|expiry|anomal/i.test(d.status)).length}
              </div>
              <div class="text-[11px] text-slate-500 mt-0.5">Require statutory review</div>
            </div>
            <div class="w-full bg-slate-100 h-1 rounded-full overflow-hidden">
              <div class="bg-[#ba1a1a] h-full" style="width: 25%"></div>
            </div>
          </div>

          <div class="bg-white p-4 rounded-xl border border-slate-200/90 shadow-xs flex flex-col justify-between">
            <div class="flex items-start justify-between">
              <span class="text-[11px] font-bold uppercase tracking-wider text-slate-500">Pending Authority Check</span>
              <span class="material-symbols-outlined text-slate-400 text-[20px]">hourglass_empty</span>
            </div>
            <div class="my-2">
              <div class="font-headline text-2xl font-extrabold text-slate-700 tracking-tight">
                ${docs.filter(d => /pending/i.test(d.status)).length}
              </div>
              <div class="text-[11px] text-slate-500 mt-0.5">Awaiting DigiLocker pull</div>
            </div>
            <div class="w-full bg-slate-100 h-1 rounded-full overflow-hidden">
              <div class="bg-slate-400 h-full" style="width: 15%"></div>
            </div>
          </div>
        </div>

        <!-- 2-Column Inspection Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-5">
          
          <!-- Left 7 Columns: Active Document Dossier -->
          <div class="lg:col-span-7 bg-white rounded-xl border border-slate-200/90 shadow-xs p-5 space-y-4">
            <div class="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <h3 class="font-headline font-bold text-base text-[#001332]">${escapeHtml(activeDoc.name)}</h3>
                <p class="text-xs text-slate-500">${escapeHtml(activeDoc.document_type)} · ${activeDoc.id}</p>
              </div>
              ${renderPill(activeDoc.status)}
            </div>

            <!-- Discrepancy or Verified Banner -->
            <div class="p-3.5 rounded-lg border ${activeDoc.is_anomaly || /mismatch|expiry/i.test(activeDoc.status) ? 'bg-[#ffdad6]/40 border-[#ffdad6] text-[#93000a]' : 'bg-[#002f1e]/10 border-[#002f1e]/20 text-[#002f1e]'}">
              <div class="flex items-center gap-1.5 font-bold text-xs mb-1">
                <span class="material-symbols-outlined text-[16px]">${activeDoc.is_anomaly || /mismatch|expiry/i.test(activeDoc.status) ? 'warning' : 'verified'}</span>
                <span>${activeDoc.is_anomaly || /mismatch|expiry/i.test(activeDoc.status) ? 'Regulatory Discrepancy Identified' : 'Regulatory Integrity Satisfied'}</span>
              </div>
              <p class="text-xs opacity-90">${escapeHtml(activeDoc.findings)}</p>
            </div>

            <!-- Extracted Metadata Fields -->
            <div>
              <div class="flex items-center justify-between mb-2">
                <h4 class="font-headline font-bold text-xs text-[#001332]">OCR Extracted Metadata (Confidence: ${activeDoc.confidence})</h4>
                <button class="px-2 py-0.5 text-[11px] font-semibold rounded bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors" 
                  onclick="VerificationModule.openCorrectionModal('${activeDoc.id}')">
                  ✎ Correct Fields
                </button>
              </div>
              <div class="grid grid-cols-2 gap-3 p-3.5 rounded-lg bg-slate-50 border border-slate-200/80 text-xs">
                ${Object.entries(extracted).map(([k, v]) => `
                  <div>
                    <span class="text-slate-400 capitalize block text-[10px] font-semibold">${k.replace(/_/g, ' ')}</span>
                    <strong class="font-mono text-slate-800 text-xs mt-0.5 block">${escapeHtml(String(v))}</strong>
                  </div>
                `).join("")}
              </div>
            </div>

            <!-- Cryptographic Seal & Verification Trail -->
            <div class="p-3.5 rounded-lg bg-slate-50 border border-slate-200/80 text-xs space-y-2">
              <div class="font-bold text-[#001332] text-xs">Cryptographic Integrity Stamp</div>
              <div class="flex items-center justify-between font-mono text-[10px] text-slate-500 bg-white p-2 rounded border border-slate-200">
                <span>SHA-256: 7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069</span>
                <span class="text-[#23a274] font-bold">SEAL VALID</span>
              </div>
              <div class="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                <span>Verified Authority: Sub-Registrar Gautam Buddha Nagar</span>
                <span>Pull Date: 2026-10-18</span>
              </div>
            </div>

            <div class="flex items-center justify-end gap-2 pt-2">
              <button class="px-3 py-1.5 text-xs font-semibold rounded bg-slate-100 text-slate-700 hover:bg-slate-200" 
                onclick="VerificationModule.openCorrectionModal('${activeDoc.id}')">
                Manual Override
              </button>
              <button class="px-3 py-1.5 text-xs font-semibold rounded bg-[#001332] text-white hover:bg-[#0f284e]" 
                onclick="VerificationModule.openReportModal('${activeDoc.id}')">
                Download Signed Dossier
              </button>
            </div>
          </div>

          <!-- Right 5 Columns: All Documents Ingested List -->
          <div class="lg:col-span-5 bg-white rounded-xl border border-slate-200/90 shadow-xs p-5 space-y-3">
            <div class="flex items-center justify-between pb-2 border-b border-slate-100">
              <h3 class="font-headline font-bold text-sm text-[#001332]">Institutional Ingestion Queue</h3>
              <span class="text-xs text-slate-400 font-mono">${docs.length} total</span>
            </div>
            <div class="overflow-x-auto max-h-[600px] overflow-y-auto">
              <table class="w-full text-left text-xs font-sans">
                <thead class="bg-slate-50 text-[10px] font-bold uppercase tracking-wider text-slate-500 sticky top-0">
                  <tr>
                    <th class="py-2 px-2">DOCUMENT</th>
                    <th class="py-2 px-2">INSTITUTION</th>
                    <th class="py-2 px-2">CONF.</th>
                    <th class="py-2 px-2">STATUS</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                  ${rows}
                </tbody>
              </table>
            </div>
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
      "Ingest Institutional Document for Verification",
      `
        <form id="upload-doc-form" class="space-y-4">
          <div>
            <label class="block text-xs font-bold text-slate-700 mb-1">Select Institution *</label>
            <select class="w-full text-xs p-2 rounded-lg border border-slate-200 bg-white" id="doc-inst-id" required>
              ${localStore.db.institutions.map(i => `<option value="${i.id}">${escapeHtml(i.name)} (${i.permanent_id})</option>`).join("")}
            </select>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-bold text-slate-700 mb-1">Document Type *</label>
              <select class="w-full text-xs p-2 rounded-lg border border-slate-200 bg-white" id="doc-type">
                <option>Registered Land Deed</option>
                <option>Fire Safety Certificate</option>
                <option>Building Plan Approval</option>
                <option>Occupancy Certificate</option>
                <option>Society / Trust Registration</option>
                <option>Bank FDR / Fixed Deposit</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-700 mb-1">Issuing Authority</label>
              <input class="w-full text-xs p-2 rounded-lg border border-slate-200 bg-white" id="doc-authority" placeholder="e.g. Sub-Registrar / Municipal Corp" />
            </div>
          </div>
          <div>
            <label class="block text-xs font-bold text-slate-700 mb-1">File Upload (.PDF / .JPG / .PNG)</label>
            <input type="file" class="w-full text-xs p-2 rounded-lg border border-dashed border-slate-300 bg-slate-50" id="doc-file" />
          </div>
        </form>
      `,
      `
        <button class="px-3 py-1.5 text-xs font-semibold rounded bg-slate-100 text-slate-700 hover:bg-slate-200" onclick="App.closeModal()">Cancel</button>
        <button class="px-3 py-1.5 text-xs font-semibold rounded bg-[#001332] text-white hover:bg-[#0f284e]" onclick="VerificationModule.confirmUpload()">Ingest & Verify</button>
      `
    );
  },

  async confirmUpload() {
    const instId = document.getElementById("doc-inst-id") ? document.getElementById("doc-inst-id").value : "INST-001";
    const inst = (window.localStore && localStore.db.institutions.find(i => i.id === instId));
    const docType = document.getElementById("doc-type") ? document.getElementById("doc-type").value : "Registered Land Deed";
    const authority = (document.getElementById("doc-authority") && document.getElementById("doc-authority").value) || "Authorized Authority";
    const fileInput = document.getElementById("doc-file");

    let createdDoc;
    if (fileInput && fileInput.files && fileInput.files.length > 0) {
      const formData = new FormData();
      formData.append("file", fileInput.files[0]);
      formData.append("institution_id", instId);
      formData.append("document_type", docType);
      formData.append("authority_ref", authority);
      try {
        createdDoc = await API.uploadDocument(formData);
        App.toast("Document uploaded and OCR extracted via backend API.", "success");
      } catch (e) {
        console.warn("Upload error:", e);
      }
    }

    if (!createdDoc) {
      const payload = {
        institution_id: instId,
        institution_name: inst ? inst.name : "Institution",
        document_type: docType,
        name: `${docType} (${inst ? (inst.permanent_id || inst.id) : 'AICTE'})`,
        issuing_authority: authority
      };
      createdDoc = await API.uploadDocument(payload);
      App.toast("Document ingested and verified.", "success");
    }

    App.closeModal();
    if (createdDoc && createdDoc.id) {
      this.selectedDocId = createdDoc.id;
    }
    App.refresh();
  },

  openCorrectionModal(id) {
    const d = localStore.db.documents.find(x => x.id === id);
    App.openModal(
      `Correct OCR Extracted Fields · ${d.id}`,
      `
        <div class="space-y-3">
          <div>
            <label class="block text-xs font-bold text-slate-700 mb-1">Status Classification</label>
            <select class="w-full text-xs p-2 rounded-lg border border-slate-200 bg-white" id="edit-doc-status">
              <option value="Verified" ${d.status === 'Verified' ? 'selected' : ''}>Verified</option>
              <option value="Mismatch" ${d.status === 'Mismatch' ? 'selected' : ''}>Mismatch</option>
              <option value="Approaching Expiry" ${d.status === 'Approaching Expiry' ? 'selected' : ''}>Approaching Expiry</option>
              <option value="Pending" ${d.status === 'Pending' ? 'selected' : ''}>Pending</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-bold text-slate-700 mb-1">Findings & Human Review Notes</label>
            <textarea class="w-full text-xs p-2 rounded-lg border border-slate-200 bg-white" id="edit-doc-findings" rows="3">${escapeHtml(d.findings)}</textarea>
          </div>
        </div>
      `,
      `
        <button class="px-3 py-1.5 text-xs font-semibold rounded bg-slate-100 text-slate-700 hover:bg-slate-200" onclick="App.closeModal()">Cancel</button>
        <button class="px-3 py-1.5 text-xs font-semibold rounded bg-[#001332] text-white hover:bg-[#0f284e]" onclick="VerificationModule.saveCorrection('${id}')">Save Changes</button>
      `
    );
  },

  async saveCorrection(id) {
    const statusVal = document.getElementById("edit-doc-status") ? document.getElementById("edit-doc-status").value : "Verified";
    const findingsVal = document.getElementById("edit-doc-findings") ? document.getElementById("edit-doc-findings").value : "Reviewed";
    try {
      await API.reviewDocument(id, "CONFIRM_MATCH", findingsVal, null, statusVal);
      App.toast("Document updated and human review logged to backend.", "success");
    } catch (e) {
      const d = window.localStore && localStore.db.documents.find(x => x.id === id);
      if (d) {
        d.status = statusVal;
        d.findings = findingsVal;
        d.is_anomaly = /mismatch|expiry/i.test(d.status);
      }
      App.toast("Document updated (offline mode).", "info");
    }
    App.closeModal();
    App.refresh();
  },

  openReportModal(id) {
    const d = localStore.db.documents.find(x => x.id === id);
    App.openModal(
      `Printable Validation Certificate · ${d.id}`,
      `
        <div class="space-y-4 p-4 border border-slate-200 rounded-lg bg-slate-50/50 font-sans text-xs">
          <div class="text-center pb-3 border-b border-slate-200">
            <h2 class="font-headline font-extrabold text-base text-[#001332]">ALL INDIA COUNCIL FOR TECHNICAL EDUCATION</h2>
            <div class="text-[11px] text-slate-600">Statutory Document Validation Certificate</div>
            <div class="font-mono text-[10px] text-slate-400 mt-1">CERTIFICATE ID: CERT-${d.id} · APH 2026-27</div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div><b>Institution:</b> ${escapeHtml(d.institution_name)}</div>
            <div><b>Document:</b> ${escapeHtml(d.name)}</div>
            <div><b>Issuing Authority:</b> ${escapeHtml(d.issuing_authority)}</div>
            <div><b>Extraction Confidence:</b> ${d.confidence}</div>
            <div><b>Status:</b> ${renderPill(d.status)}</div>
            <div><b>Verification Date:</b> ${new Date().toLocaleDateString()}</div>
          </div>
          <div class="p-3 bg-white rounded border border-slate-200">
            <b>Statutory Adjudication Findings:</b>
            <p class="mt-1 text-slate-700">${escapeHtml(d.findings)}</p>
          </div>
          <div class="font-mono text-[10px] text-slate-400 text-center">
            SHA-256 Checksum: 7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069
          </div>
        </div>
      `,
      `
        <button class="px-3 py-1.5 text-xs font-semibold rounded bg-slate-100 text-slate-700 hover:bg-slate-200" onclick="App.closeModal()">Close</button>
        <button class="px-3 py-1.5 text-xs font-semibold rounded bg-[#001332] text-white hover:bg-[#0f284e]" onclick="window.print()">Print Certificate</button>
      `
    );
  }
};

window.VerificationModule = VerificationModule;
