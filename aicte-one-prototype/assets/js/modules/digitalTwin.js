/**
 * Module 3: Institution Digital Twin (360° Unified View)
 */
const DigitalTwinModule = {
  currentTab: "overview",
  selectedInstitutionId: "INST-10482",

  async render(params = {}) {
    if (App.currentUser && App.currentUser.role === 'INSTITUTE_HEAD') {
      if (App.currentUser.institution_id) {
        if (params.id && params.id !== App.currentUser.institution_id) {
          App.toast("Tenant boundary enforced: Switched to your bound institution.", "warning");
        }
        this.selectedInstitutionId = App.currentUser.institution_id;
      }
    } else if (params.id) {
      this.selectedInstitutionId = params.id;
    }
    const twin = await API.getInstitutionDigitalTwin(this.selectedInstitutionId);
    if (!twin) {
      return `
        <div class="page-header">
          <h1>Institution Digital Twin</h1>
          <p>Please select an institution from the directory.</p>
        </div>
        <button class="btn primary" onclick="App.navigate('institutions')">← Return to Directory</button>
      `;
    }

    const inst = twin.institution;
    const apps = twin.applications || [];
    const docs = twin.documents || [];
    const comps = twin.compliance || [];
    const cases = twin.complaints || [];
    const tasks = twin.tasks || [];
    const audits = twin.activity_timeline || [];

    // Tab content generation
    let tabContent = "";
    if (this.currentTab === "overview") {
      tabContent = `
        <div class="grid-2">
          <div class="panel">
            <div class="panel-header"><h3>Regulatory Identity & Accreditation</h3></div>
            <div class="panel-body">
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;font-size:12px">
                <div><span class="muted">Institution Name:</span><strong style="display:block;margin-top:2px">${escapeHtml(inst.name)}</strong></div>
                <div><span class="muted">AICTE Permanent ID:</span><strong style="display:block;margin-top:2px;color:#2563eb">${inst.permanent_id}</strong></div>
                <div><span class="muted">Category:</span><div style="margin-top:2px">${escapeHtml(inst.category)}</div></div>
                <div><span class="muted">Type:</span><div style="margin-top:2px">${escapeHtml(inst.institution_type)}</div></div>
                <div><span class="muted">Affiliating University:</span><div style="margin-top:2px">${escapeHtml(inst.affiliation || 'Autonomous')}</div></div>
                <div><span class="muted">Website:</span><div style="margin-top:2px"><a href="${inst.website || '#'}" target="_blank" style="color:#2563eb">${escapeHtml(inst.website || 'Not provided')}</a></div></div>
                <div><span class="muted">Approved Programmes:</span><div style="margin-top:2px"><b>${inst.programmes_count}</b> programmes</div></div>
                <div><span class="muted">Intake Capacity:</span><div style="margin-top:2px"><b>${inst.total_intake}</b> seats</div></div>
              </div>
            </div>
          </div>

          <div class="panel">
            <div class="panel-header"><h3>Location & Authorized Data Source</h3></div>
            <div class="panel-body">
              <div style="display:grid;gap:12px;font-size:12px">
                <div><span class="muted">Campus Address:</span><div style="margin-top:2px">${escapeHtml(inst.address || inst.city)}</div></div>
                <div><span class="muted">State & District:</span><div style="margin-top:2px">${escapeHtml(inst.state)} — ${escapeHtml(inst.district)}</div></div>
                <div><span class="muted">Data Provenance:</span><div style="margin-top:2px"><span class="pill gray">${escapeHtml(inst.data_source)}</span> (${inst.verified_status})</div></div>
                <div><span class="muted">Last Synchronized:</span><div style="margin-top:2px">${formatDate(inst.last_verified)}</div></div>
              </div>
            </div>
          </div>
        </div>
      `;
    } else if (this.currentTab === "applications") {
      tabContent = `
        <div class="panel">
          <div class="panel-header">
            <h3>Approval Applications & Workflows</h3>
            <button class="btn sm primary" onclick="App.openCreateModal('application', '${inst.id}')">＋ Lodge Application</button>
          </div>
          <div class="table-responsive">
            <table class="data-table">
              <thead>
                <tr>
                  <th>APPLICATION ID</th>
                  <th>TYPE</th>
                  <th>STAGE</th>
                  <th>OWNER</th>
                  <th>PROGRESS</th>
                  <th>STATUS</th>
                  <th>ACTION</th>
                </tr>
              </thead>
              <tbody>
                ${apps.map(a => `
                  <tr>
                    <td><b>${a.id}</b></td>
                    <td>${escapeHtml(a.type)}</td>
                    <td><span class="pill blue">${escapeHtml(a.current_stage)}</span></td>
                    <td>${escapeHtml(a.owner)}</td>
                    <td>${a.progress}%</td>
                    <td>${renderPill(a.status)}</td>
                    <td><button class="btn sm" onclick="App.navigate('applications', { id: '${a.id}' })">Review →</button></td>
                  </tr>
                `).join("") || '<tr><td colspan="7" style="text-align:center;padding:20px;color:#64748b">No active applications.</td></tr>'}
              </tbody>
            </table>
          </div>
        </div>
      `;
    } else if (this.currentTab === "documents") {
      tabContent = `
        <div class="panel">
          <div class="panel-header">
            <h3>Document Inventory & AI Verification Status</h3>
            <button class="btn sm primary" onclick="App.navigate('verification')">Verify Document</button>
          </div>
          <div class="table-responsive">
            <table class="data-table">
              <thead>
                <tr>
                  <th>DOCUMENT</th>
                  <th>TYPE</th>
                  <th>CONFIDENCE</th>
                  <th>VERIFICATION RESULT</th>
                  <th>EVIDENCE / FINDINGS</th>
                  <th>AUTHORITY REF</th>
                </tr>
              </thead>
              <tbody>
                ${docs.map(d => `
                  <tr>
                    <td><b>${escapeHtml(d.name)}</b><div class="secondary-cell-text">${d.id}</div></td>
                    <td>${escapeHtml(d.document_type)}</td>
                    <td><b>${d.confidence}</b></td>
                    <td>${renderPill(d.status)}</td>
                    <td style="max-width:300px;white-space:normal;font-size:11px">${escapeHtml(d.findings)}</td>
                    <td><code>${escapeHtml(d.authority_ref || '—')}</code></td>
                  </tr>
                `).join("") || '<tr><td colspan="6" style="text-align:center;padding:20px;color:#64748b">No documents on record.</td></tr>'}
              </tbody>
            </table>
          </div>
        </div>
      `;
    } else if (this.currentTab === "compliance") {
      tabContent = `
        <div class="panel">
          <div class="panel-header">
            <h3>Compliance Obligations & Undertakings</h3>
            <button class="btn sm primary" onclick="App.navigate('compliance')">Add Obligation</button>
          </div>
          <div class="table-responsive">
            <table class="data-table">
              <thead>
                <tr>
                  <th>OBLIGATION TITLE</th>
                  <th>CATEGORY</th>
                  <th>DUE DATE</th>
                  <th>RESPONSIBLE</th>
                  <th>EVIDENCE FILE</th>
                  <th>STATUS</th>
                </tr>
              </thead>
              <tbody>
                ${comps.map(c => `
                  <tr>
                    <td><b>${escapeHtml(c.title)}</b><div class="secondary-cell-text">${c.id}</div></td>
                    <td>${escapeHtml(c.category)}</td>
                    <td>${formatDate(c.due_date)}</td>
                    <td>${escapeHtml(c.responsible_party)}</td>
                    <td>${escapeHtml(c.evidence_file || '—')}</td>
                    <td>${renderPill(c.status)}</td>
                  </tr>
                `).join("") || '<tr><td colspan="6" style="text-align:center;padding:20px;color:#64748b">No obligations tracked.</td></tr>'}
              </tbody>
            </table>
          </div>
        </div>
      `;
    } else if (this.currentTab === "complaints") {
      tabContent = `
        <div class="panel">
          <div class="panel-header">
            <h3>Grievances & Cross-Bureau Complaints</h3>
            <button class="btn sm primary" onclick="App.navigate('complaints')">Register Complaint</button>
          </div>
          <div class="table-responsive">
            <table class="data-table">
              <thead>
                <tr>
                  <th>CASE ID</th>
                  <th>BUREAU</th>
                  <th>CATEGORY</th>
                  <th>SUMMARY</th>
                  <th>STATUS</th>
                  <th>RELATED CASE</th>
                </tr>
              </thead>
              <tbody>
                ${cases.map(c => `
                  <tr>
                    <td><b>${c.id}</b></td>
                    <td>${escapeHtml(c.bureau)}</td>
                    <td>${escapeHtml(c.category)}</td>
                    <td style="max-width:320px;white-space:normal;font-size:11px">${escapeHtml(c.summary)}</td>
                    <td>${renderPill(c.status)}</td>
                    <td>${c.related_case_id ? `<span class="pill amber">${c.related_case_id}</span>` : '—'}</td>
                  </tr>
                `).join("") || '<tr><td colspan="6" style="text-align:center;padding:20px;color:#64748b">No complaints filed.</td></tr>'}
              </tbody>
            </table>
          </div>
        </div>
      `;
    } else if (this.currentTab === "timeline") {
      tabContent = `
        <div class="panel">
          <div class="panel-header"><h3>Chronological Governance Activity Timeline</h3></div>
          <div class="panel-body">
            <div style="display:grid;gap:16px">
              ${audits.map(a => `
                <div style="display:grid;grid-template-columns:30px 1fr;gap:14px;position:relative">
                  <div style="width:30px;height:30px;border-radius:8px;background:#eff6ff;color:#2563eb;display:grid;place-items:center;font-weight:700">●</div>
                  <div>
                    <strong style="font-size:12.5px;color:#0f172a">${escapeHtml(a.action)}</strong>
                    <p style="font-size:11.5px;color:#64748b;margin:3px 0">${escapeHtml(a.detail)}</p>
                    <small style="font-size:10.5px;color:#94a3b8">${escapeHtml(a.actor)} (${escapeHtml(a.role)}) · ${escapeHtml(a.time)}</small>
                  </div>
                </div>
              `).join("") || '<p class="muted">No activity records logged.</p>'}
            </div>
          </div>
        </div>
      `;
    }

    return `
      <div class="page-header">
        <div>
          <div class="page-eyebrow">Institutional Digital Twin</div>
          <h1>${escapeHtml(inst.name)}</h1>
          <p>Connected administrative digital twin unifying approval records, compliance obligations, grievances, and document intelligence.</p>
        </div>
        <div class="header-action-group">
          <button class="btn" onclick="App.navigate('institutions')">← Return to Directory</button>
          <button class="btn" onclick="window.print()">⎙ Print Digital Twin Profile</button>
          <button class="btn primary" onclick="App.openCreateModal('application', '${inst.id}')">＋ Lodgement Application</button>
        </div>
      </div>

      <!-- Identity Banner -->
      <div class="twin-banner">
        <div>
          <h2>${escapeHtml(inst.name)}</h2>
          <p style="color:#cbd5e1;font-size:12px">${escapeHtml(inst.city)}, ${escapeHtml(inst.state)} · ${escapeHtml(inst.category)}</p>
          <div class="twin-meta-row">
            <div class="twin-meta-item"><span>AICTE Permanent ID</span><b>${inst.permanent_id}</b></div>
            <div class="twin-meta-item"><span>Approval Status</span><b>${inst.approval_status} (${inst.approval_period})</b></div>
            <div class="twin-meta-item"><span>Programmes</span><b>${inst.programmes_count}</b></div>
            <div class="twin-meta-item"><span>Approved Intake</span><b>${inst.total_intake} seats</b></div>
            <div class="twin-meta-item"><span>University Affiliation</span><b>${escapeHtml(inst.affiliation || 'Autonomous')}</b></div>
          </div>
        </div>
        <div>
          ${renderPill(inst.approval_status)}
          <div style="margin-top:10px">${renderPill(inst.verified_status)}</div>
        </div>
      </div>

      <!-- Stats Counters -->
      <div class="stats-grid">
        <div class="stat-card" onclick="DigitalTwinModule.switchTab('applications')">
          <div class="stat-header"><span>APPLICATIONS</span><span>▤</span></div>
          <div class="stat-number">${apps.length}</div>
          <div class="stat-subtext">Approval workflow cases</div>
        </div>
        <div class="stat-card" onclick="DigitalTwinModule.switchTab('documents')">
          <div class="stat-header"><span>DOCUMENTS</span><span>◈</span></div>
          <div class="stat-number">${docs.length}</div>
          <div class="stat-subtext">Ingested & verified</div>
        </div>
        <div class="stat-card" onclick="DigitalTwinModule.switchTab('compliance')">
          <div class="stat-header"><span>COMPLIANCE OBLIGATIONS</span><span>◷</span></div>
          <div class="stat-number">${comps.length}</div>
          <div class="stat-subtext">Active undertakings</div>
        </div>
        <div class="stat-card" onclick="DigitalTwinModule.switchTab('complaints')">
          <div class="stat-header"><span>COMPLAINTS & GRIEVANCES</span><span>☷</span></div>
          <div class="stat-number">${cases.length}</div>
          <div class="stat-subtext">Independent case files</div>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <div class="tabs-nav">
        <button class="tab-btn ${this.currentTab === 'overview' ? 'active' : ''}" onclick="DigitalTwinModule.switchTab('overview')">Overview & Identity</button>
        <button class="tab-btn ${this.currentTab === 'applications' ? 'active' : ''}" onclick="DigitalTwinModule.switchTab('applications')">Applications (${apps.length})</button>
        <button class="tab-btn ${this.currentTab === 'documents' ? 'active' : ''}" onclick="DigitalTwinModule.switchTab('documents')">Documents (${docs.length})</button>
        <button class="tab-btn ${this.currentTab === 'compliance' ? 'active' : ''}" onclick="DigitalTwinModule.switchTab('compliance')">Compliance (${comps.length})</button>
        <button class="tab-btn ${this.currentTab === 'complaints' ? 'active' : ''}" onclick="DigitalTwinModule.switchTab('complaints')">Complaints (${cases.length})</button>
        <button class="tab-btn ${this.currentTab === 'timeline' ? 'active' : ''}" onclick="DigitalTwinModule.switchTab('timeline')">Activity Timeline (${audits.length})</button>
      </div>

      <!-- Active Tab Content -->
      <div>
        ${tabContent}
      </div>
    `;
  },

  switchTab(tab) {
    this.currentTab = tab;
    App.refresh();
  }
};

window.DigitalTwinModule = DigitalTwinModule;
