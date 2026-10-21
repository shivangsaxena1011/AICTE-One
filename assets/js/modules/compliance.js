/**
 * Module 8: Regulatory Compliance Intelligence
 */
const ComplianceModule = {
  state: {
    status: "",
    search: ""
  },

  async render(params = {}) {
    const list = await API.getCompliance();
    let filtered = list;
    if (this.state.status) {
      filtered = filtered.filter(c => c.status === this.state.status);
    }
    if (this.state.search) {
      const q = this.state.search.toLowerCase();
      filtered = filtered.filter(c => (c.title + c.institution_name + c.category).toLowerCase().includes(q));
    }

    const rows = filtered.map(c => `
      <tr>
        <td>
          <div class="primary-cell-text">${escapeHtml(c.title)}</div>
          <div class="secondary-cell-text">${c.id} · ${escapeHtml(c.category)}</div>
        </td>
        <td>
          <div class="primary-cell-text">${escapeHtml(c.institution_name)}</div>
        </td>
        <td><b>${formatDate(c.due_date)}</b></td>
        <td>${escapeHtml(c.responsible_party)}</td>
        <td>${escapeHtml(c.evidence_file || '—')}</td>
        <td>${renderPill(c.status)}</td>
        <td>
          <div style="display:flex;gap:6px">
            <button class="btn sm" onclick="ComplianceModule.openUploadEvidenceModal('${c.id}')">Upload Evidence</button>
            <button class="btn sm primary" onclick="ComplianceModule.openReviewModal('${c.id}')">Review</button>
          </div>
        </td>
      </tr>
    `).join("");

    return `
      <div class="page-header">
        <div>
          <div class="page-eyebrow">Regulatory Undertakings & Deadline Monitoring</div>
          <h1>Regulatory Compliance Intelligence</h1>
          <p>Monitor time-bound statutory undertakings, land lease renewals, and fire clearance validity across institutions.</p>
        </div>
        <div class="header-action-group">
          <button class="btn" onclick="CSVUtil.downloadCSV('aicte_compliance_register.csv', localStore.db.compliance)">⇩ Export CSV</button>
          <button class="btn primary" onclick="ComplianceModule.openCreateModal()">＋ Lodgement Obligation</button>
        </div>
      </div>

      <!-- Stats Grid -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-header"><span>TOTAL OBLIGATIONS</span><span>◷</span></div>
          <div class="stat-number">${list.length}</div>
          <div class="stat-subtext">Active undertakings tracked</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>OVERDUE</span><span style="color:#b91c1c">!</span></div>
          <div class="stat-number">${list.filter(c => c.status === 'Overdue').length}</div>
          <div class="stat-subtext">Statutory deadline passed</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>DUE SOON</span><span style="color:#b45309">◴</span></div>
          <div class="stat-number">${list.filter(c => /due soon|action/i.test(c.status)).length}</div>
          <div class="stat-subtext">Within 7-day threshold</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>SATISFIED</span><span style="color:#15803d">✓</span></div>
          <div class="stat-number">${list.filter(c => /satisfied|on track/i.test(c.status)).length}</div>
          <div class="stat-subtext">Evidence verified</div>
        </div>
      </div>

      <!-- Compliance Panel -->
      <div class="panel">
        <div class="filter-toolbar">
          <input
            class="filter-input"
            placeholder="Search obligation title or institution…"
            value="${escapeHtml(this.state.search)}"
            oninput="ComplianceModule.handleSearch(this.value)"
          />
          <select class="filter-select" onchange="ComplianceModule.handleFilter('status', this.value)">
            <option value="">All Compliance Statuses</option>
            <option value="Overdue">Overdue</option>
            <option value="Due soon">Due soon</option>
            <option value="On track">On track</option>
            <option value="Action required">Action required</option>
            <option value="Evidence submitted">Evidence submitted</option>
            <option value="Satisfied by evidence">Satisfied by evidence</option>
          </select>
          <span style="font-size:11px;color:#64748b;margin-left:auto"><b>${filtered.length}</b> obligations</span>
        </div>

        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>OBLIGATION ITEM</th>
                <th>INSTITUTION</th>
                <th>DUE DATE</th>
                <th>RESPONSIBLE PARTY</th>
                <th>EVIDENCE RECORD</th>
                <th>STATUS</th>
                <th>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              ${rows || '<tr><td colspan="7" style="text-align:center;padding:24px;color:#64748b">No compliance obligations match criteria.</td></tr>'}
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

  openCreateModal() {
    App.openModal(
      "Add Compliance Obligation",
      `
        <form id="create-comp-form" class="form-grid">
          <div class="form-group full">
            <label class="form-label">Institution *</label>
            <select class="form-control" id="comp-inst-id" required>
              ${localStore.db.institutions.map(i => `<option value="${i.id}">${escapeHtml(i.name)} (${i.permanent_id})</option>`).join("")}
            </select>
          </div>
          <div class="form-group full">
            <label class="form-label">Obligation Title / Statutory Requirement *</label>
            <input class="form-control" id="comp-title" required placeholder="e.g. Registered Land Lease Renewal Agreement" />
          </div>
          <div class="form-group">
            <label class="form-label">Category</label>
            <select class="form-control" id="comp-cat">
              <option>Time-bound undertaking</option>
              <option>Document expiry</option>
              <option>Evidence submission</option>
              <option>Regulatory undertaking</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Due Date *</label>
            <input class="form-control" id="comp-due" type="date" required value="2026-11-15" />
          </div>
          <div class="form-group">
            <label class="form-label">Responsible Entity</label>
            <input class="form-control" id="comp-owner" value="Institution Management" />
          </div>
          <div class="form-group">
            <label class="form-label">Evidence Reference</label>
            <input class="form-control" id="comp-evidence" value="—" />
          </div>
        </form>
      `,
      `
        <button class="btn" onclick="App.closeModal()">Cancel</button>
        <button class="btn primary" onclick="ComplianceModule.confirmCreate()">Create Obligation</button>
      `
    );
  },

  confirmCreate() {
    const instId = document.getElementById("comp-inst-id").value;
    const inst = localStore.db.institutions.find(i => i.id === instId);
    const newComp = {
      id: "CMP-" + Math.floor(1000 + Math.random() * 9000),
      institution_id: instId,
      institution_name: inst ? inst.name : "Institution",
      title: document.getElementById("comp-title").value,
      category: document.getElementById("comp-cat").value,
      due_date: document.getElementById("comp-due").value,
      responsible_party: document.getElementById("comp-owner").value,
      status: "Upcoming",
      evidence_file: document.getElementById("comp-evidence").value || "—",
      review_notes: "Statutory obligation lodged."
    };

    localStore.db.compliance.unshift(newComp);
    localStore.log("Compliance Officer", "Compliance Division", "Created Compliance Obligation", "Compliance", newComp.id, `Created obligation '${newComp.title}' for ${newComp.institution_name}.`);
    localStore.save();
    App.closeModal();
    App.toast("Compliance obligation created.");
    App.refresh();
  },

  openUploadEvidenceModal(id) {
    const c = localStore.db.compliance.find(x => x.id === id);
    App.openModal(
      `Submit Compliance Evidence · ${c.id}`,
      `
        <div style="font-size:12px;margin-bottom:12px">
          <b>Obligation:</b> ${escapeHtml(c.title)}<br>
          <b>Institution:</b> ${escapeHtml(c.institution_name)}
        </div>
        <div class="form-group full">
          <label class="form-label">Evidence Document Filename / Reference *</label>
          <input class="form-control" id="evidence-file-name" value="Renewal_Undertaking_${c.id}.pdf" />
        </div>
        <div class="form-group full" style="margin-top:10px">
          <label class="form-label">Submission Remarks</label>
          <textarea class="form-control" id="evidence-remarks" placeholder="Sub-Registrar acknowledgment or council resolution reference..."></textarea>
        </div>
      `,
      `
        <button class="btn" onclick="App.closeModal()">Cancel</button>
        <button class="btn primary" onclick="ComplianceModule.confirmEvidence('${id}')">Record Submission</button>
      `
    );
  },

  confirmEvidence(id) {
    const c = localStore.db.compliance.find(x => x.id === id);
    if (c) {
      c.evidence_file = document.getElementById("evidence-file-name").value;
      c.status = "Evidence submitted";
      localStore.log("Institution User", "Institution", "Uploaded Compliance Evidence", "Compliance", c.id, `Uploaded evidence ${c.evidence_file}.`);
      localStore.save();
    }
    App.closeModal();
    App.toast("Evidence submitted for officer verification.");
    App.refresh();
  },

  openReviewModal(id) {
    const c = localStore.db.compliance.find(x => x.id === id);
    App.openModal(
      `Review Compliance Evidence · ${c.id}`,
      `
        <div style="font-size:12px;margin-bottom:12px">
          <b>Obligation:</b> ${escapeHtml(c.title)}<br>
          <b>Evidence File:</b> ${escapeHtml(c.evidence_file)}
        </div>
        <div class="form-group full">
          <label class="form-label">Review Verdict *</label>
          <select class="form-control" id="review-verdict">
            <option>Satisfied by evidence</option>
            <option>Action required</option>
            <option>Overdue</option>
          </select>
        </div>
        <div class="form-group full" style="margin-top:10px">
          <label class="form-label">Reviewer Observations & Order</label>
          <textarea class="form-control" id="review-notes">Evidence scrutinized and verified in accordance with statutory guidelines.</textarea>
        </div>
      `,
      `
        <button class="btn" onclick="App.closeModal()">Cancel</button>
        <button class="btn primary" onclick="ComplianceModule.confirmReview('${id}')">Save Official Finding</button>
      `
    );
  },

  confirmReview(id) {
    const c = localStore.db.compliance.find(x => x.id === id);
    if (c) {
      c.status = document.getElementById("review-verdict").value;
      c.review_notes = document.getElementById("review-notes").value;
      c.reviewed_by = "Compliance Officer";
      c.reviewed_at = new Date().toISOString();
      localStore.log("Compliance Officer", "Compliance Division", "Reviewed Compliance Obligation", "Compliance", c.id, `Marked as ${c.status}. Notes: ${c.review_notes}`);
      localStore.save();
    }
    App.closeModal();
    App.toast("Review recorded successfully.");
    App.refresh();
  }
};

window.ComplianceModule = ComplianceModule;
