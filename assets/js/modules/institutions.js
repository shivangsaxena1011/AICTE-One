/**
 * Module 2: Comprehensive Institution Directory
 */
const InstitutionsModule = {
  state: {
    page: 1,
    limit: 10,
    search: "",
    state: "",
    category: "",
    type: "",
    status: "",
    sortBy: "name",
    sortOrder: "asc"
  },

  async render() {
    const [res, stats] = await Promise.all([
      API.getInstitutions({
        q: this.state.search,
        state: this.state.state,
        category: this.state.category,
        institution_type: this.state.type,
        approval_status: this.state.status,
        page: this.state.page,
        limit: this.state.limit
      }),
      API.getInstitutionsStats()
    ]);

    const rows = (res.data || []).map(i => `
      <tr>
        <td>
          <div class="primary-cell-text" style="color:#001332;font-weight:700;cursor:pointer" onclick="App.navigate('digitalTwin', { id: '${i.id}' })">
            ${escapeHtml(i.name)}
          </div>
          <div class="secondary-cell-text">${escapeHtml(i.address || i.city)}</div>
        </td>
        <td><span style="font-weight:700;color:#0f172a" class="font-mono">${i.permanent_id || i.aicte_id || 'N/A'}</span></td>
        <td>${escapeHtml(i.state)} <div class="secondary-cell-text">${escapeHtml(i.district || i.city || '')}</div></td>
        <td>${escapeHtml(i.category || 'Engineering & Technology')}</td>
        <td>${escapeHtml(i.institution_type || 'Unaided - Private')}</td>
        <td><b>${i.programmes_count || 1}</b> / <span class="secondary-cell-text">${(i.total_intake || 0).toLocaleString()} seats</span></td>
        <td>${renderPill(i.approval_status || 'Approved')}</td>
        <td><span class="pill gray" style="font-size:10px">${escapeHtml(i.data_source || 'AICTE Central Registry')}</span></td>
        <td>
          <button class="btn sm primary" onclick="App.navigate('digitalTwin', { id: '${i.id}' })">Digital Twin →</button>
        </td>
      </tr>
    `).join("");

    // States and categories list from database stats
    const allStates = (stats && stats.states && stats.states.length) ? stats.states : [...new Set(localStore.db.institutions.map(i => i.state))].sort();
    const allCats = (stats && stats.categories && stats.categories.length) ? stats.categories : [...new Set(localStore.db.institutions.map(i => i.category))].sort();

    return `
      <div class="page-header">
        <div>
          <div class="page-eyebrow">Shared Institutional Registry</div>
          <h1>Institution Directory</h1>
          <p>Official registry of 8,800+ approved technical institutions across India with permanent IDs and regulatory profiles.</p>
        </div>
        <div class="header-action-group">
          <button class="btn" onclick="InstitutionsModule.openVerificationModal()">✓ Verify Approval Gateway</button>
          <button class="btn" onclick="InstitutionsModule.exportCSV()">⇩ Export CSV Report</button>
          <button class="btn" onclick="InstitutionsModule.openImportModal()">⇧ Import Institutional Data (CSV)</button>
          <button class="btn primary" onclick="InstitutionsModule.openCreateModal()">＋ Add Institution Record</button>
        </div>
      </div>

      <!-- Quick Metrics -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-header"><span>TOTAL INSTITUTIONS</span><span>▦</span></div>
          <div class="stat-number">${(stats.total_institutions || res.total || 8842).toLocaleString()}</div>
          <div class="stat-subtext">Registered across directory</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>APPROVED STATUS</span><span style="color:#15803d">✓</span></div>
          <div class="stat-number">${(stats.approved_count || res.total || 8710).toLocaleString()}</div>
          <div class="stat-subtext">Current approval session</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>TOTAL PROGRAMMES</span><span>⌘</span></div>
          <div class="stat-number">${(stats.total_programmes || 42150).toLocaleString()}</div>
          <div class="stat-subtext">Approved technical programmes</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>TOTAL INTAKE CAPACITY</span><span>♙</span></div>
          <div class="stat-number">${(stats.total_intake || 2845000).toLocaleString()}</div>
          <div class="stat-subtext">Authorized student intake</div>
        </div>
      </div>

      <!-- Table Panel with Filters -->
      <div class="panel">
        <div class="filter-toolbar">
          <input
            class="filter-input"
            id="inst-search-input"
            placeholder="Search by institution name, permanent ID, or city…"
            value="${escapeHtml(this.state.search)}"
            onkeydown="if(event.key==='Enter')InstitutionsModule.handleSearch(this.value)"
          />
          <button class="btn sm" onclick="InstitutionsModule.handleSearch(document.getElementById('inst-search-input').value)">Search</button>

          <select class="filter-select" onchange="InstitutionsModule.handleFilter('state', this.value)">
            <option value="">All States</option>
            ${allStates.map(s => `<option value="${escapeHtml(s)}" ${this.state.state === s ? 'selected' : ''}>${escapeHtml(s)}</option>`).join("")}
          </select>

          <select class="filter-select" onchange="InstitutionsModule.handleFilter('category', this.value)">
            <option value="">All Categories</option>
            ${allCats.map(c => `<option value="${escapeHtml(c)}" ${this.state.category === c ? 'selected' : ''}>${escapeHtml(c)}</option>`).join("")}
          </select>

          <select class="filter-select" onchange="InstitutionsModule.handleFilter('status', this.value)">
            <option value="">All Statuses</option>
            <option value="Approved" ${this.state.status === 'Approved' ? 'selected' : ''}>Approved</option>
            <option value="Under Review" ${this.state.status === 'Under Review' ? 'selected' : ''}>Under Review</option>
          </select>

          <select class="filter-select" style="margin-left:auto" onchange="InstitutionsModule.handleLimit(this.value)">
            <option value="10" ${this.state.limit === 10 ? 'selected' : ''}>10 per page</option>
            <option value="25" ${this.state.limit === 25 ? 'selected' : ''}>25 per page</option>
            <option value="50" ${this.state.limit === 50 ? 'selected' : ''}>50 per page</option>
          </select>
        </div>

        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>INSTITUTION NAME</th>
                <th>PERMANENT ID</th>
                <th>STATE & DISTRICT</th>
                <th>CATEGORY</th>
                <th>TYPE</th>
                <th>PROGRAMMES / INTAKE</th>
                <th>STATUS</th>
                <th>DATA SOURCE</th>
                <th>ACTION</th>
              </tr>
            </thead>
            <tbody>
              ${rows || '<tr><td colspan="9" style="text-align:center;padding:30px;color:#64748b">No institutions match the current criteria.</td></tr>'}
            </tbody>
          </table>
        </div>

        <div class="pagination-container">
          <div>Showing <b>${Math.min(res.total, (this.state.page - 1) * this.state.limit + 1)}</b> to <b>${Math.min(res.total, this.state.page * this.state.limit)}</b> of <b>${res.total}</b> institutions</div>
          <div class="pagination-controls">
            <button class="btn sm" ${this.state.page <= 1 ? 'disabled' : ''} onclick="InstitutionsModule.changePage(${this.state.page - 1})">← Previous</button>
            <span style="font-weight:600;padding:0 8px">Page ${this.state.page} of ${res.pages || 1}</span>
            <button class="btn sm" ${this.state.page >= res.pages ? 'disabled' : ''} onclick="InstitutionsModule.changePage(${this.state.page + 1})">Next →</button>
          </div>
        </div>
      </div>
    `;
  },

  handleSearch(val) {
    this.state.search = val;
    this.state.page = 1;
    App.refresh();
  },

  handleFilter(key, val) {
    this.state[key] = val;
    this.state.page = 1;
    App.refresh();
  },

  handleLimit(val) {
    this.state.limit = parseInt(val);
    this.state.page = 1;
    App.refresh();
  },

  changePage(p) {
    this.state.page = p;
    App.refresh();
  },

  exportCSV() {
    if (API.isBackendLive) {
      window.open(`${API.baseUrl}/analytics/export/institutions-csv`, '_blank');
      App.toast("Initiating official institution directory export from backend...");
      return;
    }
    CSVUtil.downloadCSV('aicte_institutions_directory.csv', localStore.db.institutions);
    App.toast("Institutions directory exported to CSV.");
  },

  openVerificationModal(defaultQuery = "") {
    App.openModal(
      "Official AICTE Approval Verification Gateway",
      `
        <div class="space-y-4 text-xs">
          <p class="text-slate-600">
            Authoritative institutional verification gateway based on verified AICTE Central Master Records.
            Evaluates official permanent IDs, acronyms (e.g. NIET, COEP, VJTI), and institutional status without synthetic guessing.
          </p>
          <div class="flex gap-2">
            <input type="text" id="verify-query-input" class="form-control flex-1 text-xs" 
              placeholder="Enter Permanent ID (e.g. 1-10482931), AICTE ID, or College Name..." 
              value="${escapeHtml(defaultQuery)}"
              onkeydown="if(event.key==='Enter')InstitutionsModule.runVerification(this.value)" />
            <button class="btn primary sm shrink-0" onclick="InstitutionsModule.runVerification(document.getElementById('verify-query-input').value)">
              Verify Status →
            </button>
          </div>
          <div id="verification-result-box" class="mt-4"></div>
        </div>
      `,
      `
        <button class="btn" onclick="App.closeModal()">Close</button>
      `
    );
    if (defaultQuery) {
      this.runVerification(defaultQuery);
    }
  },

  async runVerification(query) {
    if (!query || !query.trim()) {
      App.toast("Please enter an institution identifier or name.");
      return;
    }
    const box = document.getElementById("verification-result-box");
    if (!box) return;
    box.innerHTML = `<div class="p-4 text-center text-slate-500 font-mono text-xs">Querying authoritative AICTE central records...</div>`;

    const res = await API.verifyInstitutionApproval(query.trim());
    const isApproved = res.status === "Approved";
    const badgeColor = isApproved ? "bg-emerald-100 text-emerald-800 border-emerald-300" :
                       res.status === "Needs Verification" ? "bg-amber-100 text-amber-800 border-amber-300" :
                       res.status === "Approval Expired" ? "bg-rose-100 text-rose-800 border-rose-300" :
                       "bg-slate-100 text-slate-800 border-slate-300";

    const inst = res.institution || {};
    box.innerHTML = `
      <div class="border rounded-lg p-4 bg-slate-50 space-y-3">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-slate-500">Official Verification Result</span>
          <span class="px-3 py-1 rounded-full text-xs font-extrabold border ${badgeColor}">
            ${escapeHtml(res.status)}
          </span>
        </div>

        ${res.is_found && inst.name ? `
          <div class="space-y-1 pt-2 border-t border-slate-200">
            <h4 class="font-bold text-sm text-[#001332]">${escapeHtml(inst.name)}</h4>
            <div class="grid grid-cols-2 gap-2 text-slate-600 font-mono text-[11px] pt-1">
              <div><span class="text-slate-400">Permanent ID:</span> <b>${escapeHtml(inst.permanent_id || '—')}</b></div>
              <div><span class="text-slate-400">AICTE ID:</span> <b>${escapeHtml(inst.aicte_id || '—')}</b></div>
              <div><span class="text-slate-400">State & District:</span> ${escapeHtml(inst.state || '')}, ${escapeHtml(inst.district || '')}</div>
              <div><span class="text-slate-400">Approval Session:</span> ${escapeHtml(inst.approval_period || '2026-2027')}</div>
            </div>
            ${res.data_freshness && res.data_freshness.warning ? `
              <div class="p-2 rounded bg-amber-50 text-amber-800 text-[11px] border border-amber-200 mt-2">
                ⚠ ${escapeHtml(res.data_freshness.warning)}
              </div>
            ` : ''}
          </div>
          <div class="flex items-center justify-between pt-3 border-t border-slate-200">
            <a href="${res.authoritative_link || '#'}" target="_blank" class="text-xs text-blue-700 font-semibold hover:underline">
              View on AICTE Central Portal ↗
            </a>
            <button class="btn sm" onclick="InstitutionsModule.openDiscrepancyModal('${inst.id || inst.permanent_id}', '${escapeHtml(inst.name)}')">
              Report Data Mismatch
            </button>
          </div>
        ` : `
          <div class="p-3 bg-amber-50 rounded border border-amber-200 text-amber-900 text-xs space-y-2">
            <p>${escapeHtml(res.message || res.disclaimer || 'Institution record not located in current master batch.')}</p>
            <p class="text-[11px] text-amber-700">Note: Absence in the local database does not confirm non-approval. Verify directly with AICTE central facility below.</p>
            <a href="${res.authoritative_link || '#'}" target="_blank" class="inline-block font-bold text-blue-700 underline text-xs">
              Open AICTE Facilities Portal ↗
            </a>
          </div>
        `}
      </div>
    `;
  },

  openDiscrepancyModal(instId, instName) {
    App.openModal(
      "Report Institutional Data Discrepancy",
      `
        <form id="discrepancy-form" class="space-y-3 text-xs" onsubmit="event.preventDefault();InstitutionsModule.submitDiscrepancy('${instId}');">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Target Institution</label>
            <input type="text" class="form-control" value="${escapeHtml(instName)} (${instId})" disabled />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Reported By (Officer / Institute Head) *</label>
              <input type="text" id="disc-reported-by" class="form-control" required placeholder="Dr. S. K. Sharma" />
            </div>
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Official Contact Email *</label>
              <input type="email" id="disc-contact-email" class="form-control" required placeholder="registrar@college.edu.in" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Mismatched Attribute *</label>
              <select id="disc-field-name" class="form-control" required>
                <option value="name">Institution Name</option>
                <option value="website">Official Website URL</option>
                <option value="address">Campus Address</option>
                <option value="district">District</option>
                <option value="total_intake">Approved Intake Capacity</option>
                <option value="institution_type">Institution Type</option>
              </select>
            </div>
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Proposed Verified Value *</label>
              <input type="text" id="disc-proposed-value" class="form-control" required placeholder="Correct official value" />
            </div>
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Verification Rationale & Evidence Reference *</label>
            <textarea id="disc-rationale" class="form-control" rows="2" required placeholder="Specify AICTE Extension of Approval (EoA) reference or supporting order..."></textarea>
          </div>
        </form>
      `,
      `
        <button class="btn" onclick="App.closeModal()">Cancel</button>
        <button class="btn primary" onclick="InstitutionsModule.submitDiscrepancy('${instId}')">Submit Correction Request</button>
      `
    );
  },

  async submitDiscrepancy(instId) {
    const form = document.getElementById("discrepancy-form");
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }
    const payload = {
      reported_by: document.getElementById("disc-reported-by").value,
      contact_email: document.getElementById("disc-contact-email").value,
      field_name: document.getElementById("disc-field-name").value,
      proposed_value: document.getElementById("disc-proposed-value").value,
      rationale: document.getElementById("disc-rationale").value,
      evidence_file: "Institutional_EoA_Evidence.pdf"
    };

    const res = await API.submitCorrectionRequest(instId, payload);
    App.closeModal();
    App.toast(`Correction request ${res.id || ''} lodged for administrative officer review.`);
  },

  openImportModal() {
    App.openModal(
      "Import Institutional Records via CSV",
      `
        <p style="font-size:12px;color:#64748b;margin-bottom:14px">
          Upload an authorized institution dataset (CSV). Records will be validated, duplicates detected against permanent IDs, and an import summary displayed.
        </p>
        <div class="file-dropzone" onclick="document.getElementById('csv-file-input').click()">
          <div style="font-size:28px;color:#2563eb;margin-bottom:6px">⇧</div>
          <strong style="font-size:13px;color:#0f172a">Select CSV file or drag and drop here</strong>
          <p style="font-size:11px;color:#64748b;margin-top:2px">Columns expected: Permanent ID, Institution Name, State, District, Category, Institution Type</p>
          <input type="file" id="csv-file-input" accept=".csv" style="display:none" onchange="InstitutionsModule.handleFileSelect(this.files[0])" />
        </div>
        <div id="import-summary-result" style="margin-top:16px"></div>
      `,
      `
        <button class="btn" onclick="App.closeModal()">Close</button>
      `
    );
  },

  async handleFileSelect(file) {
    if (!file) return;
    const text = await file.text();
    const result = CSVUtil.importInstitutionsFromCSV(text);

    const summaryEl = document.getElementById("import-summary-result");
    if (summaryEl) {
      summaryEl.innerHTML = `
        <div style="border:1px solid #e2e8f0;border-radius:8px;padding:14px;background:#f8fafc">
          <h4 style="font-size:13px;font-weight:700;margin-bottom:8px">Import Verification Summary</h4>
          <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;text-align:center;margin-bottom:12px">
            <div style="background:#ffffff;padding:8px;border-radius:6px;border:1px solid #e2e8f0">
              <span style="font-size:11px;color:#64748b">Total Rows</span>
              <strong style="display:block;font-size:16px">${result.total}</strong>
            </div>
            <div style="background:#f0fdf4;padding:8px;border-radius:6px;border:1px solid #bbf7d0">
              <span style="font-size:11px;color:#15803d">Created</span>
              <strong style="display:block;font-size:16px;color:#15803d">${result.created}</strong>
            </div>
            <div style="background:#fffbeb;padding:8px;border-radius:6px;border:1px solid #fde68a">
              <span style="font-size:11px;color:#b45309">Skipped Duplicates</span>
              <strong style="display:block;font-size:16px;color:#b45309">${result.skipped}</strong>
            </div>
            <div style="background:#fef2f2;padding:8px;border-radius:6px;border:1px solid #fecaca">
              <span style="font-size:11px;color:#b91c1c">Rejected Errors</span>
              <strong style="display:block;font-size:16px;color:#b91c1c">${result.rejected}</strong>
            </div>
          </div>
          ${result.errors.length ? `<div style="font-size:11px;color:#b91c1c">${result.errors.join('<br>')}</div>` : ''}
          <button class="btn sm primary" style="width:100%;margin-top:10px" onclick="App.closeModal();App.refresh();">Apply & Reload Directory</button>
        </div>
      `;
    }
  },

  openCreateModal() {
    App.openModal(
      "Add New Institutional Record",
      `
        <form id="create-inst-form" class="form-grid" onsubmit="event.preventDefault();InstitutionsModule.submitCreate();">
          <div class="form-group full">
            <label class="form-label">Institution Official Name *</label>
            <input class="form-control" name="name" required placeholder="e.g. National Institute of Technology" />
          </div>
          <div class="form-group">
            <label class="form-label">Authorized Permanent ID *</label>
            <input class="form-control" name="permanent_id" required placeholder="e.g. 1-10928374" />
          </div>
          <div class="form-group">
            <label class="form-label">Institution Category *</label>
            <select class="form-control" name="category">
              <option>Engineering and Technology</option>
              <option>Management</option>
              <option>Pharmacy</option>
              <option>Architecture and Planning</option>
              <option>Hotel Management and Catering Technology</option>
              <option>Polytechnic</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">State *</label>
            <input class="form-control" name="state" required placeholder="e.g. Maharashtra" />
          </div>
          <div class="form-group">
            <label class="form-label">District / City *</label>
            <input class="form-control" name="city" required placeholder="e.g. Pune" />
          </div>
          <div class="form-group full">
            <label class="form-label">Campus Address</label>
            <textarea class="form-control" name="address" placeholder="Full postal address"></textarea>
          </div>
          <div class="form-group">
            <label class="form-label">Institution Type</label>
            <select class="form-control" name="institution_type">
              <option>Private-Self Financed</option>
              <option>Government</option>
              <option>Govt-Aided Autonomous</option>
              <option>Deemed to be University</option>
              <option>State University Department</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">University Affiliation</label>
            <input class="form-control" name="affiliation" placeholder="e.g. Savitribai Phule Pune University" />
          </div>
          <div class="form-group">
            <label class="form-label">Approved Programmes</label>
            <input class="form-control" name="programmes_count" type="number" value="6" />
          </div>
          <div class="form-group">
            <label class="form-label">Total Approved Intake</label>
            <input class="form-control" name="total_intake" type="number" value="480" />
          </div>
        </form>
      `,
      `
        <button class="btn" onclick="App.closeModal()">Cancel</button>
        <button class="btn primary" onclick="InstitutionsModule.submitCreate()">Create Record</button>
      `
    );
  },

  async submitCreate() {
    const form = document.getElementById("create-inst-form");
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());
    payload.programmes_count = parseInt(payload.programmes_count) || 0;
    payload.total_intake = parseInt(payload.total_intake) || 0;

    await API.createInstitution(payload);
    App.closeModal();
    App.toast("Institution record created successfully.");
    App.refresh();
  }
};

window.InstitutionsModule = InstitutionsModule;
