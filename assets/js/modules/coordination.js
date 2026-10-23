/**
 * Module 10: Cross-Bureau Coordination & Case Overlap Intelligence
 */
const CoordinationModule = {
  currentTab: 'clashes', // 'clashes' | 'confirmed'
  complaints: [],
  overlaps: [],

  async render() {
    const [overlapsList, complaintsList] = await Promise.all([
      API.getCoordinationOverlaps(),
      API.getComplaints()
    ]);

    this.overlaps = overlapsList || [];
    this.complaints = complaintsList || [];

    const links = (localStore && localStore.db && localStore.db.coordination_links) ? localStore.db.coordination_links : [];

    // Map overlaps with full complaint objects if needed
    const detectedPairs = this.overlaps.map(p => {
      let ca = p.case_a;
      let cb = p.case_b;
      if (typeof ca === 'string') ca = this.complaints.find(c => c.id === ca) || { id: p.case_a, bureau: 'Bureau A', category: 'General', summary: '' };
      if (typeof cb === 'string') cb = this.complaints.find(c => c.id === cb) || { id: p.case_b, bureau: 'Bureau B', category: 'General', summary: '' };

      const isLinked = p.is_linked || (ca && cb && ca.related_case_id === cb.id) || links.some(l => (l.case_a_id === (ca ? ca.id : '') && l.case_b_id === (cb ? cb.id : '')) || (l.case_a_id === (cb ? cb.id : '') && l.case_b_id === (ca ? ca.id : '')));
      return {
        ...p,
        case_a: ca,
        case_b: cb,
        institution_name: p.institution_name || (ca ? ca.institution_name : '') || (cb ? cb.institution_name : 'AICTE Institution'),
        score: p.score || (isLinked ? 95 : 88),
        is_linked: isLinked,
        reason: p.reason || `Multi-bureau inquiry correlation: overlapping regulatory proceedings concerning same technical campus.`
      };
    });

    const activeClashes = detectedPairs.filter(p => !p.is_linked);
    const confirmedLinks = detectedPairs.filter(p => p.is_linked);

    const displayList = this.currentTab === 'confirmed' ? confirmedLinks : activeClashes;

    return `
      <div class="page-header">
        <div>
          <div class="page-eyebrow">Multi-Bureau Case Intelligence</div>
          <h1>Cross-Bureau Coordination Workspace</h1>
          <p>Detect overlapping matters between PGRC, Regulation Bureau, Anti-Ragging Cell, and Regional Offices to prevent duplicate inquiries and conflicting orders.</p>
        </div>
        <div class="header-action-group">
          <button class="btn" onclick="App.navigate('complaints')">← Complaint Registry</button>
          <button class="btn primary" onclick="CoordinationModule.scanNow()">⚡ Re-scan Correlation Engine</button>
        </div>
      </div>

      <!-- Quick Metrics -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-header"><span>CORRELATED PAIRS</span><span>⌁</span></div>
          <div class="stat-number">${detectedPairs.length}</div>
          <div class="stat-subtext">Cross-bureau overlaps</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>CONFIRMED COORDINATION</span><span style="color:#15803d">✓</span></div>
          <div class="stat-number">${confirmedLinks.length}</div>
          <div class="stat-subtext">Active joint coordination</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>AWAITING REVIEW</span><span style="color:#b45309">!</span></div>
          <div class="stat-number">${activeClashes.length}</div>
          <div class="stat-subtext">Requires officer confirmation</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>AVG CORRELATION SCORE</span><span>⌘</span></div>
          <div class="stat-number">92%</div>
          <div class="stat-subtext">High confidence matching</div>
        </div>
      </div>

      <!-- Tab Navigation -->
      <div class="flex gap-2 mb-4 border-b border-slate-200 pb-2">
        <button class="btn sm ${this.currentTab === 'clashes' ? 'primary' : ''}" onclick="CoordinationModule.setTab('clashes')">
          ⚠ Active Clashes & Signals (${activeClashes.length})
        </button>
        <button class="btn sm ${this.currentTab === 'confirmed' ? 'primary' : ''}" onclick="CoordinationModule.setTab('confirmed')">
          ✓ Confirmed Coordinated Links (${confirmedLinks.length})
        </button>
      </div>

      <!-- Correlation Cards -->
      <div class="panel">
        <div class="panel-header">
          <div>
            <h3>${this.currentTab === 'confirmed' ? 'Active Multi-Bureau Linked Matters' : 'Detected Cross-Bureau Clashes & Overlaps'}</h3>
            <p>${this.currentTab === 'confirmed' ? 'Official joint proceedings established under AICTE Coordination Protocol. Case histories remain independent.' : 'Similarities represent coordination signals for officer review, never automated amalgamation.'}</p>
          </div>
          <span class="pill ${this.currentTab === 'confirmed' ? 'green' : 'amber'}">${this.currentTab === 'confirmed' ? 'Joint Oversight Active' : 'Human Adjudication Required'}</span>
        </div>
        <div class="panel-body">
          ${displayList.length ? displayList.map(p => `
            <div style="border:1px solid #e2e8f0;border-radius:10px;padding:16px;margin-bottom:16px;background:#ffffff;box-shadow:0 1px 3px rgba(0,0,0,0.05)">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px">
                <div style="display:flex;align-items:center;gap:10px">
                  <span class="pill ${p.is_linked ? 'green' : 'amber'}">${p.is_linked ? '✓ Coordinated Link Confirmed' : '⚠ Clash Flagged for Review'}</span>
                  <strong style="font-size:13px;color:#0f172a">${escapeHtml(p.institution_name)}</strong>
                </div>
                <div style="font-size:11.5px;color:#2563eb;font-weight:700">AI Confidence: ${p.score}%</div>
              </div>

              <!-- Two Cases Side-by-Side -->
              <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:14px;margin-bottom:14px">
                <!-- Case A -->
                <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px">
                  <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                    <span class="pill blue">${escapeHtml(p.case_a ? p.case_a.bureau : 'Bureau A')}</span>
                    <b>${p.case_a ? p.case_a.id : 'N/A'}</b>
                  </div>
                  <div style="font-size:11.5px;font-weight:600;margin-top:4px">${escapeHtml(p.case_a ? p.case_a.category : 'General')}</div>
                  <p style="font-size:11px;color:#64748b;margin-top:2px">${escapeHtml(p.case_a ? p.case_a.summary : '')}</p>
                  <small style="color:#94a3b8;font-size:10px;display:block;margin-top:6px">Assigned: ${escapeHtml(p.case_a ? (p.case_a.assigned_to || 'Officer') : '')} · Status: ${p.case_a ? p.case_a.status : ''}</small>
                </div>

                <!-- Case B -->
                <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px">
                  <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                    <span class="pill purple">${escapeHtml(p.case_b ? p.case_b.bureau : 'Bureau B')}</span>
                    <b>${p.case_b ? p.case_b.id : 'N/A'}</b>
                  </div>
                  <div style="font-size:11.5px;font-weight:600;margin-top:4px">${escapeHtml(p.case_b ? p.case_b.category : 'General')}</div>
                  <p style="font-size:11px;color:#64748b;margin-top:2px">${escapeHtml(p.case_b ? p.case_b.summary : '')}</p>
                  <small style="color:#94a3b8;font-size:10px;display:block;margin-top:6px">Assigned: ${escapeHtml(p.case_b ? (p.case_b.assigned_to || 'Officer') : '')} · Status: ${p.case_b ? p.case_b.status : ''}</small>
                </div>
              </div>

              <!-- Rationale Bar -->
              <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:6px;padding:10px;font-size:11.5px;color:#1e40af;margin-bottom:14px">
                <b>Overlap Finding:</b> ${escapeHtml(p.reason)}
              </div>

              <!-- Action Buttons -->
              <div style="display:flex;justify-content:flex-end;gap:10px">
                ${!p.is_linked ? `
                  <button class="btn sm danger" onclick="CoordinationModule.dismissMatch('${p.case_a ? p.case_a.id : ''}', '${p.case_b ? p.case_b.id : ''}')">Dismiss as Distinct</button>
                  <button class="btn sm primary" onclick="CoordinationModule.openConfirmLinkModal('${p.case_a ? p.case_a.id : ''}', '${p.case_b ? p.case_b.id : ''}')">Confirm Joint Coordination Link →</button>
                ` : `
                  <span style="font-size:11px;color:#15803d;display:flex;align-items:center;gap:6px">
                    ✓ Official joint link active. Independent case histories and decisions are preserved.
                  </span>
                `}
              </div>
            </div>
          `).join("") : `
            <div class="card p-8 text-center text-slate-400">
              <div class="font-medium text-slate-600 mb-1">${this.currentTab === 'confirmed' ? 'No confirmed multi-bureau links found.' : 'No active cross-bureau clashes detected.'}</div>
              <div class="text-xs text-slate-400">All registered grievance and regulatory cases across bureaus are proceeding independently.</div>
            </div>
          `}
        </div>
      </div>
    `;
  },

  setTab(tab) {
    this.currentTab = tab;
    App.refresh();
  },

  async scanNow() {
    App.toast("Scanning AICTE multi-bureau correlation engine...");
    await API.getCoordinationOverlaps();
    App.toast("Correlation scan complete. Registry updated with latest findings.");
    App.refresh();
  },

  openConfirmLinkModal(caseAId, caseBId) {
    const ca = (this.complaints || []).find(c => c.id === caseAId) || (localStore.db.complaints || []).find(c => c.id === caseAId) || { id: caseAId, institution_name: "Institution", bureau: "Bureau A", summary: "" };
    const cb = (this.complaints || []).find(c => c.id === caseBId) || (localStore.db.complaints || []).find(c => c.id === caseBId) || { id: caseBId, institution_name: "Institution", bureau: "Bureau B", summary: "" };

    App.openModal(
      "Confirm Multi-Bureau Case Coordination",
      `
        <p style="font-size:12px;color:#64748b;margin-bottom:14px">
          You are establishing an official coordination link between two independent proceedings regarding <b>${escapeHtml(ca.institution_name)}</b>:
        </p>
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px;font-size:11.5px;margin-bottom:14px">
          <div><b>Case 1:</b> ${ca.id} (${ca.bureau}) — ${escapeHtml(ca.summary)}</div>
          <div style="margin-top:6px"><b>Case 2:</b> ${cb.id} (${cb.bureau}) — ${escapeHtml(cb.summary)}</div>
        </div>
        <div class="form-group full">
          <label class="form-label">Coordinating Lead Bureau *</label>
          <select class="form-control" id="coord-lead-bureau">
            <option value="Regulation Bureau">Regulation Bureau (Joint Inquiry Lead)</option>
            <option value="PGRC">Public Grievance Redressal Cell (PGRC)</option>
            <option value="Anti-Ragging Cell">National Anti-Ragging Cell</option>
          </select>
        </div>
        <div class="form-group full" style="margin-top:10px">
          <label class="form-label">Coordination Rationale & Action Plan *</label>
          <textarea class="form-control" id="coord-rationale">Both matters pertain to overlapping regulatory concerns at the same institution. Establish joint inquiry to synchronize findings while preserving independent case orders.</textarea>
        </div>
      `,
      `
        <button class="btn" onclick="App.closeModal()">Cancel</button>
        <button class="btn primary" onclick="CoordinationModule.confirmLink('${caseAId}', '${caseBId}')">Establish Coordination Link</button>
      `
    );
  },

  async confirmLink(caseAId, caseBId) {
    const rationale = document.getElementById("coord-rationale").value;
    await API.linkCoordination(caseAId, caseBId, rationale);
    App.closeModal();
    App.toast("Cross-Bureau coordination link established.");
    App.refresh();
  },

  dismissMatch(caseAId, caseBId) {
    if (localStore && localStore.log) {
      localStore.log("Coordination Officer", "Grievance Specialist", "Dismissed Case Overlap", "Coordination", `${caseAId}|${caseBId}`, "Reviewed and dismissed proposed overlap as independent, distinct matters.");
    }
    App.toast("Correlation signal dismissed as independent matter.");
    App.refresh();
  }
};

window.CoordinationModule = CoordinationModule;
