/**
 * AICTE ONE - Module 17: Administration, RBAC & Platform Settings
 * Multi-role simulator, dual-mode connectivity manager, system diagnostics, and data reset
 */
const SettingsModule = {
  roles: [
    { id: 'ADMIN', name: 'System Administrator', email: 'admin@aicte-india.org', bureau: 'Central Administration', perms: 'Full Administrative & Configuration Access' },
    { id: 'SCRUTINY_OFFICER', name: 'Scrutiny Officer', email: 'scrutiny.officer@aicte-india.org', bureau: 'Approval Bureau', perms: 'Application Scrutiny, Document Authentication, Deficiency Issuance' },
    { id: 'EVC_COORDINATOR', name: 'EVC Committee Coordinator', email: 'evc.coordinator@aicte-india.org', bureau: 'Approval Bureau', perms: 'Expert Visit Committee Scheduling, Inspection Reports, Pendency Management' },
    { id: 'COMPLIANCE_OFFICER', name: 'Regulatory Compliance Officer', email: 'compliance.officer@aicte-india.org', bureau: 'Policy & Academic Bureau', perms: 'Compliance Verification, FDR Tracking, Land/Fire NOC Review' },
    { id: 'VIGILANCE_OFFICER', name: 'Complaint & Vigilance Officer', email: 'vigilance.officer@aicte-india.org', bureau: 'Vigilance Bureau', perms: 'Complaint Registry, Cross-Bureau Coordination, Hearing Management' },
    { id: 'INSTITUTION_USER', name: 'Institutional Principal / Head', email: 'principal@gitm.ac.in', bureau: 'Institutional User', perms: 'View Own Institute Twin, Submit Applications & Compliance Evidence' }
  ],

  async render(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const currentRole = App.getCurrentRole();
    const isApiConnected = ApiService.isBackendConnected();

    container.innerHTML = `
      <div class="page-header flex justify-between items-center mb-6">
        <div>
          <h1 class="page-title text-2xl font-bold text-navy-900">Administration & System Settings</h1>
          <p class="text-sm text-slate-500">Role-based access control simulation, dual-mode operation toggles, and system maintenance</p>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- RBAC Role Simulation -->
        <div class="md:col-span-2 space-y-6">
          <div class="card p-6">
            <h3 class="text-lg font-bold text-navy-900 mb-2">Simulated User Persona (RBAC)</h3>
            <p class="text-xs text-slate-600 mb-4">
              Select an authorized persona below to switch administrative roles and experience how permissions, navigation, and workflows adapt.
            </p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              ${this.roles.map(r => `
                <div class="border rounded-lg p-4 cursor-pointer transition-all ${currentRole.id === r.id ? 'border-navy-900 bg-navy-50/50 ring-2 ring-navy-900' : 'border-slate-200 hover:border-slate-300 bg-white'}" onclick="SettingsModule.switchRole('${r.id}')">
                  <div class="flex items-center justify-between mb-1">
                    <span class="font-bold text-sm text-navy-900">${r.name}</span>
                    ${currentRole.id === r.id ? '<span class="badge badge-success text-[10px]">Active</span>' : ''}
                  </div>
                  <div class="text-xs text-slate-600 font-mono">${r.email}</div>
                  <div class="text-[11px] text-slate-500 mt-2 font-medium">${r.bureau}</div>
                  <div class="text-[10px] text-slate-400 mt-1">${r.perms}</div>
                </div>
              `).join('')}
            </div>
          </div>

          <!-- Dual-Mode Connectivity & Data Operations -->
          <div class="card p-6">
            <h3 class="text-lg font-bold text-navy-900 mb-2">Dual-Mode Storage & Connectivity</h3>
            <p class="text-xs text-slate-600 mb-4">
              AICTE ONE automatically synchronizes with the FastAPI backend when available, or runs 100% offline via browser-based reactive storage.
            </p>
            <div class="flex items-center justify-between p-4 rounded bg-slate-50 border border-slate-200 mb-4">
              <div class="flex items-center gap-3">
                <span class="w-3 h-3 rounded-full ${isApiConnected ? 'bg-emerald-500' : 'bg-amber-500'}"></span>
                <div>
                  <div class="font-bold text-sm text-navy-900">
                    ${isApiConnected ? 'Connected to FastAPI Backend (port 8000)' : 'Standalone Browser Mode (LocalStorage)'}
                  </div>
                  <div class="text-xs text-slate-500">
                    ${isApiConnected ? 'Relational SQLite/PostgreSQL storage with server-side rules engine' : 'Client-side reactive store with full offline capability'}
                  </div>
                </div>
              </div>
              <button class="btn btn-secondary text-xs" onclick="SettingsModule.testBackendConnection()">
                Test Connection
              </button>
            </div>

            <div class="border-t border-slate-200 pt-4 flex items-center justify-between">
              <div>
                <div class="text-sm font-semibold text-red-700">Restore Factory Seed Dataset</div>
                <div class="text-xs text-slate-500">Resets local client storage and repopulates demo institutions, applications & complaints</div>
              </div>
              <button class="btn btn-danger text-xs" onclick="SettingsModule.resetData()">
                Reset Data Store
              </button>
            </div>
          </div>
        </div>

        <!-- System Diagnostics Sidebar -->
        <div class="space-y-6">
          <div class="card p-6 bg-navy-900 text-white">
            <h3 class="text-base font-bold mb-3 flex items-center gap-2">
              <svg class="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
              Platform Diagnostics
            </h3>
            <div class="space-y-3 text-xs">
              <div class="flex justify-between border-b border-navy-800 pb-2">
                <span class="text-slate-400">Release Version</span>
                <span class="font-mono text-emerald-300">v2.4.0-prod</span>
              </div>
              <div class="flex justify-between border-b border-navy-800 pb-2">
                <span class="text-slate-400">Regulatory Framework</span>
                <span class="text-slate-200">AICTE APH 2024-27</span>
              </div>
              <div class="flex justify-between border-b border-navy-800 pb-2">
                <span class="text-slate-400">AI Engine</span>
                <span class="text-slate-200">Gemini 2.5 + Heuristic Rules</span>
              </div>
              <div class="flex justify-between border-b border-navy-800 pb-2">
                <span class="text-slate-400">OCR & SHA-256 Engine</span>
                <span class="text-emerald-300">Active</span>
              </div>
              <div class="flex justify-between border-b border-navy-800 pb-2">
                <span class="text-slate-400">Overlap Detector</span>
                <span class="text-emerald-300">Active (Threshold 60)</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-400">Audit Trail Integrity</span>
                <span class="text-emerald-300">Append-Only / Verified</span>
              </div>
            </div>
          </div>

          <div class="card p-6">
            <h4 class="text-sm font-bold text-navy-900 mb-2">Display & Accessibility</h4>
            <div class="space-y-3">
              <div>
                <label class="block text-xs font-semibold text-slate-600 mb-1">Color Palette</label>
                <select class="select text-xs w-full" onchange="SettingsModule.changeTheme(this.value)">
                  <option value="default">Government Classic (Navy & Slate)</option>
                  <option value="high-contrast">High Contrast (Accessibility Mode)</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-600 mb-1">Date Format Display</label>
                <div class="text-xs font-mono text-slate-700 bg-slate-50 p-2 rounded border border-slate-200">
                  DD-MMM-YYYY (e.g. 21-Oct-2024)
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  },

  switchRole(roleId) {
    const role = this.roles.find(r => r.id === roleId);
    if (!role) return;
    App.setCurrentRole(role);
    App.toast(`Switched persona to: ${role.name}`, 'info');
    this.render('main-content');
  },

  async testBackendConnection() {
    const connected = await ApiService.checkBackendHealth();
    if (connected) {
      App.toast('Successfully connected to AICTE ONE FastAPI backend server!', 'success');
    } else {
      App.toast('FastAPI server offline or unreachable. Platform operating in browser mode.', 'warning');
    }
    this.render('main-content');
  },

  resetData() {
    if (confirm('Are you sure you want to restore the factory seed database? All local mock adjustments will be reset.')) {
      DataStore.resetToDefaults();
      App.toast('Local database restored to factory seed state', 'success');
      setTimeout(() => window.location.reload(), 1000);
    }
  },

  changeTheme(theme) {
    if (theme === 'high-contrast') {
      document.body.classList.add('high-contrast');
      App.toast('High contrast accessibility mode activated', 'info');
    } else {
      document.body.classList.remove('high-contrast');
      App.toast('Standard government palette activated', 'info');
    }
  }
};

window.SettingsModule = SettingsModule;
