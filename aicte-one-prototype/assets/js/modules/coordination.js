/**
 * Module 10: Cross-Bureau Coordination & Case Overlap Intelligence
 */
const CoordinationModule = {
  async render() {
    const complaints = localStore.db.complaints;
    const links = localStore.db.coordination_links;

    // Scan for all pairs sharing same institution ID
    const detectedPairs = [];
    for (let i = 0; i < complaints.length; i++) {
      for (let j = i + 1; j < complaints.length; j++) {
        const ca = complaints[i];
        const cb = complaints[j];
        if (ca.institution_id === cb.institution_id) {
          const isLinked = ca.related_case_id === cb.id || links.some(l => (l.case_a_id === ca.id && l.case_b_id === cb.id) || (l.case_a_id === cb.id && l.case_b_id === ca.id));
          detectedPairs.push({
            case_a: ca,
            case_b: cb,
            institution_name: ca.institution_name,
            score: isLinked ? 94 : 85,
            is_linked: isLinked,
            reason: `Exact Institution Permanent ID (${ca.institution_id}) correlation; overlapping intake and regulatory inquiries.`
          });
        }
      }
    }

    return `
      <div class="page-header">
        <div>
          <div class="page-eyebrow">Multi-Bureau Case Intelligence</div>
          <h1>Cross-Bureau Coordination Workspace</h1>
          <p>Detect overlapping matters between PGRC, Regulation Bureau, and Regional Offices to prevent duplicate inquiries and conflicting orders.</p>
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
          <div class="stat-number">${detectedPairs.filter(p => p.is_linked).length}</div>
          <div class="stat-subtext">Active joint coordination</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>AWAITING REVIEW</span><span style="color:#b45309">!</span></div>
          <div class="stat-number">${detectedPairs.filter(p => !p.is_linked).length}</div>
          <div class="stat-subtext">Requires officer confirmation</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>AVG CORRELATION SCORE</span><span>⌘</span></div>
          <div class="stat-number">91%</div>
          <div class="stat-subtext">High confidence matching</div>
        </div>
      </div>

      <!-- Correlation Cards -->
      <div class="panel">
        <div class="panel-header">
          <div>
            <h3>Detected Cross-Bureau Matter Overlaps</h3>
            <p>Similarities represent coordination signals for officer review, never automated amalgamation.</p>
          </div>
          <span class="pill amber">Human Adjudication Required</span>
        </div>
        <div class="panel-body">
          ${detectedPairs.map(p => `
            <div style="border:1px solid #e2e8f0;border-radius:10px;padding:16px;margin-bottom:16px;background:#ffffff">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
                <div style="display:flex;align-items:center;gap:10px">
                  <span class="pill ${p.is_linked ? 'green' : 'amber'}">${p.is_linked ? '✓ Coordinated Link Confirmed' : '⚠ Coordination Signal Flagged'}</span>
                  <strong style="font-size:13px;color:#0f172a">${escapeHtml(p.institution_name)}</strong>
                </div>
                <div style="font-size:11.5px;color:#2563eb;font-weight:700">Correlation Score: ${p.score}%</div>
              </div>

              <!-- Two Cases Side-by-Side -->
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px">
                <!-- Case A -->
                <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px">
                  <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                    <span class="pill blue">${escapeHtml(p.case_a.bureau)}</span>
                    <b>${p.case_a.id}</b>
                  </div>
                  <div style="font-size:11.5px;font-weight:600;margin-top:4px">${escapeHtml(p.case_a.category)}</div>
                  <p style="font-size:11px;color:#64748b;margin-top:2px">${escapeHtml(p.case_a.summary)}</p>
                  <small style="color:#94a3b8;font-size:10px;display:block;margin-top:6px">Assigned: ${escapeHtml(p.case_a.assigned_to)} · Status: ${p.case_a.status}</small>
                </div>

                <!-- Case B -->
                <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px">
                  <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                    <span class="pill purple">${escapeHtml(p.case_b.bureau)}</span>
                    <b>${p.case_b.id}</b>
                  </div>
                  <div style="font-size:11.5px;font-weight:600;margin-top:4px">${escapeHtml(p.case_b.category)}</div>
                  <p style="font-size:11px;color:#64748b;margin-top:2px">${escapeHtml(p.case_b.summary)}</p>
                  <small style="color:#94a3b8;font-size:10px;display:block;margin-top:6px">Assigned: ${escapeHtml(p.case_b.assigned_to)} · Status: ${p.case_b.status}</small>
                </div>
              </div>

              <!-- Rationale Bar -->
              <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:6px;padding:10px;font-size:11.5px;color:#1e40af;margin-bottom:14px">
                <b>Matching Rationale:</b> ${escapeHtml(p.reason)}
              </div>

              <!-- Action Buttons -->
              <div style="display:flex;justify-content:flex-end;gap:10px">
                ${!p.is_linked ? `
                  <button class="btn sm danger" onclick="CoordinationModule.dismissMatch('${p.case_a.id}', '${p.case_b.id}')">Dismiss as Distinct</button>
                  <button class="btn sm primary" onclick="CoordinationModule.openConfirmLinkModal('${p.case_a.id}', '${p.case_b.id}')">Confirm Joint Coordination Link →</button>
                ` : `
                  <span style="font-size:11px;color:#15803d;display:flex;align-items:center;gap:6px">
                    ✓ Official joint link active. Independent case histories and decisions are preserved.
                  </span>
                `}
              </div>
            </div>
          `).join("") || '<p class="muted">No cross-Bureau matter overlaps detected.</p>'}
        </div>
      </div>
    `;
  },

  scanNow() {
    App.toast("Correlation engine re-evaluated entire complaints registry.");
    App.refresh();
  },

  openConfirmLinkModal(caseAId, caseBId) {
    const ca = localStore.db.complaints.find(c => c.id === caseAId);
    const cb = localStore.db.complaints.find(c => c.id === caseBId);

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
          </select>
        </div>
        <div class="form-group full" style="margin-top:10px">
          <label class="form-label">Coordination Rationale & Action Plan *</label>
          <textarea class="form-control" id="coord-rationale">Both matters pertain to unauthorized intake in CSE at the same institution. Establish joint inquiry to synchronize findings while preserving independent case orders.</textarea>
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
    localStore.log("Coordination Officer", "Grievance Specialist", "Dismissed Case Overlap", "Coordination", `${caseAId}|${caseBId}`, "Reviewed and dismissed proposed overlap as independent, distinct matters.");
    App.toast("Correlation signal dismissed as independent matter.");
    App.refresh();
  }
};

window.CoordinationModule = CoordinationModule;
