/**
 * Module 9: Complaints and Grievances Registry
 */
const ComplaintsModule = {
  state: {
    bureau: "",
    status: "",
    search: ""
  },

  async render(params = {}) {
    const list = await API.getComplaints();
    let filtered = list;
    if (this.state.bureau) filtered = filtered.filter(c => c.bureau === this.state.bureau);
    if (this.state.status) filtered = filtered.filter(c => c.status === this.state.status);
    if (this.state.search) {
      const q = this.state.search.toLowerCase();
      filtered = filtered.filter(c => (c.id + c.institution_name + c.category + c.summary).toLowerCase().includes(q));
    }

    const rows = filtered.map(c => `
      <tr>
        <td><b>${c.id}</b></td>
        <td>
          <div class="primary-cell-text">${escapeHtml(c.institution_name)}</div>
          <div class="secondary-cell-text">${c.channel}</div>
        </td>
        <td><span class="pill gray">${escapeHtml(c.bureau)}</span></td>
        <td>
          <div class="primary-cell-text">${escapeHtml(c.category)}</div>
          <div class="secondary-cell-text" style="max-width:300px;white-space:normal">${escapeHtml(c.summary)}</div>
        </td>
        <td>${escapeHtml(c.assigned_to)}</td>
        <td>${formatDate(c.received_date)}</td>
        <td>${renderPill(c.status)}</td>
        <td>
          ${c.related_case_id ? `<span class="pill amber" style="cursor:pointer" onclick="App.navigate('coordination')">Linked: ${c.related_case_id}</span>` : '—'}
        </td>
        <td>
          <div style="display:flex;gap:6px">
            <button class="btn sm" onclick="ComplaintsModule.openTransferModal('${c.id}')">Transfer</button>
            <button class="btn sm primary" onclick="ComplaintsModule.openDisposeModal('${c.id}')">Dispose</button>
          </div>
        </td>
      </tr>
    `).join("");

    return `
      <div class="page-header">
        <div>
          <div class="page-eyebrow">Institutional Grievance Intelligence</div>
          <h1>Central Complaints Registry</h1>
          <p>Unify grievance intake across Public Grievance Redressal Cell (PGRC), Regulation Bureau, and Regional Offices.</p>
        </div>
        <div class="header-action-group">
          <button class="btn" onclick="CSVUtil.downloadCSV('aicte_complaints_register.csv', localStore.db.complaints)">⇩ Export CSV</button>
          <button class="btn" onclick="App.navigate('coordination')">⌁ Cross-Bureau Coordination Workspace →</button>
          <button class="btn primary" onclick="ComplaintsModule.openRegisterModal()">＋ Register Grievance / Case</button>
        </div>
      </div>

      <!-- Stats Grid -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-header"><span>OPEN GRIEVANCES</span><span>☷</span></div>
          <div class="stat-number">${list.filter(c => !/closed|disposed/i.test(c.status)).length}</div>
          <div class="stat-subtext">Active grievance dossiers</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>OVERLAPPING CASES</span><span style="color:#b45309">⌁</span></div>
          <div class="stat-number">${list.filter(c => c.related_case_id).length}</div>
          <div class="stat-subtext">Cross-bureau correlation detected</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>BUREAUS INVOLVED</span><span>▦</span></div>
          <div class="stat-number">${new Set(list.map(c => c.bureau)).size}</div>
          <div class="stat-subtext">Coordinating administrative cells</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>AVERAGE DISPOSAL</span><span>◷</span></div>
          <div class="stat-number">14 Days</div>
          <div class="stat-subtext">Citizen charter compliance</div>
        </div>
      </div>

      <!-- Table Panel -->
      <div class="panel">
        <div class="filter-toolbar">
          <input
            class="filter-input"
            placeholder="Search complaint ID, institution, or summary…"
            value="${escapeHtml(this.state.search)}"
            oninput="ComplaintsModule.handleSearch(this.value)"
          />
          <select class="filter-select" onchange="ComplaintsModule.handleFilter('bureau', this.value)">
            <option value="">All Bureaus / Cells</option>
            <option value="PGRC">PGRC</option>
            <option value="Regulation Bureau">Regulation Bureau</option>
            <option value="Regional Office">Regional Office</option>
            <option value="Approval Bureau">Approval Bureau</option>
          </select>
          <select class="filter-select" onchange="ComplaintsModule.handleFilter('status', this.value)">
            <option value="">All Statuses</option>
            <option value="Received">Received</option>
            <option value="Assigned">Assigned</option>
            <option value="Under process">Under process</option>
            <option value="Awaiting information">Awaiting information</option>
            <option value="Disposed or closed">Disposed or closed</option>
          </select>
          <span style="font-size:11px;color:#64748b;margin-left:auto"><b>${filtered.length}</b> cases</span>
        </div>

        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>CASE ID</th>
                <th>INSTITUTION</th>
                <th>BUREAU / CELL</th>
                <th>CATEGORY & SUMMARY</th>
                <th>INVESTIGATOR</th>
                <th>RECEIVED</th>
                <th>STATUS</th>
                <th>CROSS-BUREAU LINK</th>
                <th>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              ${rows || '<tr><td colspan="9" style="text-align:center;padding:24px;color:#64748b">No complaints recorded.</td></tr>'}
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

  openRegisterModal() {
    App.openModal(
      "Register Citizen Grievance / Institutional Complaint",
      `
        <form id="create-complaint-form" class="form-grid">
          <div class="form-group full">
            <label class="form-label">Institution Concerned *</label>
            <select class="form-control" id="cplt-inst-id" required>
              ${localStore.db.institutions.map(i => `<option value="${i.id}">${escapeHtml(i.name)} (${i.permanent_id})</option>`).join("")}
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Receiving Bureau / Cell *</label>
            <select class="form-control" id="cplt-bureau">
              <option>PGRC</option>
              <option>Regulation Bureau</option>
              <option>Regional Office</option>
              <option>Approval Bureau</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Category *</label>
            <select class="form-control" id="cplt-category">
              <option>Student Admission & Intake</option>
              <option>Faculty & Staff Grievance</option>
              <option>Fee Refund / Overcharging</option>
              <option>Infrastructure Deficiency</option>
              <option>Institutional Records Discrepancy</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Intake Channel</label>
            <select class="form-control" id="cplt-channel">
              <option>Central Grievance Portal (CPGRAMS)</option>
              <option>Online Grievance Submission</option>
              <option>Internal Audit Alert</option>
              <option>Regional Office Referral</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Assigned Investigator</label>
            <input class="form-control" id="cplt-owner" value="M. Joshi (Grievance Officer)" />
          </div>
          <div class="form-group full">
            <label class="form-label">Grievance Summary *</label>
            <textarea class="form-control" id="cplt-summary" required placeholder="Clear summary of allegations or audit discrepancy..."></textarea>
          </div>
        </form>
      `,
      `
        <button class="btn" onclick="App.closeModal()">Cancel</button>
        <button class="btn primary" onclick="ComplaintsModule.confirmRegister()">Register Dossier</button>
      `
    );
  },

  confirmRegister() {
    const instId = document.getElementById("cplt-inst-id").value;
    const inst = localStore.db.institutions.find(i => i.id === instId);
    const summary = document.getElementById("cplt-summary").value;
    const bureau = document.getElementById("cplt-bureau").value;
    const category = document.getElementById("cplt-category").value;

    if (!summary) {
      alert("Summary is required.");
      return;
    }

    const newCase = {
      id: "CASE-" + Math.floor(1000 + Math.random() * 9000),
      institution_id: instId,
      institution_name: inst ? inst.name : "Institution",
      bureau: bureau,
      category: category,
      summary: summary,
      channel: document.getElementById("cplt-channel").value,
      status: "Received",
      assigned_to: document.getElementById("cplt-owner").value,
      received_date: new Date().toISOString().slice(0, 10),
      due_date: "2026-11-15",
      related_case_id: "",
      overlap_score: 0
    };

    // Real-time overlap scan against other complaints for this institution
    const otherCase = localStore.db.complaints.find(c => c.institution_id === instId && c.id !== newCase.id);
    if (otherCase) {
      newCase.related_case_id = otherCase.id;
      newCase.overlap_score = 90;
      newCase.overlap_reason = `Exact Institution Permanent ID (${inst.permanent_id}) correlation; overlapping administrative enquiry.`;
    }

    localStore.db.complaints.unshift(newCase);
    localStore.log(newCase.assigned_to, "Grievance Officer", "Registered Complaint Case", "Complaint", newCase.id, `Registered case for ${newCase.institution_name} in ${bureau}.`);
    localStore.save();
    App.closeModal();
    App.toast("Grievance case registered successfully.");
    App.refresh();
  },

  openTransferModal(id) {
    const c = localStore.db.complaints.find(x => x.id === id);
    App.openModal(
      `Transfer Grievance Dossier · ${c.id}`,
      `
        <div style="font-size:12px;margin-bottom:12px">
          <b>Case:</b> ${c.id} (${escapeHtml(c.bureau)})<br>
          <b>Institution:</b> ${escapeHtml(c.institution_name)}
        </div>
        <div class="form-group full">
          <label class="form-label">Transfer To Bureau / Cell *</label>
          <select class="form-control" id="transfer-bureau">
            <option>Regulation Bureau</option>
            <option>Approval Bureau</option>
            <option>PGRC</option>
            <option>Regional Office</option>
            <option>Central Vigilance Cell</option>
          </select>
        </div>
        <div class="form-group full" style="margin-top:10px">
          <label class="form-label">Transfer Rationale</label>
          <textarea class="form-control" id="transfer-reason">Transferred for coordinated regulatory audit.</textarea>
        </div>
      `,
      `
        <button class="btn" onclick="App.closeModal()">Cancel</button>
        <button class="btn primary" onclick="ComplaintsModule.confirmTransfer('${id}')">Execute Transfer</button>
      `
    );
  },

  confirmTransfer(id) {
    const c = localStore.db.complaints.find(x => x.id === id);
    if (c) {
      const old = c.bureau;
      c.bureau = document.getElementById("transfer-bureau").value;
      c.status = "Transferred";
      localStore.log("Grievance Officer", "Grievance Cell", "Transferred Complaint", "Complaint", c.id, `Transferred from ${old} to ${c.bureau}.`);
      localStore.save();
    }
    App.closeModal();
    App.toast("Grievance transferred to target Bureau.");
    App.refresh();
  },

  openDisposeModal(id) {
    const c = localStore.db.complaints.find(x => x.id === id);
    App.openModal(
      `Dispose & Close Grievance Case · ${c.id}`,
      `
        <div style="font-size:12px;margin-bottom:12px">
          <b>Summary:</b> ${escapeHtml(c.summary)}
        </div>
        <div class="form-group full">
          <label class="form-label">Final Disposal Order / Resolution Notes *</label>
          <textarea class="form-control" id="disposal-notes" style="min-height:90px" placeholder="Record inquiry outcome, compliance deed verified, or corrective directives issued..."></textarea>
        </div>
      `,
      `
        <button class="btn" onclick="App.closeModal()">Cancel</button>
        <button class="btn primary" onclick="ComplaintsModule.confirmDispose('${id}')">Disposed & Close File</button>
      `
    );
  },

  confirmDispose(id) {
    const c = localStore.db.complaints.find(x => x.id === id);
    if (c) {
      c.status = "Disposed or closed";
      c.resolution_notes = document.getElementById("disposal-notes").value;
      localStore.log("Disposal Authority", "Competent Authority", "Disposed Complaint Case", "Complaint", c.id, `Case closed with order: ${c.resolution_notes.slice(0, 60)}...`);
      localStore.save();
    }
    App.closeModal();
    App.toast("Grievance case disposed and closed.");
    App.refresh();
  }
};

window.ComplaintsModule = ComplaintsModule;
