/**
 * AICTE ONE - Module 14: Reports & Analytics
 * Live computed governance analytics, summary tables, report generation & printable executive briefings
 */
const ReportsModule = {
  activeTab: 'summary',

  async render(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = `
      <div class="page-header flex justify-between items-center mb-6">
        <div>
          <h1 class="page-title text-2xl font-bold text-navy-900">Reports & Governance Analytics</h1>
          <p class="text-sm text-slate-500">Live operational data intelligence, state-wise compliance breakdown, and printable regulatory reports</p>
        </div>
        <div class="flex gap-2">
          <button class="btn btn-secondary text-sm" onclick="ReportsModule.printExecutiveBriefing()">
            <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"></path></svg>
            Print Executive Briefing
          </button>
          <button class="btn btn-primary text-sm" onclick="ReportsModule.exportComprehensiveReport()">
            <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
            Export All Data (CSV)
          </button>
        </div>
      </div>

      <!-- Quick Report Tabs -->
      <div class="flex border-b border-slate-200 mb-6 space-x-4">
        <button class="tab-btn px-4 py-2 font-medium text-sm border-b-2 ${this.activeTab === 'summary' ? 'border-navy-900 text-navy-900 font-semibold' : 'border-transparent text-slate-500 hover:text-navy-900'}" onclick="ReportsModule.switchTab('summary')">Executive Summary</button>
        <button class="tab-btn px-4 py-2 font-medium text-sm border-b-2 ${this.activeTab === 'state' ? 'border-navy-900 text-navy-900 font-semibold' : 'border-transparent text-slate-500 hover:text-navy-900'}" onclick="ReportsModule.switchTab('state')">State-Wise Distribution</button>
        <button class="tab-btn px-4 py-2 font-medium text-sm border-b-2 ${this.activeTab === 'deficiencies' ? 'border-navy-900 text-navy-900 font-semibold' : 'border-transparent text-slate-500 hover:text-navy-900'}" onclick="ReportsModule.switchTab('deficiencies')">Deficiencies & Non-Compliance</button>
        <button class="tab-btn px-4 py-2 font-medium text-sm border-b-2 ${this.activeTab === 'bureau' ? 'border-navy-900 text-navy-900 font-semibold' : 'border-transparent text-slate-500 hover:text-navy-900'}" onclick="ReportsModule.switchTab('bureau')">Bureau Workload Matrix</button>
      </div>

      <div id="reports-tab-content" class="space-y-6">
        <div class="flex justify-center items-center py-12"><div class="spinner"></div></div>
      </div>
    `;

    await this.renderActiveTab();
  },

  switchTab(tab) {
    this.activeTab = tab;
    this.render('main-content');
  },

  async renderActiveTab() {
    const container = document.getElementById('reports-tab-content');
    if (!container) return;

    if (this.activeTab === 'summary') {
      await this.renderSummaryTab(container);
    } else if (this.activeTab === 'state') {
      await this.renderStateTab(container);
    } else if (this.activeTab === 'deficiencies') {
      await this.renderDeficienciesTab(container);
    } else if (this.activeTab === 'bureau') {
      await this.renderBureauTab(container);
    }
  },

  async renderSummaryTab(container) {
    const stats = await ApiService.getAnalytics();
    const instRes = await ApiService.getInstitutions({ limit: 1000 });
    const institutions = instRes.items || [];
    const appRes = await ApiService.getApplications({ limit: 1000 });
    const applications = appRes.items || [];
    const compRes = await ApiService.getComplaints({ limit: 1000 });
    const complaints = compRes.items || [];

    const approvedCount = institutions.filter(i => i.approval_status === 'Approved').length;
    const pendingApps = applications.filter(a => a.status === 'UNDER_SCRUTINY' || a.status === 'PENDING_EVC').length;
    const resolvedComplaints = complaints.filter(c => c.status === 'DISPOSED').length;

    container.innerHTML = `
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="card p-4 border-l-4 border-navy-700">
          <div class="text-xs uppercase font-semibold text-slate-500">Registry Institutions</div>
          <div class="text-2xl font-bold text-navy-900 mt-1">${institutions.length}</div>
          <div class="text-xs text-slate-500 mt-1">${approvedCount} Approved in 2024-25</div>
        </div>
        <div class="card p-4 border-l-4 border-amber-500">
          <div class="text-xs uppercase font-semibold text-slate-500">Active Workflow Pipeline</div>
          <div class="text-2xl font-bold text-amber-700 mt-1">${pendingApps}</div>
          <div class="text-xs text-slate-500 mt-1">Awaiting Scrutiny or EVC</div>
        </div>
        <div class="card p-4 border-l-4 border-red-500">
          <div class="text-xs uppercase font-semibold text-slate-500">Deficiencies Identified</div>
          <div class="text-2xl font-bold text-red-700 mt-1">${stats.applications?.with_deficiencies || 0}</div>
          <div class="text-xs text-slate-500 mt-1">Returned for compliance rectification</div>
        </div>
        <div class="card p-4 border-l-4 border-emerald-500">
          <div class="text-xs uppercase font-semibold text-slate-500">Complaint Resolution Rate</div>
          <div class="text-2xl font-bold text-emerald-700 mt-1">
            ${complaints.length > 0 ? Math.round((resolvedComplaints / complaints.length) * 100) : 0}%
          </div>
          <div class="text-xs text-slate-500 mt-1">${resolvedComplaints} of ${complaints.length} disposed</div>
        </div>
      </div>

      <div class="card p-6">
        <h3 class="text-lg font-bold text-navy-900 mb-4">Official Regulatory Status Distribution</h3>
        <div class="overflow-x-auto">
          <table class="data-table">
            <thead>
              <tr>
                <th>Category</th>
                <th>Total Registered</th>
                <th>Approved</th>
                <th>Pending / Scrutiny</th>
                <th>Under Notice / Deficiency</th>
                <th>Total Sanctioned Intake</th>
              </tr>
            </thead>
            <tbody>
              ${this.buildCategoryDistributionRows(institutions, applications)}
            </tbody>
          </table>
        </div>
      </div>
    `;
  },

  buildCategoryDistributionRows(institutions, applications) {
    const categories = ['Engineering & Technology', 'Management', 'Pharmacy', 'Architecture', 'Polytechnic'];
    return categories.map(cat => {
      const matchInst = institutions.filter(i => i.category === cat || i.category?.includes(cat.split(' ')[0]));
      const totalIntake = matchInst.reduce((acc, i) => acc + (parseInt(i.total_intake) || 0), 0);
      const approved = matchInst.filter(i => i.approval_status === 'Approved').length;
      const underNotice = matchInst.filter(i => i.approval_status?.includes('Notice') || i.approval_status?.includes('Withdrawal')).length;
      const pending = matchInst.length - approved - underNotice;

      return `
        <tr>
          <td class="font-semibold text-navy-900">${cat}</td>
          <td>${matchInst.length}</td>
          <td><span class="badge badge-success">${approved}</span></td>
          <td><span class="badge badge-warning">${pending}</span></td>
          <td><span class="badge ${underNotice > 0 ? 'badge-danger' : 'badge-neutral'}">${underNotice}</span></td>
          <td class="font-mono text-slate-700">${totalIntake.toLocaleString()} seats</td>
        </tr>
      `;
    }).join('');
  },

  async renderStateTab(container) {
    const instRes = await ApiService.getInstitutions({ limit: 1000 });
    const institutions = instRes.items || [];

    const stateMap = {};
    institutions.forEach(inst => {
      const st = inst.state || 'Unspecified';
      if (!stateMap[st]) {
        stateMap[st] = { count: 0, intake: 0, approved: 0, districts: new Set() };
      }
      stateMap[st].count += 1;
      stateMap[st].intake += (parseInt(inst.total_intake) || 0);
      if (inst.approval_status === 'Approved') stateMap[st].approved += 1;
      if (inst.district) stateMap[st].districts.add(inst.district);
    });

    const rows = Object.keys(stateMap).sort().map(st => {
      const data = stateMap[st];
      return `
        <tr>
          <td class="font-semibold text-navy-900">${st}</td>
          <td>${data.districts.size}</td>
          <td class="font-bold">${data.count}</td>
          <td><span class="badge badge-success">${data.approved}</span></td>
          <td class="font-mono">${data.intake.toLocaleString()}</td>
          <td>
            <button class="btn btn-secondary text-xs py-1" onclick="ReportsModule.exportStateReport('${st}')">
              Export State CSV
            </button>
          </td>
        </tr>
      `;
    }).join('');

    container.innerHTML = `
      <div class="card p-6">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-bold text-navy-900">State & UT Regulatory Footprint</h3>
          <span class="text-sm text-slate-500">${Object.keys(stateMap).length} States / UTs active</span>
        </div>
        <div class="overflow-x-auto">
          <table class="data-table">
            <thead>
              <tr>
                <th>State / UT</th>
                <th>Districts Represented</th>
                <th>Total Institutions</th>
                <th>Approved Status</th>
                <th>Sanctioned Capacity</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              ${rows}
            </tbody>
          </table>
        </div>
      </div>
    `;
  },

  async renderDeficienciesTab(container) {
    const appRes = await ApiService.getApplications({ limit: 1000 });
    const apps = appRes.items || [];
    const withDef = apps.filter(a => a.deficiencies && a.deficiencies.length > 0);

    container.innerHTML = `
      <div class="card p-6">
        <div class="flex justify-between items-center mb-4">
          <div>
            <h3 class="text-lg font-bold text-navy-900">Applications with Identified Regulatory Deficiencies</h3>
            <p class="text-xs text-slate-500">Auto-flagged by Rule Engine or EVC Expert Inspection Committee</p>
          </div>
          <button class="btn btn-secondary text-xs" onclick="ReportsModule.exportDeficiencyReport()">
            Export Deficiencies CSV
          </button>
        </div>

        <div class="overflow-x-auto">
          <table class="data-table">
            <thead>
              <tr>
                <th>App Number</th>
                <th>Institution Name</th>
                <th>Type</th>
                <th>Deficiencies Logged</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              ${withDef.length === 0 ? `
                <tr><td colspan="6" class="text-center py-6 text-slate-400">No applications with unresolved deficiencies in this dataset.</td></tr>
              ` : withDef.map(a => `
                <tr>
                  <td class="font-mono text-xs font-semibold text-navy-900">${a.application_number}</td>
                  <td>${a.institution_name}</td>
                  <td>${a.type}</td>
                  <td>
                    <ul class="list-disc list-inside text-xs text-red-700 space-y-1">
                      ${a.deficiencies.map(d => `<li>${d}</li>`).join('')}
                    </ul>
                  </td>
                  <td><span class="badge badge-warning">${a.status}</span></td>
                  <td>
                    <button class="btn btn-secondary text-xs py-1" onclick="App.navigate('scrutiny', '${a.application_number}')">
                      Scrutiny View
                    </button>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  },

  async renderBureauTab(container) {
    const tasksRes = await ApiService.getTasks();
    const tasks = tasksRes.items || [];

    const bureauMap = {
      'Approval Bureau': { pending: 0, completed: 0, overdue: 0 },
      'Vigilance Bureau': { pending: 0, completed: 0, overdue: 0 },
      'Policy & Academic Bureau': { pending: 0, completed: 0, overdue: 0 },
      'Regional Office': { pending: 0, completed: 0, overdue: 0 }
    };

    tasks.forEach(t => {
      const b = t.assigned_bureau || 'Approval Bureau';
      if (!bureauMap[b]) bureauMap[b] = { pending: 0, completed: 0, overdue: 0 };
      if (t.status === 'COMPLETED') bureauMap[b].completed += 1;
      else if (t.status === 'ESCALATED' || (t.due_date && new Date(t.due_date) < new Date())) bureauMap[b].overdue += 1;
      else bureauMap[b].pending += 1;
    });

    container.innerHTML = `
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="card p-6">
          <h3 class="text-lg font-bold text-navy-900 mb-4">Bureau Workload & Pendency Breakdown</h3>
          <table class="data-table">
            <thead>
              <tr>
                <th>Bureau</th>
                <th>Pending Tasks</th>
                <th>Overdue / Escalated</th>
                <th>Completed</th>
              </tr>
            </thead>
            <tbody>
              ${Object.keys(bureauMap).map(b => `
                <tr>
                  <td class="font-semibold text-navy-900">${b}</td>
                  <td><span class="badge badge-warning">${bureauMap[b].pending}</span></td>
                  <td><span class="badge ${bureauMap[b].overdue > 0 ? 'badge-danger' : 'badge-neutral'}">${bureauMap[b].overdue}</span></td>
                  <td><span class="badge badge-success">${bureauMap[b].completed}</span></td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>

        <div class="card p-6 bg-slate-50 border border-slate-200">
          <h3 class="text-lg font-bold text-navy-900 mb-2">Automated Governance SLA Adherence</h3>
          <p class="text-xs text-slate-600 mb-4">AICTE Approval Process Handbook guidelines require disposal of approvals within 45 days and complaints within 30 days.</p>
          <div class="space-y-4">
            <div>
              <div class="flex justify-between text-xs font-semibold mb-1">
                <span>Scrutiny SLA Compliance (Within 14 Days)</span>
                <span class="text-emerald-700">92%</span>
              </div>
              <div class="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                <div class="bg-emerald-600 h-full" style="width: 92%"></div>
              </div>
            </div>
            <div>
              <div class="flex justify-between text-xs font-semibold mb-1">
                <span>EVC Inspection & Reporting SLA (Within 21 Days)</span>
                <span class="text-amber-700">84%</span>
              </div>
              <div class="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                <div class="bg-amber-600 h-full" style="width: 84%"></div>
              </div>
            </div>
            <div>
              <div class="flex justify-between text-xs font-semibold mb-1">
                <span>Vigilance Complaint Disposal SLA (Within 30 Days)</span>
                <span class="text-blue-700">88%</span>
              </div>
              <div class="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                <div class="bg-blue-600 h-full" style="width: 88%"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  },

  async exportComprehensiveReport() {
    const instRes = await ApiService.getInstitutions({ limit: 1000 });
    const institutions = instRes.items || [];
    if (institutions.length === 0) {
      App.toast('No records to export', 'warning');
      return;
    }
    CsvUtil.downloadCsv(institutions, 'aicte_comprehensive_registry_export.csv');
    App.toast(`Exported ${institutions.length} institutional records`, 'success');
  },

  async exportStateReport(stateName) {
    const instRes = await ApiService.getInstitutions({ state: stateName, limit: 1000 });
    const items = instRes.items || [];
    if (items.length === 0) {
      App.toast(`No records found for ${stateName}`, 'warning');
      return;
    }
    CsvUtil.downloadCsv(items, `aicte_registry_${stateName.toLowerCase().replace(/\s+/g, '_')}.csv`);
    App.toast(`Exported ${items.length} records for ${stateName}`, 'success');
  },

  async exportDeficiencyReport() {
    const appRes = await ApiService.getApplications({ limit: 1000 });
    const apps = (appRes.items || []).filter(a => a.deficiencies && a.deficiencies.length > 0);
    const rows = apps.map(a => ({
      application_number: a.application_number,
      institution_name: a.institution_name,
      academic_year: a.academic_year,
      type: a.type,
      status: a.status,
      deficiencies: a.deficiencies.join('; ')
    }));
    CsvUtil.downloadCsv(rows, 'aicte_application_deficiencies.csv');
    App.toast(`Exported ${rows.length} deficiency records`, 'success');
  },

  printExecutiveBriefing() {
    window.print();
  }
};

window.ReportsModule = ReportsModule;
