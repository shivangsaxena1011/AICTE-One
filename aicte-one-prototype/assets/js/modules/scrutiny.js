/**
 * Module 5: Dedicated Scrutiny & Workflow Workspace
 */
const ScrutinyModule = {
  selectedAppId: "APP-2026-0842",

  async render() {
    const apps = localStore.db.applications.filter(a => /scrutiny|validation/i.test(a.current_stage));
    const activeApp = localStore.db.applications.find(a => a.id === this.selectedAppId) || apps[0] || localStore.db.applications[0];
    const docs = localStore.db.documents.filter(d => d.institution_id === activeApp.institution_id);

    return `
      <div class="page-header">
        <div>
          <div class="page-eyebrow">Scrutiny Committee Workspace</div>
          <h1>Scrutiny & Deficiency Workflow</h1>
          <p>Examine statutory checklists, evaluate document evidence, flag regulatory deficiencies, and issue rectification notices.</p>
        </div>
        <div class="header-action-group">
          <button class="btn" onclick="ScrutinyModule.openForwardEVC('${activeApp.id}')">Forward to EVC Committee →</button>
          <button class="btn danger" onclick="ScrutinyModule.openDeficiencyNotice('${activeApp.id}')">Issue Deficiency Checklist</button>
        </div>
      </div>

      <!-- Quick Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-header"><span>IN SCRUTINY QUEUE</span><span>⌕</span></div>
          <div class="stat-number">${apps.length}</div>
          <div class="stat-subtext">Awaiting officer clearance</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>DEFICIENCIES FLAGGED</span><span style="color:#b91c1c">!</span></div>
          <div class="stat-number">${localStore.db.applications.reduce((acc, a) => acc + (a.deficiency_count || 0), 0)}</div>
          <div class="stat-subtext">Across active applications</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>DOCUMENTS VERIFIED</span><span style="color:#15803d">✓</span></div>
          <div class="stat-number">${docs.filter(d => /verified/i.test(d.status)).length} / ${docs.length}</div>
          <div class="stat-subtext">Attached to active case</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>SCRUTINY TIMELINE</span><span>◷</span></div>
          <div class="stat-number">10 Days</div>
          <div class="stat-subtext">Prescribed disposal window</div>
        </div>
      </div>

      <!-- Workspace Grid -->
      <div class="grid-2">
        <!-- Active Application Scrutiny Checklist -->
        <div class="panel">
          <div class="panel-header">
            <div>
              <h3>Statutory Scrutiny Checklist · ${activeApp.id}</h3>
              <p>${escapeHtml(activeApp.institution_name)} (${activeApp.permanent_id})</p>
            </div>
            ${renderPill(activeApp.status)}
          </div>
          <div class="panel-body">
            <div style="display:flex;flex-direction:column;gap:14px">
              <div style="border:1px solid #e2e8f0;border-radius:8px;padding:12px;background:#f8fafc">
                <div style="display:flex;justify-content:space-between;align-items:center">
                  <strong style="font-size:12.5px;color:#0f172a">1. Land Area & Registered Lease Deed</strong>
                  <span class="pill amber">Approaching Expiry</span>
                </div>
                <p style="font-size:11.5px;color:#64748b;margin:4px 0">
                  Sub-Registrar registered deed on file: 12.5 Acres. Registered lease expires on 25-Oct-2026. Extension deed submission mandatory.
                </p>
                <div style="font-size:11px;color:#1e40af"><b>Rule Check:</b> AICTE APH 2026 Chapter I Clause 1.4</div>
              </div>

              <div style="border:1px solid #e2e8f0;border-radius:8px;padding:12px;background:#f8fafc">
                <div style="display:flex;justify-content:space-between;align-items:center">
                  <strong style="font-size:12.5px;color:#0f172a">2. Fire & Life Safety Clearance</strong>
                  <span class="pill green">Verified</span>
                </div>
                <p style="font-size:11.5px;color:#64748b;margin:4px 0">
                  State Fire Services NOC valid for academic block and hostel complexes. Automatic sprinkler and hydrant test certified.
                </p>
                <div style="font-size:11px;color:#1e40af"><b>Rule Check:</b> National Building Code (NBC) Part IV</div>
              </div>

              <div style="border:1px solid #e2e8f0;border-radius:8px;padding:12px;background:#f8fafc">
                <div style="display:flex;justify-content:space-between;align-items:center">
                  <strong style="font-size:12.5px;color:#0f172a">3. Faculty Cadre Ratio & Qualification</strong>
                  <span class="pill red">Deficiency Flagged</span>
                </div>
                <p style="font-size:11.5px;color:#64748b;margin:4px 0">
                  Prescribed cadre ratio is 1:2:6. Extracted declaration indicates Professor deficiency in Computer Science department.
                </p>
                <div style="font-size:11px;color:#1e40af"><b>Rule Check:</b> AICTE Pay Scales & Cadre Qualifications Regulations</div>
              </div>

              <div style="border:1px solid #e2e8f0;border-radius:8px;padding:12px;background:#f8fafc">
                <div style="display:flex;justify-content:space-between;align-items:center">
                  <strong style="font-size:12.5px;color:#0f172a">4. Anti-Ragging Measures & Ombudsman</strong>
                  <span class="pill green">Satisfied</span>
                </div>
                <p style="font-size:11.5px;color:#64748b;margin:4px 0">
                  Institution has notified anti-ragging squad, web portal display, and appointed Retired District Judge as student ombudsman.
                </p>
                <div style="font-size:11px;color:#1e40af"><b>Rule Check:</b> AICTE Redressal of Grievance Regulations 2019</div>
              </div>
            </div>

            <div style="display:flex;gap:10px;margin-top:20px">
              <button class="btn primary" onclick="ScrutinyModule.approveScrutiny('${activeApp.id}')">✓ Clear Scrutiny Stage</button>
              <button class="btn danger" onclick="ScrutinyModule.openDeficiencyNotice('${activeApp.id}')">Return with Deficiency Checklist</button>
            </div>
          </div>
        </div>

        <!-- Case Selector & Evidence Documents -->
        <div>
          <!-- Case Selector -->
          <div class="panel">
            <div class="panel-header"><h3>Select Application to Scrutinize</h3></div>
            <div class="panel-body" style="padding:10px">
              ${apps.map(a => `
                <div
                  style="padding:10px;border-radius:8px;border:1px solid ${a.id === activeApp.id ? '#2563eb' : '#e2e8f0'};background:${a.id === activeApp.id ? '#eff6ff' : '#ffffff'};cursor:pointer;margin-bottom:8px"
                  onclick="ScrutinyModule.selectApp('${a.id}')"
                >
                  <div style="display:flex;justify-content:space-between;font-weight:700;font-size:12px">
                    <span>${a.id}</span>
                    ${renderPill(a.status)}
                  </div>
                  <div style="font-size:11.5px;color:#0f172a;margin-top:2px">${escapeHtml(a.institution_name)}</div>
                  <div style="font-size:10.5px;color:#64748b">${escapeHtml(a.type)} · Owner: ${escapeHtml(a.owner)}</div>
                </div>
              `).join("")}
            </div>
          </div>

          <!-- Document Verification Snapshot -->
          <div class="panel">
            <div class="panel-header">
              <h3>Associated Evidence Documents</h3>
              <button class="btn sm" onclick="App.navigate('verification')">Open Module →</button>
            </div>
            <div class="panel-body" style="padding:10px">
              ${docs.map(d => `
                <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 10px;border-bottom:1px solid #f1f5f9;font-size:11.5px">
                  <div>
                    <strong>${escapeHtml(d.name)}</strong>
                    <div class="secondary-cell-text">${escapeHtml(d.document_type)} · ${d.confidence}</div>
                  </div>
                  ${renderPill(d.status)}
                </div>
              `).join("") || '<p class="muted">No documents uploaded.</p>'}
            </div>
          </div>
        </div>
      </div>
    `;
  },

  selectApp(id) {
    this.selectedAppId = id;
    App.refresh();
  },

  async approveScrutiny(id) {
    await API.transitionApplication(id, "EVC scheduling", "EVC pending", "Scrutiny Committee", "Scrutiny Committee satisfied with preliminary documents; queued for physical EVC inspection.");
    App.toast("Application cleared scrutiny. Queued for EVC scheduling.");
    App.refresh();
  },

  openForwardEVC(id) {
    App.navigate("evc", { appId: id });
  },

  openDeficiencyNotice(id) {
    const app = localStore.db.applications.find(a => a.id === id);
    App.openModal(
      `Issue Statutory Deficiency Memorandum · ${id}`,
      `
        <p style="font-size:12px;color:#64748b;margin-bottom:14px">
          The following deficiencies will be formally communicated to <b>${escapeHtml(app.institution_name)}</b> with a 15-day rectification window:
        </p>
        <div style="display:flex;flex-direction:column;gap:8px;font-size:12px;margin-bottom:14px">
          <label><input type="checkbox" checked /> Land lease registered deed approaching expiry (Expires 25-Oct-2026)</label>
          <label><input type="checkbox" checked /> Cadre ratio deficit: 1 Professor required in Computer Science</label>
          <label><input type="checkbox" /> Fire & Life safety certificate renewal pending</label>
        </div>
        <div class="form-group full">
          <label class="form-label">Scrutiny Officer Observations</label>
          <textarea class="form-control" id="deficiency-remarks">Institution is required to upload registered lease renewal and ratified faculty appointment order within 15 days.</textarea>
        </div>
      `,
      `
        <button class="btn" onclick="App.closeModal()">Cancel</button>
        <button class="btn danger" onclick="ScrutinyModule.confirmDeficiency('${id}')">Dispatch Deficiency Notice</button>
      `
    );
  },

  async confirmDeficiency(id) {
    const remarks = document.getElementById("deficiency-remarks").value;
    await API.transitionApplication(id, "Re-scrutiny", "Returned for rectification", "Scrutiny Officer", remarks, [
      "Land lease registered deed renewal required",
      "Professor cadre ratio deficit in CSE"
    ]);
    App.closeModal();
    App.toast("Deficiency notice dispatched. Application returned for rectification.");
    App.refresh();
  }
};

window.ScrutinyModule = ScrutinyModule;
