/**
 * AICTE ONE - Module 16: Audit Trail
 * Immutable governance log viewer, actor accountability, entity diff inspection, and CSV export
 */
const AuditModule = {
  currentFilters: {
    entity_type: '',
    search: '',
    page: 1,
    limit: 25
  },

  async render(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = `
      <div class="page-header flex justify-between items-center mb-6">
        <div>
          <h1 class="page-title text-2xl font-bold text-navy-900">Regulatory Audit Trail & Log</h1>
          <p class="text-sm text-slate-500">Append-only compliance log recording all administrative decisions, document inspections, and state transitions</p>
        </div>
        <div class="flex gap-2">
          <button class="btn btn-secondary text-sm" onclick="AuditModule.exportCsv()">
            <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
            Export Audit Trail (CSV)
          </button>
        </div>
      </div>

      <!-- Filters -->
      <div class="card p-4 mb-6 bg-slate-50 border border-slate-200">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div class="md:col-span-2">
            <label class="block text-xs font-semibold text-slate-600 mb-1">Search Action / Entity ID / Actor</label>
            <input type="text" id="audit-search" class="input text-sm w-full" placeholder="e.g. DEFICIENCIES_RECORDED, APP-2024-001, officer@aicte..." value="${this.currentFilters.search}">
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1">Entity Domain</label>
            <select id="audit-entity-type" class="select text-sm w-full">
              <option value="">All Entities</option>
              <option value="APPLICATION" ${this.currentFilters.entity_type === 'APPLICATION' ? 'selected' : ''}>Application</option>
              <option value="INSTITUTION" ${this.currentFilters.entity_type === 'INSTITUTION' ? 'selected' : ''}>Institution</option>
              <option value="DOCUMENT" ${this.currentFilters.entity_type === 'DOCUMENT' ? 'selected' : ''}>Document</option>
              <option value="COMPLIANCE" ${this.currentFilters.entity_type === 'COMPLIANCE' ? 'selected' : ''}>Compliance</option>
              <option value="COMPLAINT" ${this.currentFilters.entity_type === 'COMPLAINT' ? 'selected' : ''}>Complaint</option>
              <option value="TASK" ${this.currentFilters.entity_type === 'TASK' ? 'selected' : ''}>Task</option>
              <option value="EVC" ${this.currentFilters.entity_type === 'EVC' ? 'selected' : ''}>EVC Visit</option>
            </select>
          </div>
          <div class="flex items-end gap-2">
            <button class="btn btn-primary text-sm flex-1" onclick="AuditModule.applyFilters()">Apply Filters</button>
            <button class="btn btn-secondary text-sm" onclick="AuditModule.resetFilters()">Reset</button>
          </div>
        </div>
      </div>

      <!-- Audit Table -->
      <div class="card p-0 overflow-hidden">
        <div class="overflow-x-auto">
          <table class="data-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Action Code</th>
                <th>Entity Domain</th>
                <th>Entity ID</th>
                <th>Authorized Actor</th>
                <th>IP / Channel</th>
                <th>Audit Details</th>
              </tr>
            </thead>
            <tbody id="audit-table-body">
              <tr><td colspan="7" class="text-center py-12"><div class="spinner"></div></td></tr>
            </tbody>
          </table>
        </div>
        <div id="audit-pagination" class="p-4 border-t border-slate-200 flex justify-between items-center text-xs text-slate-500"></div>
      </div>
    `;

    document.getElementById('audit-search').addEventListener('keypress', (e) => {
      if (e.key === 'Enter') AuditModule.applyFilters();
    });

    await this.loadAuditLogs();
  },

  applyFilters() {
    this.currentFilters.search = document.getElementById('audit-search').value.trim();
    this.currentFilters.entity_type = document.getElementById('audit-entity-type').value;
    this.currentFilters.page = 1;
    this.loadAuditLogs();
  },

  resetFilters() {
    this.currentFilters.search = '';
    this.currentFilters.entity_type = '';
    this.currentFilters.page = 1;
    document.getElementById('audit-search').value = '';
    document.getElementById('audit-entity-type').value = '';
    this.loadAuditLogs();
  },

  async loadAuditLogs() {
    const tbody = document.getElementById('audit-table-body');
    const pagination = document.getElementById('audit-pagination');
    if (!tbody) return;

    const params = {
      page: this.currentFilters.page,
      limit: this.currentFilters.limit,
      search: this.currentFilters.search,
      entity_type: this.currentFilters.entity_type
    };

    const res = await ApiService.getAuditLogs(params);
    const logs = res.items || [];
    const total = res.total || logs.length;

    if (logs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-8 text-slate-400">No audit records match the selected filter.</td></tr>`;
      pagination.innerHTML = 'Showing 0 records';
      return;
    }

    tbody.innerHTML = logs.map(l => {
      const ts = l.timestamp ? new Date(l.timestamp).toLocaleString('en-IN', {
        day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit'
      }) : 'N/A';

      const actionBadges = {
        CREATE: 'badge-success',
        STATUS_CHANGE: 'badge-warning',
        DEFICIENCIES_RECORDED: 'badge-danger',
        REJECT: 'badge-danger',
        UPDATE: 'badge-neutral',
        ESCALATE: 'badge-danger'
      };
      const badgeClass = actionBadges[l.action] || 'badge-neutral';

      return `
        <tr>
          <td class="font-mono text-xs text-slate-500 whitespace-nowrap">${ts}</td>
          <td><span class="badge ${badgeClass} text-[10px] font-mono font-semibold">${l.action}</span></td>
          <td class="font-semibold text-slate-700 text-xs">${l.entity_type}</td>
          <td class="font-mono text-xs font-bold text-navy-900">${l.entity_id}</td>
          <td class="text-xs text-slate-600">${l.actor}</td>
          <td class="font-mono text-xs text-slate-400">${l.ip_address || '127.0.0.1'}</td>
          <td>
            <button class="btn btn-secondary text-xs py-1" onclick="AuditModule.viewDetails('${l.id}')">
              Inspect Diff
            </button>
          </td>
        </tr>
      `;
    }).join('');

    const totalPages = Math.ceil(total / this.currentFilters.limit) || 1;
    pagination.innerHTML = `
      <div>Showing ${((this.currentFilters.page - 1) * this.currentFilters.limit) + 1} to ${Math.min(this.currentFilters.page * this.currentFilters.limit, total)} of ${total} audit records</div>
      <div class="flex gap-1">
        <button class="btn btn-secondary text-xs py-1 px-2" ${this.currentFilters.page <= 1 ? 'disabled' : ''} onclick="AuditModule.changePage(${this.currentFilters.page - 1})">Prev</button>
        <span class="px-2 py-1 font-semibold text-slate-700">Page ${this.currentFilters.page} of ${totalPages}</span>
        <button class="btn btn-secondary text-xs py-1 px-2" ${this.currentFilters.page >= totalPages ? 'disabled' : ''} onclick="AuditModule.changePage(${this.currentFilters.page + 1})">Next</button>
      </div>
    `;
  },

  changePage(newPage) {
    this.currentFilters.page = newPage;
    this.loadAuditLogs();
  },

  async viewDetails(logId) {
    const res = await ApiService.getAuditLogs({ limit: 1000 });
    const log = (res.items || []).find(l => String(l.id) === String(logId));
    if (!log) {
      App.toast('Log entry not found', 'error');
      return;
    }

    let payloadFormatted = 'No extra payload data';
    if (log.payload) {
      payloadFormatted = typeof log.payload === 'string' ? log.payload : JSON.stringify(log.payload, null, 2);
    }

    App.showModal('Audit Record Inspection', `
      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-4 text-xs bg-slate-50 p-4 rounded border border-slate-200">
          <div><span class="text-slate-500">Record ID:</span> <span class="font-mono font-bold">${log.id}</span></div>
          <div><span class="text-slate-500">Timestamp:</span> <span class="font-mono">${log.timestamp}</span></div>
          <div><span class="text-slate-500">Action:</span> <span class="font-bold text-navy-900">${log.action}</span></div>
          <div><span class="text-slate-500">Actor:</span> <span>${log.actor}</span></div>
          <div><span class="text-slate-500">Entity:</span> <span class="font-semibold">${log.entity_type} (${log.entity_id})</span></div>
          <div><span class="text-slate-500">Client Host:</span> <span class="font-mono">${log.ip_address || '127.0.0.1'}</span></div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 mb-1">State Transition / Payload Diff</label>
          <pre class="bg-slate-900 text-emerald-400 p-4 rounded font-mono text-xs overflow-x-auto max-h-64">${payloadFormatted}</pre>
        </div>
      </div>
    `, [
      { label: 'Close', class: 'btn-secondary', onclick: 'App.closeModal()' }
    ]);
  },

  async exportCsv() {
    const res = await ApiService.getAuditLogs({ limit: 5000 });
    const logs = res.items || [];
    if (logs.length === 0) {
      App.toast('No audit records to export', 'warning');
      return;
    }
    const exportRows = logs.map(l => ({
      id: l.id,
      timestamp: l.timestamp,
      action: l.action,
      entity_type: l.entity_type,
      entity_id: l.entity_id,
      actor: l.actor,
      ip_address: l.ip_address || '127.0.0.1',
      payload: typeof l.payload === 'object' ? JSON.stringify(l.payload) : (l.payload || '')
    }));
    CsvUtil.downloadCsv(exportRows, 'aicte_audit_trail_export.csv');
    App.toast(`Exported ${exportRows.length} audit logs`, 'success');
  }
};

window.AuditModule = AuditModule;
