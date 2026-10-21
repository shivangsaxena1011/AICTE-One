/**
 * Module 4: Approval Applications & Workflow Register
 */
const ApplicationsModule = {
  state: {
    stage: "",
    status: "",
    search: ""
  },

  async render(params = {}) {
    const apps = await API.getApplications({
      stage: this.state.stage,
      status: this.state.status,
      q: this.state.search
    });

    if (params.id) {
      setTimeout(() => ApplicationsModule.openDetailModal(params.id), 50);
    }

    const rows = apps.map(a => `
      <tr>
        <td>
          <div class="primary-cell-text" style="color:#2563eb;cursor:pointer" onclick="ApplicationsModule.openDetailModal('${a.id}')">${a.id}</div>
          <div class="secondary-cell-text">${escapeHtml(a.type)}</div>
        </td>
        <td>
          <div class="primary-cell-text">${escapeHtml(a.institution_name)}</div>
          <div class="secondary-cell-text">${a.permanent_id}</div>
        </td>
        <td><span class="pill blue">${escapeHtml(a.current_stage)}</span></td>
        <td>${escapeHtml(a.owner)}</td>
        <td>${formatDate(a.submitted_at)}</td>
        <td>${formatDate(a.due_date)}</td>
        <td>
          <div style="display:flex;align-items:center;gap:6px">
            <div style="width:60px;background:#e2e8f0;height:6px;border-radius:10px;overflow:hidden">
              <div style="width:${a.progress}%;background:#2563eb;height:100%"></div>
            </div>
            <b>${a.progress}%</b>
          </div>
        </td>
        <td>${renderPill(a.status)}</td>
        <td>
          <button class="btn sm primary" onclick="ApplicationsModule.openDetailModal('${a.id}')">Review Stage →</button>
        </td>
      </tr>
    `).join("");

    return `
      <div class="page-header">
        <div>
          <div class="page-eyebrow">Approval Workflow Automation</div>
          <h1>Approval Applications Register</h1>
          <p>Track institution applications through preliminary validation, scrutiny, EVC inspections, and committee dispositions.</p>
        </div>
        <div class="header-action-group">
          <button class="btn" onclick="CSVUtil.downloadCSV('aicte_applications_register.csv', localStore.db.applications)">⇩ Export CSV</button>
          <button class="btn primary" onclick="App.openCreateModal('application')">＋ Lodgement Application</button>
        </div>
      </div>

      <!-- Quick Metrics -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-header"><span>IN PROGRESS</span><span>▤</span></div>
          <div class="stat-number">${apps.length}</div>
          <div class="stat-subtext">Active applications</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>SCRUTINY STAGE</span><span>⌕</span></div>
          <div class="stat-number">${apps.filter(a => /scrutiny/i.test(a.current_stage)).length}</div>
          <div class="stat-subtext">Committee scrutiny & re-scrutiny</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>EVC QUEUE</span><span>◷</span></div>
          <div class="stat-number">${apps.filter(a => /evc/i.test(a.current_stage)).length}</div>
          <div class="stat-subtext">Awaiting or scheduled inspection</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>ACTION REQUIRED</span><span>!</span></div>
          <div class="stat-number">${apps.filter(a => /deficiency|rectification|risk/i.test(a.status)).length}</div>
          <div class="stat-subtext">Deficiencies flagged</div>
        </div>
      </div>

      <!-- Register Panel -->
      <div class="panel">
        <div class="filter-toolbar">
          <input
            class="filter-input"
            placeholder="Search application ID or institution…"
            value="${escapeHtml(this.state.search)}"
            oninput="ApplicationsModule.handleSearch(this.value)"
          />
          <select class="filter-select" onchange="ApplicationsModule.handleFilter('stage', this.value)">
            <option value="">All Workflow Stages</option>
            <option value="Preliminary validation">Preliminary validation</option>
            <option value="Scrutiny">Scrutiny</option>
            <option value="Re-scrutiny">Re-scrutiny</option>
            <option value="EVC scheduling">EVC scheduling</option>
            <option value="EVC completed">EVC completed</option>
            <option value="SAC/SHC review">SAC/SHC review</option>
            <option value="Authorized disposition">Authorized disposition</option>
          </select>

          <select class="filter-select" onchange="ApplicationsModule.handleFilter('status', this.value)">
            <option value="">All Statuses</option>
            <option value="New submission">New submission</option>
            <option value="In review">In review</option>
            <option value="Returned for rectification">Returned for rectification</option>
            <option value="EVC pending">EVC pending</option>
            <option value="Approved">Approved</option>
          </select>
          <span style="font-size:11px;color:#64748b;margin-left:auto"><b>${apps.length}</b> applications</span>
        </div>

        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>APPLICATION</th>
                <th>INSTITUTION</th>
                <th>CURRENT STAGE</th>
                <th>OWNER</th>
                <th>SUBMITTED</th>
                <th>TARGET DATE</th>
                <th>PROGRESS</th>
                <th>STATUS</th>
                <th>ACTION</th>
              </tr>
            </thead>
            <tbody>
              ${rows || '<tr><td colspan="9" style="text-align:center;padding:24px;color:#64748b">No applications found matching criteria.</td></tr>'}
            </tbody>
          </table>
        </div>
      </div>
    `;
  },

  handleSearch(val) {
    this.state.search = val;
    App.refresh();
  },

  handleFilter(key, val) {
    this.state[key] = val;
    App.refresh();
  },

  async openDetailModal(id) {
    const app = localStore.db.applications.find(a => a.id === id);
    if (!app) return;

    const stages = [
      "Preliminary validation", "Scrutiny", "Re-scrutiny",
      "EVC scheduling", "EVC completed", "SAC/SHC review", "Authorized disposition"
    ];

    App.openModal(
      `Application Review · ${app.id}`,
      `
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:14px;margin-bottom:16px">
          <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div>
              <h4 style="font-size:14px;font-weight:700;color:#0f172a">${escapeHtml(app.institution_name)}</h4>
              <p style="font-size:11.5px;color:#64748b">Permanent ID: ${app.permanent_id} · ${escapeHtml(app.type)}</p>
            </div>
            ${renderPill(app.status)}
          </div>
          <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:12px;font-size:11.5px">
            <div><span class="muted">Academic Session:</span> <b>${app.academic_year}</b></div>
            <div><span class="muted">Submitted Date:</span> <b>${formatDate(app.submitted_at)}</b></div>
            <div><span class="muted">Target Disposal:</span> <b>${formatDate(app.due_date)}</b></div>
          </div>
        </div>

        <form id="edit-app-stage-form" class="form-grid">
          <div class="form-group">
            <label class="form-label">Workflow Stage *</label>
            <select class="form-control" id="modal-app-stage">
              ${stages.map(s => `<option value="${s}" ${app.current_stage === s ? 'selected' : ''}>${s}</option>`).join("")}
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Workflow Status *</label>
            <select class="form-control" id="modal-app-status">
              <option ${app.status === 'In review' ? 'selected' : ''}>In review</option>
              <option ${app.status === 'EVC pending' ? 'selected' : ''}>EVC pending</option>
              <option ${app.status === 'Returned for rectification' ? 'selected' : ''}>Returned for rectification</option>
              <option ${app.status === 'Approved' ? 'selected' : ''}>Approved</option>
              <option ${app.status === 'Completed' ? 'selected' : ''}>Completed</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Responsible Officer / Committee</label>
            <input class="form-control" id="modal-app-owner" value="${escapeHtml(app.owner)}" />
          </div>
          <div class="form-group">
            <label class="form-label">Progress Percentage (0-100%)</label>
            <input class="form-control" id="modal-app-progress" type="number" min="0" max="100" value="${app.progress}" />
          </div>
          <div class="form-group full">
            <label class="form-label">Action Remarks & Deficiency Rationale</label>
            <textarea class="form-control" id="modal-app-remarks" placeholder="Record scrutiny observation or stage transition rationale...">${escapeHtml(app.last_action || '')}</textarea>
          </div>
        </form>

        <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:10px;margin-top:14px;font-size:11px;color:#1e40af">
          <b>Regulatory Safeguard:</b> Stage transitions update auditable governance records. Advancing to EVC or disposition requires Scrutiny Committee authorization.
        </div>
      `,
      `
        <button class="btn" onclick="App.closeModal()">Cancel</button>
        <button class="btn danger" onclick="ApplicationsModule.returnDeficiency('${app.id}')">Return for Rectification</button>
        <button class="btn primary" onclick="ApplicationsModule.saveStageTransition('${app.id}')">Save Stage Transition</button>
      `
    );
  },

  async saveStageTransition(id) {
    const stage = document.getElementById("modal-app-stage").value;
    const status = document.getElementById("modal-app-status").value;
    const owner = document.getElementById("modal-app-owner").value;
    const remarks = document.getElementById("modal-app-remarks").value;

    await API.transitionApplication(id, stage, status, owner, remarks);
    App.closeModal();
    App.toast("Application stage and status updated successfully.");
    App.refresh();
  },

  async returnDeficiency(id) {
    const remarks = document.getElementById("modal-app-remarks").value || "Deficiencies noted during scrutiny.";
    await API.transitionApplication(id, "Re-scrutiny", "Returned for rectification", "Scrutiny Officer", remarks, ["Fire NOC renewal", "Cadre ratio compliance"]);
    App.closeModal();
    App.toast("Application returned to institution with formal deficiency checklist.");
    App.refresh();
  }
};

window.ApplicationsModule = ApplicationsModule;
