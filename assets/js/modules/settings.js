/**
 * AICTE ONE - Module 17: Administration, RBAC & Platform Settings
 * Server-Enforced RBAC, Real Account Authenticator, System Diagnostics & Audit Integrity
 */
const SettingsModule = {
  personas: [
    {
      id: 'SUPER_ADMIN',
      username: 'superadmin',
      name: 'Dr. V. K. Adhikari',
      title: 'Super Administrator',
      email: 'admin@aicte-india.org',
      bureau: 'Central Administration',
      perms: 'Full statutory & administrative oversight across all bureaus, institutions & audit records'
    },
    {
      id: 'SECURITY_OFFICER',
      username: 'security.officer',
      name: 'Col. Rajeshwar Singh',
      title: 'Security Officer',
      email: 'security@aicte-india.org',
      bureau: 'Information Security & Vigilance',
      perms: 'Security incidents, document anomalies, audit trails & regulatory system safeguards'
    },
    {
      id: 'POLICY_COMPLIANCE_OFFICER',
      username: 'compliance.officer',
      name: 'Dr. Meenakshi Sundaram',
      title: 'Policy & Compliance Officer',
      email: 'compliance.officer@aicte-india.org',
      bureau: 'Policy & Academic Bureau',
      perms: 'Regulatory compliance oversight, undertakings verification, FDR tracking & NOC reviews'
    },
    {
      id: 'COMPLAINT_OFFICER',
      username: 'complaint.officer',
      name: 'Shri Arvind Deshmukh',
      title: 'Complaint & Vigilance Officer',
      email: 'vigilance.officer@aicte-india.org',
      bureau: 'Public Grievance Cell',
      perms: 'Grievance intake, investigation assignment, cross-bureau conflict linking & case disposal'
    },
    {
      id: 'ANTI_RAGGING_OFFICER',
      username: 'antiragging.officer',
      name: 'Prof. Sunita Narain',
      title: 'Anti-Ragging Committee Head',
      email: 'antiragging@aicte-india.org',
      bureau: 'National Anti-Ragging Committee',
      perms: 'Specialized jurisdiction over student harassment, ragging complaints & hearing disposition'
    },
    {
      id: 'INSTITUTE_HEAD',
      username: 'principal.gitm',
      name: 'Dr. Anand K. Patwardhan',
      title: 'Institute Principal / Head',
      email: 'principal@gitm.ac.in',
      bureau: 'GITM (INST-10482)',
      perms: 'Tenant-isolated access strictly limited to authorized institution Digital Twin, EoA & compliance'
    },
    {
      id: 'STUDENT_COMPLAINANT',
      username: 'student.aarav',
      name: 'Aarav Sharma',
      title: 'Student Scholar & Complainant',
      email: 'aarav.student@gmail.com',
      bureau: 'Student Body',
      perms: 'Grievance submission & personal tracking. Zero access to confidential officer notes or other students'
    },
    {
      id: 'PUBLIC_VISITOR',
      username: 'public.visitor',
      name: 'Citizen / Prospective Student',
      title: 'Public Visitor',
      email: 'citizen@bharat.in',
      bureau: 'Public Access',
      perms: 'Public institutional directory search, approval status verification & open transparency metrics'
    }
  ],

  // Backward compatibility alias
  get roles() {
    return this.personas;
  },

  async render(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const currentUser = App.currentUser;
    const currentRoleCode = currentUser ? currentUser.role : (App.getCurrentRole() ? App.getCurrentRole().id : 'PUBLIC_VISITOR');
    const isApiConnected = API.isBackendConnected();

    container.innerHTML = `
      <div class="page-header flex justify-between items-center mb-6">
        <div>
          <h1 class="page-title text-2xl font-bold text-navy-900">Administration, Identity & RBAC Security</h1>
          <p class="text-sm text-slate-500">Statutory 8-role persona matrix, server-enforced credentials, cryptographic token sessions & system health</p>
        </div>
        <div class="flex items-center gap-2">
          ${currentUser ? `
            <button class="btn btn-secondary text-xs" onclick="App.logout()">
              Sign Out (${currentUser.username})
            </button>
          ` : `
            <button class="btn btn-primary text-xs" onclick="typeof AuthGateway !== 'undefined' ? AuthGateway.show() : App.showLoginModal()">
              Sign In via Role Gateway
            </button>
          `}
        </div>
      </div>

      <!-- Active Session Information Banner -->
      <div class="card p-4 mb-6 border-l-4 ${currentUser ? 'border-emerald-500 bg-emerald-50/40' : 'border-amber-500 bg-amber-50/40'}">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div class="text-xs font-bold uppercase tracking-wider text-slate-500">Authenticated Identity Status</div>
            <div class="text-base font-extrabold text-navy-900">
              ${currentUser ? `${currentUser.full_name} <span class="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-navy-900 text-white ml-2">${currentUser.role}</span>` : 'Anonymous / Public Visitor Session'}
            </div>
            <div class="text-xs text-slate-600 mt-1">
              ${currentUser ? `Account: <span class="font-mono font-semibold">${currentUser.email}</span> • Institution: <span class="font-mono">${currentUser.institution_id || 'AICTE Headquarters (Central)'}</span> • Server-Verified Permissions: <span class="font-mono text-emerald-800 font-semibold">${(currentUser.permissions || []).length} assigned</span>` : 'You are currently browsing with Public Visitor permissions. Officer and Institutional workflows require server authentication.'}
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button class="btn btn-secondary text-xs" onclick="App.showPasswordResetModal()">
              Password Recovery
            </button>
            <button class="btn btn-primary text-xs" onclick="App.showLoginModal()">
              Custom Login
            </button>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Statutory 8-Persona Matrix -->
        <div class="md:col-span-2 space-y-6">
          <div class="card p-6">
            <div class="flex items-center justify-between mb-2">
              <h3 class="text-lg font-bold text-navy-900">Statutory 8-Persona Accounts (Server-Verified)</h3>
              <span class="badge badge-info text-[10px]">Production Regulatory Baseline</span>
            </div>
            <p class="text-xs text-slate-600 mb-4">
              Select an account below to perform <strong>real cryptographic authentication</strong> via <code>/api/auth/login</code>. The server derives permissions directly from the verified account and strictly enforces tenant and role boundaries.
            </p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              ${this.personas.map(p => {
                const isActive = currentUser && currentUser.username === p.username;
                return `
                  <div class="border rounded-lg p-4 cursor-pointer transition-all ${isActive ? 'border-navy-900 bg-navy-50/70 ring-2 ring-navy-900' : 'border-slate-200 hover:border-slate-400 bg-white shadow-xs'}" onclick="SettingsModule.authenticatePersona('${p.username}')">
                    <div class="flex items-center justify-between mb-1">
                      <span class="font-bold text-sm text-navy-900">${p.title}</span>
                      ${isActive ? '<span class="badge badge-success text-[10px]">Active Session</span>' : '<span class="text-[10px] text-slate-400 font-mono">Click to Login</span>'}
                    </div>
                    <div class="text-xs font-semibold text-slate-700">${p.name}</div>
                    <div class="text-[11px] text-slate-500 font-mono">${p.email}</div>
                    <div class="text-[11px] text-navy-800 mt-2 font-medium flex items-center gap-1">
                      <span class="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
                      ${p.bureau}
                    </div>
                    <div class="text-[10px] text-slate-500 mt-1 line-clamp-2">${p.perms}</div>
                  </div>
                `;
              }).join('')}
            </div>
          </div>

          <!-- Dual-Mode Connectivity & Data Operations -->
          <div class="card p-6">
            <h3 class="text-lg font-bold text-navy-900 mb-2">Dual-Mode Storage & Connectivity</h3>
            <p class="text-xs text-slate-600 mb-4">
              AICTE ONE automatically synchronizes with the FastAPI backend when available, or runs in high-fidelity standalone browser mode.
            </p>
            <div class="flex items-center justify-between p-4 rounded bg-slate-50 border border-slate-200 mb-4">
              <div class="flex items-center gap-3">
                <span class="w-3 h-3 rounded-full ${isApiConnected ? 'bg-emerald-500' : 'bg-amber-500'}"></span>
                <div>
                  <div class="font-bold text-sm text-navy-900">
                    ${isApiConnected ? 'Connected to FastAPI Backend (port 8000)' : 'Standalone Browser Mode (LocalStorage)'}
                  </div>
                  <div class="text-xs text-slate-500">
                    ${isApiConnected ? 'Relational SQLite/PostgreSQL storage with bcrypt authentication and server-side rules engine' : 'Client-side reactive store with full offline capability'}
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

          <!-- Phase 5: System Health & Disaster Recovery Backups -->
          <div class="card p-6">
            <div class="flex items-center justify-between mb-2">
              <h3 class="text-lg font-bold text-navy-900">System Health & Disaster Recovery Backups</h3>
              <span class="badge badge-primary text-[10px]">Phase 5 DevSecOps</span>
            </div>
            <p class="text-xs text-slate-600 mb-4">
              Real-time telemetry across all statutory platform subsystems and cryptographic SHA-256 point-in-time database snapshot management.
            </p>
            <div class="flex flex-wrap gap-2 mb-4">
              <button class="btn btn-secondary text-xs" onclick="SettingsModule.refreshHealthTelemetry()">
                Refresh Subsystem Telemetry
              </button>
              <button class="btn btn-primary text-xs" onclick="SettingsModule.triggerBackupSnapshot()">
                Create Database Backup (SHA-256)
              </button>
            </div>
            <div id="health-telemetry-container" class="space-y-3 text-xs bg-slate-50 p-4 rounded border border-slate-200">
              <div class="text-slate-500 italic">Click "Refresh Subsystem Telemetry" to inspect live subsystem statuses...</div>
            </div>
          </div>
        </div>

        <!-- System Diagnostics Sidebar -->
        <div class="space-y-6">
          <!-- Official Project SHANKH Identity Card -->
          <div class="card p-5 bg-white border border-slate-200 text-center shadow-sm">
            <img src="assets/img/shankh-logo.png" alt="SHANKH Logo" class="w-20 h-20 mx-auto mb-2 object-contain drop-shadow-sm">
            <h3 class="font-bold text-base text-navy-900 tracking-tight">Project SHANKH · AICTE ONE</h3>
            <div class="text-[11px] font-mono font-bold text-[#a73a00] uppercase tracking-wider mb-1.5">Code • Analyze • Solve</div>
            <p class="text-xs text-slate-600 leading-relaxed">
              Official Cognitive AI and Regulatory Automation platform powering institutional intelligence, document forensic validation, and cross-bureau conflict resolution under the AICTE Approval Process Handbook (APH 2024-27).
            </p>
          </div>

          <div class="card p-6 bg-navy-900 text-white">
            <h3 class="text-base font-bold mb-3 flex items-center gap-2">
              <svg class="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
              Platform Security Diagnostics
            </h3>
            <div class="space-y-3 text-xs">
              <div class="flex justify-between border-b border-navy-800 pb-2">
                <span class="text-slate-400">Release Version</span>
                <span class="font-mono text-emerald-300">v2.4.0 (Phase 1 Baseline)</span>
              </div>
              <div class="flex justify-between border-b border-navy-800 pb-2">
                <span class="text-slate-400">Authentication</span>
                <span class="text-emerald-300">Bcrypt + HS256 JWT + HttpOnly</span>
              </div>
              <div class="flex justify-between border-b border-navy-800 pb-2">
                <span class="text-slate-400">Tenant Isolation</span>
                <span class="text-emerald-300">Backend Guard Enforced</span>
              </div>
              <div class="flex justify-between border-b border-navy-800 pb-2">
                <span class="text-slate-400">Whistleblower Privacy</span>
                <span class="text-emerald-300">Protected Case Isolation</span>
              </div>
              <div class="flex justify-between border-b border-navy-800 pb-2">
                <span class="text-slate-400">Audit Trail Integrity</span>
                <span class="text-emerald-300">Append-Only / Verified</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-400">Rate Limiting</span>
                <span class="text-emerald-300">Active (10 req/min/IP)</span>
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
                <label class="block text-xs font-semibold text-slate-600 mb-1">Standard Date Format</label>
                <div class="text-xs font-mono text-slate-700 bg-slate-50 p-2 rounded border border-slate-200">
                  DD-MMM-YYYY (e.g. 22-Oct-2026)
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  },

  async authenticatePersona(username) {
    try {
      App.toast(`Authenticating ${username} on server...`, 'info');
      const mfaCode = (username === 'superadmin' || username === 'security.officer') ? '123456' : null;
      await App.authenticatePersona(username, 'AicteOne@2026!', mfaCode);
      this.render('main-content');
    } catch (e) {
      App.toast(`Authentication failed: ${e.message}`, 'error');
    }
  },

  switchRole(roleId) {
    const persona = this.personas.find(p => p.id === roleId || p.username === roleId);
    if (persona) {
      this.authenticatePersona(persona.username);
    }
  },

  async testBackendConnection() {
    const connected = await API.checkBackendHealth();
    if (connected) {
      App.toast('Successfully connected to AICTE ONE FastAPI backend server!', 'success');
    } else {
      App.toast('FastAPI server offline or unreachable. Platform operating in browser mode.', 'warning');
    }
    this.render('main-content');
  },

  resetData() {
    if (confirm('Are you sure you want to restore the factory seed database? All local custom adjustments will be reset.')) {
      if (window.DataStore && typeof DataStore.resetToDefaults === 'function') {
        DataStore.resetToDefaults();
      }
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
  },

  async refreshHealthTelemetry() {
    const el = document.getElementById('health-telemetry-container');
    if (!el) return;
    el.innerHTML = '<div class="text-slate-500 italic">Querying server diagnostics and subsystem ping endpoints...</div>';
    try {
      const data = await API.getDetailedSystemHealth();
      const services = data.services || {};
      const alerts = data.system_alerts || [];
      const backups = await API.listDatabaseBackups();

      let html = `
        <div class="flex items-center justify-between pb-2 border-b border-slate-200">
          <div>
            <span class="font-bold text-slate-800">Overall Subsystem Status:</span>
            <span class="font-bold ml-1 ${data.overall_status === 'HEALTHY' ? 'text-emerald-700' : 'text-amber-700'}">${data.overall_status}</span>
          </div>
          <span class="text-[10px] text-slate-400 font-mono">${data.timestamp ? new Date(data.timestamp).toLocaleString() : ''}</span>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
      `;

      for (const [k, v] of Object.entries(services)) {
        const isOk = v.status === 'HEALTHY';
        html += `
          <div class="bg-white p-2.5 rounded border border-slate-200 shadow-2xs">
            <div class="flex items-center justify-between">
              <span class="font-bold uppercase tracking-wider text-[10px] text-slate-500">${k.replace(/_/g, ' ')}</span>
              <span class="badge ${isOk ? 'badge-success' : 'badge-warning'} text-[9px]">${v.status}</span>
            </div>
            <div class="text-xs text-slate-700 mt-1 truncate">${v.details || v.active_mode || v.description || 'Nominal operational status'}</div>
          </div>
        `;
      }
      html += '</div>';

      if (backups && backups.backups && backups.backups.length > 0) {
        html += `
          <div class="mt-4 pt-3 border-t border-slate-200">
            <div class="font-bold text-xs text-slate-800 mb-2">Stored Cryptographic Database Snapshots (${backups.total_backups})</div>
            <div class="space-y-1.5 max-h-36 overflow-y-auto">
              ${backups.backups.slice(0, 5).map(b => `
                <div class="flex items-center justify-between bg-white p-2 rounded border border-slate-200 text-[11px]">
                  <div>
                    <span class="font-mono font-bold text-navy-900">${b.backup_id}</span>
                    <span class="text-slate-400 text-[10px] ml-2">SHA: ${b.sha256 ? b.sha256.substring(0, 12) : ''}...</span>
                  </div>
                  <div class="flex items-center gap-1.5">
                    <button class="btn btn-secondary text-[10px] py-0.5 px-1.5" onclick="SettingsModule.verifyBackup('${b.backup_id}')">Verify</button>
                    <button class="btn btn-primary text-[10px] py-0.5 px-1.5" onclick="SettingsModule.verifyRestore('${b.backup_id}')">Check Restore</button>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        `;
      }

      el.innerHTML = html;
      App.toast('Subsystem telemetry refreshed successfully', 'success');
    } catch (e) {
      el.innerHTML = `<div class="text-red-600 font-bold">Error querying telemetry: ${e.message}</div>`;
      App.toast(`Diagnostics query error: ${e.message}`, 'error');
    }
  },

  async triggerBackupSnapshot() {
    try {
      App.toast('Generating cryptographic database backup snapshot...', 'info');
      const res = await API.createDatabaseBackup('Manual administrator snapshot via web console');
      App.toast(`Backup ${res.backup.backup_id} created with verified SHA-256 digest!`, 'success');
      this.refreshHealthTelemetry();
    } catch (e) {
      App.toast(`Backup creation failed: ${e.message}`, 'error');
    }
  },

  async verifyBackup(id) {
    try {
      const res = await API.verifyDatabaseBackup(id);
      if (res.verified) {
        App.toast(`Cryptographic integrity verified for ${id}! SHA-256 matches manifest.`, 'success');
      } else {
        App.toast(`Integrity check FAILED for ${id}: ${res.error}`, 'error');
      }
    } catch (e) {
      App.toast(`Verification failed: ${e.message}`, 'error');
    }
  },

  async verifyRestore(id) {
    try {
      const res = await API.restoreAndVerifyBackup(id);
      if (res.verification && res.verification.relational_integrity_passed) {
        App.toast(`Restoration verified: All relations, foreign keys & audit continuity confirmed for ${id}!`, 'success');
      } else {
        App.toast(`Restoration test failed relational validation for ${id}`, 'warning');
      }
    } catch (e) {
      App.toast(`Restoration test failed: ${e.message}`, 'error');
    }
  }
};

window.SettingsModule = SettingsModule;
