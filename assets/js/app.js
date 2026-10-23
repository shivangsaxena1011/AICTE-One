/**
 * AICTE ONE - Master Application Controller
 * Router, Event Bus, Modal System, Toast Notifications, Role Switcher & Module Dispatcher
 */
const App = {
  currentRoute: 'overview',
  currentParam: null,
  currentRole: null,

  modules: {
    'overview': () => (window.OverviewModule || OverviewModule),
    'executive-intelligence': () => (window.OverviewModule || OverviewModule),
    'institutions': () => (window.InstitutionsModule || InstitutionsModule),
    'digitalTwin': () => (window.DigitalTwinModule || DigitalTwinModule),
    'digital-twin': () => (window.DigitalTwinModule || DigitalTwinModule),
    'digital_twin': () => (window.DigitalTwinModule || DigitalTwinModule),
    'institution-digital-twin': () => (window.DigitalTwinModule || DigitalTwinModule),
    'applications': () => (window.ApplicationsModule || ApplicationsModule),
    'scrutiny': () => (window.ScrutinyModule || ScrutinyModule),
    'approval-and-scrutiny-workflow': () => (window.ScrutinyModule || ScrutinyModule),
    'evc': () => (window.EvcModule || window.EVCModule || EVCModule),
    'verification': () => (window.VerificationModule || VerificationModule),
    'intelligent-document-verification': () => (window.VerificationModule || VerificationModule),
    'compliance': () => (window.ComplianceModule || ComplianceModule),
    'compliance-and-undertakings': () => (window.ComplianceModule || ComplianceModule),
    'complaints': () => (window.ComplaintsModule || ComplaintsModule),
    'complaint-intelligence': () => (window.ComplaintsModule || ComplaintsModule),
    'coordination': () => (window.CoordinationModule || CoordinationModule),
    'tasks': () => (window.TasksModule || TasksModule),
    'graph': () => (window.GraphModule || GraphModule),
    'copilot': () => (window.CopilotModule || CopilotModule),
    'reports': () => (window.ReportsModule || ReportsModule),
    'notifications': () => (window.NotificationsModule || NotificationsModule),
    'audit': () => (window.AuditModule || AuditModule),
    'settings': () => (window.SettingsModule || SettingsModule)
  },

  currentUser: null,

  async init() {
    await API.checkBackendHealth();
    if (typeof AuthGateway !== 'undefined') {
      AuthGateway.init();
    }
    await this.initRole();
    this.setupNavigation();
    this.setupGlobalSearch();
    this.setupModals();
    this.updateBackendStatusIndicator();
    this.updateNotificationBadge();

    // Check URL hash for initial route
    const hash = window.location.hash.replace(/^#\/?/, '');
    if (hash) {
      const parts = hash.split('/');
      const route = parts[0];
      const param = parts.slice(1).join('/') || null;
      this.navigate(route || 'overview', param || null, false);
    } else {
      this.navigate('overview', null, false);
    }

    window.addEventListener('hashchange', () => {
      const currentHash = window.location.hash.replace(/^#\/?/, '');
      const parts = currentHash.split('/');
      const route = parts[0];
      const param = parts.slice(1).join('/') || null;
      if (route && (route !== this.currentRoute || param !== this.currentParam)) {
        this.navigate(route, param || null, false);
      }
    });

    console.log('AICTE ONE Platform initialized with individual authentication and RBAC.');
  },

  async initRole() {
    if (API.isBackendConnected()) {
      const user = await API.getCurrentUser();
      if (user) {
        this.currentUser = user;
        this.currentRole = {
          id: user.role,
          name: user.full_name,
          email: user.email,
          bureau: user.department || user.role,
          perms: (user.permissions || []).join(', ')
        };
      } else {
        // Fallback: check saved persona or default to Public Visitor
        this.currentUser = null;
        this.currentRole = {
          id: 'PUBLIC_VISITOR',
          name: 'Public Visitor',
          email: 'citizen@bharat.in',
          bureau: 'Public Access',
          perms: 'Public institutional directory & approval verification'
        };
      }
    } else {
      const saved = localStorage.getItem('aicte_current_role');
      if (saved) {
        try {
          this.currentRole = JSON.parse(saved);
        } catch (e) {
          this.currentRole = null;
        }
      }
      if (!this.currentRole) {
        // Default strictly to Public Visitor, never auto-assign Admin
        this.currentRole = {
          id: 'PUBLIC_VISITOR',
          name: 'Public Visitor',
          email: 'citizen@bharat.in',
          bureau: 'Public Access',
          perms: 'Public Directory & Search'
        };
      }
    }
    this.updateRoleDisplay();
  },

  getCurrentRole() {
    if (this.currentUser) {
      return {
        id: this.currentUser.role,
        name: this.currentUser.full_name,
        email: this.currentUser.email,
        bureau: this.currentUser.department || this.currentUser.role,
        perms: (this.currentUser.permissions || []).join(', ')
      };
    }
    return this.currentRole || {
      id: 'PUBLIC_VISITOR',
      name: 'Public Visitor',
      email: 'citizen@bharat.in',
      bureau: 'Public Access',
      perms: 'Public Directory & Search'
    };
  },

  setCurrentRole(role) {
    this.currentRole = role;
    localStorage.setItem('aicte_current_role', JSON.stringify(role));
    this.updateRoleDisplay();
  },

  updateRoleDisplay() {
    const el = document.getElementById('header-role-name');
    const emailEl = document.getElementById('header-role-email');
    const anchorEl = document.getElementById('header-context-anchor');
    const badgesEl = document.getElementById('header-context-badges');

    if (this.currentUser) {
      if (el) el.textContent = this.currentUser.full_name;
      if (emailEl) emailEl.innerHTML = `<span class="text-emerald-700 font-semibold">${this.currentUser.role}</span> • Sign Out`;

      if (anchorEl) {
        if (this.currentUser.role === 'INSTITUTE_HEAD') {
          anchorEl.innerHTML = `
            <span class="material-symbols-outlined text-[#a73a00] text-[16px] shrink-0">corporate_fare</span>
            <span class="font-semibold text-[#001332]">Bound Institution:</span>
            <span class="text-slate-700 font-medium truncate max-w-[220px]">Gurugram Institute of Technology & Management</span>
            <span class="font-mono text-slate-500 text-[10px] sm:text-[11px]">[PID: 1-10482931]</span>
          `;
        } else {
          anchorEl.innerHTML = `
            <span class="material-symbols-outlined text-[#a73a00] text-[16px] shrink-0">verified_user</span>
            <span class="font-semibold text-[#001332]">Statutory Jurisdiction:</span>
            <span class="text-slate-700 font-medium truncate max-w-[220px]">${this.currentUser.department || 'Central Governance Bureau'}</span>
            <span class="font-mono text-slate-500 text-[10px] sm:text-[11px]">[Active Session 2026–27]</span>
          `;
        }
      }
      if (badgesEl) {
        badgesEl.innerHTML = `
          <span class="px-1.5 sm:px-2 py-0.5 rounded bg-[#002f1e] text-[#23a274] font-semibold text-[9px] sm:text-[10px] flex items-center gap-1">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            Authenticated Session
          </span>
          <span class="px-1.5 sm:px-2 py-0.5 rounded bg-[#eaedff] text-[#001332] font-semibold text-[10px] border border-[#dae2fd]">Role: ${this.currentUser.role}</span>
          <span class="px-1.5 sm:px-2 py-0.5 rounded bg-white text-[#a73a00] font-mono text-[9px] sm:text-[10px] font-bold border border-slate-200">Audit Active</span>
        `;
      }
    } else if (this.currentRole) {
      if (el) el.textContent = this.currentRole.name;
      if (emailEl) emailEl.innerHTML = `<span class="text-slate-500">${this.currentRole.bureau || 'Public'}</span> • <span class="text-primary font-bold">Sign In</span>`;
      if (anchorEl) {
        anchorEl.innerHTML = `
          <span class="material-symbols-outlined text-[#a73a00] text-[16px] shrink-0">corporate_fare</span>
          <span class="font-semibold text-[#001332]">Regulatory Grid:</span>
          <span class="text-slate-700 font-medium truncate max-w-[220px]">Academic Cycle 2026–27</span>
          <span class="font-mono text-slate-500 text-[10px] sm:text-[11px]">[8,842 Master Records]</span>
        `;
      }
    }
  },

  async authenticatePersona(username, password = 'AicteOne@2026!', mfaCode = null) {
    const data = await API.login(username, password, mfaCode);
    this.currentUser = data.user;
    this.currentRole = {
      id: data.user.role,
      name: data.user.full_name,
      email: data.user.email,
      bureau: data.user.department || data.user.role,
      perms: (data.user.permissions || []).join(', ')
    };
    this.updateRoleDisplay();
    this.closeModal();
    this.toast(`Authenticated as ${data.user.full_name} (${data.user.role})`, 'success');
    return data;
  },

  async logout() {
    await API.logout();
    this.currentUser = null;
    this.currentRole = {
      id: 'PUBLIC_VISITOR',
      name: 'Public Visitor',
      email: 'citizen@bharat.in',
      bureau: 'Public Access',
      perms: 'Public Directory & Search'
    };
    localStorage.removeItem('aicte_current_role');
    sessionStorage.removeItem('aicte_judge_demo');

    if (typeof AuthGateway !== 'undefined') {
      AuthGateway.isJudgeDemo = false;
      const banner = document.getElementById('judge-demo-banner');
      if (banner) banner.remove();
      AuthGateway.step = 1;
      AuthGateway.selectedRole = null;
      AuthGateway.show();
    }

    this.updateRoleDisplay();
    this.toast('Signed out successfully. Session invalidated.', 'info');
  },

  showLoginModal(targetRoute = null) {
    const bodyHtml = `
      <div class="space-y-4 text-xs">
        <div class="p-3 bg-navy-50 rounded-lg border border-navy-100 flex items-center justify-between">
          <div>
            <div class="font-bold text-navy-900">Official AICTE Single Sign-On</div>
            <div class="text-[11px] text-slate-500">Government of India • Ministry of Education</div>
          </div>
          <span class="badge badge-success text-[10px]">Bcrypt Secured</span>
        </div>

        <form id="app-login-form" onsubmit="event.preventDefault(); App.handleLoginFormSubmit('${targetRoute || ''}')" class="space-y-3">
          <div id="login-error-box" class="hidden p-2.5 rounded bg-red-50 border border-red-200 text-red-700 text-xs font-medium"></div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">Username or Registered Email *</label>
            <input type="text" id="login-input-username" class="input w-full text-xs" placeholder="e.g. superadmin, principal.gitm, or email" required />
          </div>

          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="block font-semibold text-slate-700">Password *</label>
              <a href="javascript:void(0)" class="text-primary hover:underline text-[11px]" onclick="App.showPasswordResetModal()">Forgot Password?</a>
            </div>
            <input type="password" id="login-input-password" class="input w-full text-xs" placeholder="Enter your individual password" required />
          </div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">MFA Verification Code (Optional / Privileged Accounts)</label>
            <input type="text" id="login-input-mfa" class="input w-full text-xs font-mono" placeholder="6-digit TOTP / demo PIN (e.g. 123456)" />
          </div>

          <div class="pt-2">
            <button type="submit" id="login-submit-btn" class="btn btn-primary w-full text-xs font-bold py-2 justify-center flex items-center gap-1.5">
              <span>Sign In to Platform</span>
            </button>
          </div>
        </form>

        <details class="border-t border-slate-200 pt-3 text-slate-500">
          <summary class="text-[11px] font-semibold text-slate-500 cursor-pointer hover:text-slate-700 select-none">
            Authorized Local Test Accounts (Dev / Audit Inspection)
          </summary>
          <div class="grid grid-cols-2 gap-2 mt-2">
            <button type="button" class="btn btn-secondary text-[11px] text-left p-2 justify-start truncate" onclick="App.fillDemoLogin('superadmin', 'AicteOne@2026!')">
              🛡️ Super Administrator
            </button>
            <button type="button" class="btn btn-secondary text-[11px] text-left p-2 justify-start truncate" onclick="App.fillDemoLogin('security.officer', 'AicteOne@2026!')">
              🔒 Security Officer
            </button>
            <button type="button" class="btn btn-secondary text-[11px] text-left p-2 justify-start truncate" onclick="App.fillDemoLogin('compliance.officer', 'AicteOne@2026!')">
              📋 Policy & Compliance
            </button>
            <button type="button" class="btn btn-secondary text-[11px] text-left p-2 justify-start truncate" onclick="App.fillDemoLogin('complaint.officer', 'AicteOne@2026!')">
              ⚖️ Complaint Officer
            </button>
            <button type="button" class="btn btn-secondary text-[11px] text-left p-2 justify-start truncate" onclick="App.fillDemoLogin('principal.gitm', 'AicteOne@2026!')">
              🏛️ Institute Head (GITM)
            </button>
            <button type="button" class="btn btn-secondary text-[11px] text-left p-2 justify-start truncate" onclick="App.fillDemoLogin('student.aarav', 'AicteOne@2026!')">
              🎓 Student Complainant
            </button>
          </div>
        </details>
      </div>
    `;

    this.openModal('Sign In to AICTE ONE', bodyHtml, `
      <button class="btn btn-secondary text-xs" onclick="App.closeModal()">Cancel</button>
    `);
  },

  fillDemoLogin(username, password) {
    const uInput = document.getElementById('login-input-username');
    const pInput = document.getElementById('login-input-password');
    const mInput = document.getElementById('login-input-mfa');
    if (uInput) uInput.value = username;
    if (pInput) pInput.value = password;
    if (mInput) {
      if (username === 'superadmin' || username === 'security.officer') {
        mInput.value = '123456';
      } else {
        mInput.value = '';
      }
    }
  },

  async handleLoginFormSubmit(targetRoute) {
    const uInput = document.getElementById('login-input-username');
    const pInput = document.getElementById('login-input-password');
    const mInput = document.getElementById('login-input-mfa');
    const errBox = document.getElementById('login-error-box');
    const submitBtn = document.getElementById('login-submit-btn');

    if (!uInput || !pInput) return;
    const username = uInput.value.trim();
    const password = pInput.value;
    const mfa = mInput ? mInput.value.trim() : null;

    if (errBox) errBox.classList.add('hidden');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span>Verifying credentials...</span>';
    }

    try {
      await this.authenticatePersona(username, password, mfa || null);
      if (targetRoute) {
        this.navigate(targetRoute);
      }
    } catch (err) {
      if (errBox) {
        let msg = err.message || 'Invalid username or password.';
        if (msg.toLowerCase().includes('mfa code required') || msg.toLowerCase().includes('mfa')) {
          msg = 'MFA code required for this privileged account. For audit/demo inspection, enter PIN: 123456';
          if (mInput) {
            mInput.focus();
            if (!mInput.value) mInput.value = '123456';
          }
        }
        errBox.textContent = msg;
        errBox.classList.remove('hidden');
      }
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span>Sign In to Platform</span>';
      }
    }
  },

  showPasswordResetModal() {
    const bodyHtml = `
      <div class="space-y-4 text-xs">
        <p class="text-slate-600">
          Enter your registered username or official email address to generate a single-use, time-limited password recovery link (valid for 15 minutes).
        </p>

        <form id="password-reset-request-form" onsubmit="event.preventDefault(); App.handleResetRequestSubmit()" class="space-y-3">
          <div id="reset-msg-box" class="hidden p-2.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-medium"></div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">Username or Email *</label>
            <input type="text" id="reset-account-input" class="input w-full text-xs" placeholder="e.g. principal.gitm or principal@gitm.ac.in" required />
          </div>

          <div id="reset-token-display-box" class="hidden p-3 bg-slate-50 border border-slate-200 rounded space-y-2">
            <div class="font-bold text-navy-900 text-xs">Password Reset Token Issued:</div>
            <div id="reset-token-value" class="p-2 bg-white border border-slate-300 font-mono text-xs break-all rounded"></div>
            <div class="pt-2">
              <label class="block font-semibold text-slate-700 mb-1">New Password (Min 8 Characters) *</label>
              <input type="password" id="reset-new-password" class="input w-full text-xs" placeholder="Enter new secure password" />
            </div>
            <button type="button" class="btn btn-primary w-full text-xs font-bold mt-2" onclick="App.handleConfirmPasswordReset()">
              Update Password
            </button>
          </div>

          <div id="reset-request-btn-box">
            <button type="submit" class="btn btn-primary w-full text-xs font-bold py-2">
              Generate Password Recovery Token
            </button>
          </div>
        </form>
      </div>
    `;

    this.openModal('Password Recovery', bodyHtml, `
      <button class="btn btn-secondary text-xs" onclick="App.showLoginModal()">Back to Sign In</button>
      <button class="btn btn-secondary text-xs" onclick="App.closeModal()">Close</button>
    `);
  },

  async handleResetRequestSubmit() {
    const input = document.getElementById('reset-account-input');
    const msgBox = document.getElementById('reset-msg-box');
    const tokenBox = document.getElementById('reset-token-display-box');
    const tokenVal = document.getElementById('reset-token-value');
    const btnBox = document.getElementById('reset-request-btn-box');

    if (!input) return;
    const account = input.value.trim();

    try {
      const res = await API.requestPasswordReset(account);
      if (msgBox) {
        msgBox.textContent = res.message;
        msgBox.classList.remove('hidden');
      }
      if (res.token && tokenBox && tokenVal) {
        tokenVal.textContent = res.token;
        tokenBox.classList.remove('hidden');
        if (btnBox) btnBox.classList.add('hidden');
      }
    } catch (e) {
      if (msgBox) {
        msgBox.textContent = e.message || 'Error requesting password reset.';
        msgBox.className = 'p-2.5 rounded bg-red-50 border border-red-200 text-red-700 text-xs font-medium';
        msgBox.classList.remove('hidden');
      }
    }
  },

  async handleConfirmPasswordReset() {
    const tokenVal = document.getElementById('reset-token-value');
    const newPassInput = document.getElementById('reset-new-password');
    const msgBox = document.getElementById('reset-msg-box');

    if (!tokenVal || !newPassInput) return;
    const token = tokenVal.textContent.trim();
    const newPassword = newPassInput.value;

    if (newPassword.length < 8) {
      alert('Password must be at least 8 characters long.');
      return;
    }

    try {
      const res = await API.confirmPasswordReset(token, newPassword);
      this.toast('Password updated successfully! Please log in.', 'success');
      this.showLoginModal();
    } catch (e) {
      if (msgBox) {
        msgBox.textContent = e.message || 'Error updating password.';
        msgBox.className = 'p-2.5 rounded bg-red-50 border border-red-200 text-red-700 text-xs font-medium';
        msgBox.classList.remove('hidden');
      }
    }
  },

  updateBackendStatusIndicator() {
    const pill = document.getElementById('backend-status-pill');
    if (!pill) return;
    const isLive = API.isBackendConnected();
    pill.className = `flex items-center gap-1 sm:gap-1.5 px-2 sm:px-2.5 py-1 rounded-full text-[10px] sm:text-[11px] font-semibold ${isLive ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-amber-50 text-amber-800 border border-amber-200'}`;
    pill.innerHTML = `
      <span class="w-2 h-2 rounded-full ${isLive ? 'bg-emerald-600' : 'bg-amber-600'} shrink-0"></span>
      <span class="hidden sm:inline">${isLive ? 'FastAPI Connected' : 'Browser Offline Mode'}</span>
      <span class="sm:hidden">${isLive ? 'API Live' : 'Offline'}</span>
    `;
  },

  setupNavigation() {
    document.querySelectorAll('[data-route]').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const route = link.getAttribute('data-route');
        const param = link.getAttribute('data-param') || null;
        this.navigate(route, param);
      });
    });
  },

  async navigate(route, param = null, updateHash = true) {
    if (!this.modules[route]) {
      console.warn(`Module '${route}' not found. Defaulting to overview.`);
      route = 'overview';
    }

    // Public vs Protected route check
    const publicRoutes = ['overview', 'executive-intelligence', 'institutions', 'digitalTwin', 'digital-twin', 'digital_twin', 'institution-digital-twin', 'reports', 'settings'];
    const isDemo = typeof AuthGateway !== 'undefined' && AuthGateway.isJudgeDemo;
    if (!this.currentUser && !isDemo && !publicRoutes.includes(route)) {
      this.toast('Authentication required to access officer or institutional workflow.', 'info');
      if (typeof AuthGateway !== 'undefined') {
        AuthGateway.show();
      } else {
        this.showLoginModal(route);
      }
      return;
    }

    this.currentRoute = route;
    this.currentParam = param;

    if (updateHash) {
      window.location.hash = param ? `#/${route}/${param}` : `#/${route}`;
    }

    // Update active nav styling
    document.querySelectorAll('.nav-item').forEach(item => {
      const itemRoute = item.getAttribute('data-route');
      if (itemRoute === route) {
        item.classList.add('nav-active');
      } else {
        item.classList.remove('nav-active');
      }
    });

    // Close mobile sidebar if open
    this.toggleSidebar(false);

    // Call destroy on previous module if it exists
    if (this._currentModuleInstance && typeof this._currentModuleInstance.destroy === 'function') {
      try { this._currentModuleInstance.destroy(); } catch (e) { console.warn(e); }
      this._currentModuleInstance = null;
    }

    // Render target module
    const moduleGetter = this.modules[route];
    if (moduleGetter) {
      const module = moduleGetter();
      if (module && typeof module.render === 'function') {
        this._currentModuleInstance = module;
        const contentContainer = document.getElementById('main-content');
        try {
          // If param is passed as string, also pass as { id: param } for modules expecting object
          const paramObj = (typeof param === 'string' && param.includes('=')) ?
            Object.fromEntries(new URLSearchParams(param)) :
            (typeof param === 'string' ? { id: param } : param || {});

          let res;
          // Route-aware parameter dispatching
          if (['audit', 'notifications', 'reports', 'settings'].includes(route)) {
            res = await module.render('main-content', paramObj);
          } else {
            res = await module.render(paramObj);
          }

          if (typeof res === 'string' && contentContainer) {
            contentContainer.innerHTML = res;
          }
          if (typeof module.postRender === 'function') {
            module.postRender(paramObj);
          }
        } catch (err) {
          console.error(`Error rendering module '${route}':`, err);
          if (contentContainer) {
            contentContainer.innerHTML = `
              <div class="card p-8 text-center text-red-600">
                <h3 class="font-bold text-lg">Error Rendering Module</h3>
                <p class="text-xs text-slate-500 mt-2">${escapeHtml(err.message || String(err))}</p>
                <button class="btn btn-secondary text-xs mt-4" onclick="App.navigate('overview')">Return to Overview</button>
              </div>
            `;
          }
        }
      }
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
  },

  refresh() {
    this.navigate(this.currentRoute, this.currentParam, false);
  },

  async updateNotificationBadge() {
    const badge = document.getElementById('notification-badge');
    if (!badge) return;
    try {
      const res = await API.getNotifications();
      const list = Array.isArray(res) ? res : (res.items || res.data || []);
      const unread = list.filter(n => !n.is_read).length;
      if (unread > 0) {
        badge.textContent = unread > 99 ? '99+' : unread;
        badge.classList.remove('hidden');
      } else {
        badge.classList.add('hidden');
      }
    } catch (e) {
      badge.classList.add('hidden');
    }
  },

  setupGlobalSearch() {
    const input = document.getElementById('global-search-input');
    const resultsBox = document.getElementById('global-search-results');
    if (!input || !resultsBox) return;

    let debounceTimer = null;
    input.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      const query = e.target.value.trim();
      if (query.length < 2) {
        resultsBox.classList.add('hidden');
        resultsBox.innerHTML = '';
        return;
      }

      debounceTimer = setTimeout(async () => {
        const instRes = await API.getInstitutions({ search: query, limit: 5 });
        const appRes = await API.getApplications({ search: query, limit: 5 });

        const institutions = instRes.items || instRes.data || (Array.isArray(instRes) ? instRes : []);
        const applications = appRes.items || appRes.data || (Array.isArray(appRes) ? appRes : []);

        if (institutions.length === 0 && applications.length === 0) {
          resultsBox.innerHTML = `<div class="p-3 text-xs text-slate-400">No matching institutions or applications found</div>`;
          resultsBox.classList.remove('hidden');
          return;
        }

        resultsBox.innerHTML = `
          ${institutions.length > 0 ? `
            <div class="p-2 border-b border-slate-100 bg-slate-50 text-[11px] font-bold text-slate-500 uppercase">Institutions</div>
            ${institutions.map(i => `
              <div class="p-2.5 hover:bg-slate-100 cursor-pointer flex justify-between items-center text-xs" onclick="App.selectSearchResult('digitalTwin', '${i.id}')">
                <div>
                  <div class="font-bold text-navy-900">${escapeHtml(i.name)}</div>
                  <div class="text-[11px] text-slate-500 font-mono">${escapeHtml(i.permanent_id)} &bull; ${escapeHtml(i.city || '')}, ${escapeHtml(i.state || '')}</div>
                </div>
                <span class="badge badge-neutral text-[10px]">${escapeHtml(i.category || '')}</span>
              </div>
            `).join('')}
          ` : ''}

          ${applications.length > 0 ? `
            <div class="p-2 border-b border-slate-100 bg-slate-50 text-[11px] font-bold text-slate-500 uppercase">Approval Applications</div>
            ${applications.map(a => `
              <div class="p-2.5 hover:bg-slate-100 cursor-pointer flex justify-between items-center text-xs" onclick="App.selectSearchResult('scrutiny', '${a.id || a.application_number}')">
                <div>
                  <div class="font-bold text-navy-900">${escapeHtml(a.id || a.application_number)}</div>
                  <div class="text-[11px] text-slate-500">${escapeHtml(a.institution_name)} &bull; ${escapeHtml(a.type)}</div>
                </div>
                <span class="badge badge-warning text-[10px]">${escapeHtml(a.status)}</span>
              </div>
            `).join('')}
          ` : ''}
        `;
        resultsBox.classList.remove('hidden');
      }, 250);
    });

    document.addEventListener('click', (e) => {
      if (!input.contains(e.target) && !resultsBox.contains(e.target)) {
        resultsBox.classList.add('hidden');
      }
    });
  },

  selectSearchResult(route, param) {
    const resultsBox = document.getElementById('global-search-results');
    const input = document.getElementById('global-search-input');
    if (resultsBox) resultsBox.classList.add('hidden');
    if (input) input.value = '';
    this.navigate(route, param);
  },

  setupModals() {
    const backdrop = document.getElementById('modal-backdrop');
    if (backdrop) {
      backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop) this.closeModal();
      });
    }
  },

  openModal(title, bodyHtml, footerHtml = "") {
    const backdrop = document.getElementById('modal-backdrop');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    const modalFooter = document.getElementById('modal-footer');
    if (!backdrop || !modalTitle || !modalBody || !modalFooter) return;

    modalTitle.textContent = title;
    modalBody.innerHTML = bodyHtml;
    modalFooter.innerHTML = footerHtml || `<button class="btn btn-secondary text-xs" onclick="App.closeModal()">Close</button>`;

    backdrop.classList.remove('hidden');
    backdrop.classList.add('flex');
  },

  showModal(title, bodyHtml, buttons = []) {
    let footerHtml = "";
    if (typeof buttons === "string") {
      footerHtml = buttons;
    } else if (Array.isArray(buttons)) {
      footerHtml = buttons.map(btn => `
        <button class="btn ${btn.class || 'btn-secondary'} text-xs font-semibold" onclick="${btn.onclick}">
          ${btn.label}
        </button>
      `).join('');
    }
    this.openModal(title, bodyHtml, footerHtml);
  },

  closeModal() {
    const backdrop = document.getElementById('modal-backdrop');
    if (backdrop) {
      backdrop.classList.add('hidden');
      backdrop.classList.remove('flex');
    }
  },

  openCreateModal(type, prefillId = null) {
    const instOptions = localStore.db.institutions.map(i =>
      `<option value="${i.id}" ${prefillId === i.id || prefillId === i.permanent_id ? 'selected' : ''}>${escapeHtml(i.name)} (${i.permanent_id})</option>`
    ).join('');

    if (type === 'application') {
      this.openModal('Lodgement New Approval Application', `
        <form id="create-app-form" class="space-y-4 text-xs">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Target Institution *</label>
            <select id="modal-app-inst" class="select w-full text-xs" required>${instOptions}</select>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Application Type *</label>
              <select id="modal-app-type" class="select w-full text-xs">
                <option value="Extension of Approval (EoA)">Extension of Approval (EoA)</option>
                <option value="Increase in Intake / Additional Course">Increase in Intake / Additional Course</option>
                <option value="Establishment of New Technical Institution">Establishment of New Technical Institution</option>
                <option value="Introduction of Supernumerary Seats">Introduction of Supernumerary Seats</option>
                <option value="Closure of Course / Institution">Closure of Course / Institution</option>
              </select>
            </div>
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Academic Year</label>
              <input type="text" id="modal-app-year" class="input w-full text-xs" value="2026-2027" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Assigned Scrutiny Officer</label>
              <input type="text" id="modal-app-owner" class="input w-full text-xs" value="R. Sharma" />
            </div>
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Statutory Due Date</label>
              <input type="date" id="modal-app-due" class="input w-full text-xs" value="2026-11-15" />
            </div>
          </div>
        </form>
      `, `
        <button class="btn btn-secondary text-xs" onclick="App.closeModal()">Cancel</button>
        <button class="btn btn-primary text-xs" onclick="App.handleCreateApplication()">Submit Lodgement</button>
      `);
    } else if (type === 'institution') {
      this.openModal('Register New Institution in Directory', `
        <form id="create-inst-form" class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Institution Name *</label>
            <input type="text" id="modal-inst-name" class="input w-full text-xs" placeholder="e.g. Apex Institute of Technology" required />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Permanent ID *</label>
              <input type="text" id="modal-inst-pid" class="input w-full text-xs" placeholder="e.g. 1-94827101" required />
            </div>
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Category *</label>
              <select id="modal-inst-cat" class="select w-full text-xs">
                <option value="Engineering & Technology">Engineering & Technology</option>
                <option value="Management">Management</option>
                <option value="Pharmacy">Pharmacy</option>
                <option value="Architecture & Planning">Architecture & Planning</option>
                <option value="Polytechnic / Diploma">Polytechnic / Diploma</option>
              </select>
            </div>
          </div>
          <div class="grid grid-cols-3 gap-2">
            <div>
              <label class="block font-semibold text-slate-700 mb-1">State *</label>
              <input type="text" id="modal-inst-state" class="input w-full text-xs" placeholder="e.g. Maharashtra" required />
            </div>
            <div>
              <label class="block font-semibold text-slate-700 mb-1">District</label>
              <input type="text" id="modal-inst-district" class="input w-full text-xs" placeholder="e.g. Pune" />
            </div>
            <div>
              <label class="block font-semibold text-slate-700 mb-1">City</label>
              <input type="text" id="modal-inst-city" class="input w-full text-xs" placeholder="e.g. Pune" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Institution Type</label>
              <select id="modal-inst-type" class="select w-full text-xs">
                <option value="Govt">Govt</option>
                <option value="Govt-Aided">Govt-Aided</option>
                <option value="Unaided - Private">Unaided - Private</option>
                <option value="University Managed">University Managed</option>
              </select>
            </div>
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Approved Intake</label>
              <input type="number" id="modal-inst-intake" class="input w-full text-xs" value="480" />
            </div>
          </div>
        </form>
      `, `
        <button class="btn btn-secondary text-xs" onclick="App.closeModal()">Cancel</button>
        <button class="btn btn-primary text-xs" onclick="App.handleCreateInstitution()">Create Institution Record</button>
      `);
    } else if (type === 'compliance') {
      this.openModal('Register Regulatory Compliance Obligation', `
        <form class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Institution *</label>
            <select id="modal-comp-inst" class="select w-full text-xs">${instOptions}</select>
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Obligation Title *</label>
            <input type="text" id="modal-comp-title" class="input w-full text-xs" placeholder="e.g. Fixed Deposit Receipt (FDR) Renewal" required />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Category</label>
              <select id="modal-comp-cat" class="select w-full text-xs">
                <option value="Document expiry">Document expiry</option>
                <option value="Statutory undertaking">Statutory undertaking</option>
                <option value="Evidence submission">Evidence submission</option>
                <option value="Annual disclosure">Annual disclosure</option>
              </select>
            </div>
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Due Date *</label>
              <input type="date" id="modal-comp-due" class="input w-full text-xs" value="2026-11-20" required />
            </div>
          </div>
        </form>
      `, `
        <button class="btn btn-secondary text-xs" onclick="App.closeModal()">Cancel</button>
        <button class="btn btn-primary text-xs" onclick="App.handleCreateCompliance()">Register Obligation</button>
      `);
    } else if (type === 'complaint') {
      this.openModal('Lodge Institutional Grievance / Vigilance Complaint', `
        <form class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Institution Subject *</label>
            <select id="modal-cplt-inst" class="select w-full text-xs">${instOptions}</select>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Receiving Bureau *</label>
              <select id="modal-cplt-bureau" class="select w-full text-xs">
                <option value="PGRC">Public Grievance Redressal Cell (PGRC)</option>
                <option value="Regulation Bureau">Regulation Bureau</option>
                <option value="Vigilance Bureau">Vigilance Bureau</option>
                <option value="Approval Bureau">Approval Bureau</option>
              </select>
            </div>
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Category</label>
              <select id="modal-cplt-cat" class="select w-full text-xs">
                <option value="Intake discrepancy">Intake discrepancy / Over-admissions</option>
                <option value="Faculty deficiency">Faculty cadre deficiency</option>
                <option value="Fee irregularities">Capitation fee / Fee irregularities</option>
                <option value="Document validity">Unverified certificate submission</option>
              </select>
            </div>
          </div>
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Summary of Allegation / Inquiry *</label>
            <textarea id="modal-cplt-summary" class="input w-full text-xs h-20" placeholder="State facts, dates, and evidence references..." required></textarea>
          </div>
        </form>
      `, `
        <button class="btn btn-secondary text-xs" onclick="App.closeModal()">Cancel</button>
        <button class="btn btn-primary text-xs" onclick="App.handleCreateComplaint()">Lodge Record</button>
      `);
    } else if (type === 'task') {
      this.openModal('Create Administrative Governance Task', `
        <form class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Task Title *</label>
            <input type="text" id="modal-task-title" class="input w-full text-xs" placeholder="e.g. Verify rectified fire NOC submission" required />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Assigned Bureau</label>
              <select id="modal-task-bureau" class="select w-full text-xs">
                <option value="Approval Bureau">Approval Bureau</option>
                <option value="Vigilance Bureau">Vigilance Bureau</option>
                <option value="Policy & Academic Bureau">Policy & Academic Bureau</option>
                <option value="Regional Office">Regional Office</option>
              </select>
            </div>
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Priority</label>
              <select id="modal-task-prio" class="select w-full text-xs">
                <option value="High">High</option>
                <option value="Critical">Critical</option>
                <option value="Medium">Medium</option>
              </select>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Due Date</label>
              <input type="date" id="modal-task-due" class="input w-full text-xs" value="2026-11-10" />
            </div>
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Assignee</label>
              <input type="text" id="modal-task-assignee" class="input w-full text-xs" value="Assigned Officer" />
            </div>
          </div>
        </form>
      `, `
        <button class="btn btn-secondary text-xs" onclick="App.closeModal()">Cancel</button>
        <button class="btn btn-primary text-xs" onclick="App.handleCreateTask()">Create Task</button>
      `);
    } else {
      this.toast(`Create dialog for '${type}' opened in workspace.`, 'info');
    }
  },

  async handleCreateApplication() {
    const instId = document.getElementById('modal-app-inst').value;
    const type = document.getElementById('modal-app-type').value;
    const year = document.getElementById('modal-app-year').value;
    const owner = document.getElementById('modal-app-owner').value;
    const due = document.getElementById('modal-app-due').value;

    const newApp = await API.createApplication({
      institution_id: instId,
      type,
      academic_year: year,
      owner,
      due_date: due
    });

    this.closeModal();
    this.toast(`Application ${newApp.id} lodged successfully.`, 'success');
    this.refresh();
  },

  async handleCreateInstitution() {
    const name = document.getElementById('modal-inst-name').value.trim();
    const pid = document.getElementById('modal-inst-pid').value.trim();
    const state = document.getElementById('modal-inst-state').value.trim();
    const district = document.getElementById('modal-inst-district').value.trim();
    const city = document.getElementById('modal-inst-city').value.trim();
    const cat = document.getElementById('modal-inst-cat').value;
    const type = document.getElementById('modal-inst-type').value;
    const intake = parseInt(document.getElementById('modal-inst-intake').value) || 0;

    if (!name || !pid || !state) {
      this.toast('Please enter Name, Permanent ID, and State.', 'error');
      return;
    }

    const newInst = await API.createInstitution({
      name,
      permanent_id: pid,
      state,
      district: district || state,
      city: city || district || state,
      category: cat,
      institution_type: type,
      total_intake: intake,
      approval_status: 'Approved',
      approval_period: '2026-2027',
      programmes_count: 4
    });

    this.closeModal();
    this.toast(`Institution ${newInst.name} registered successfully.`, 'success');
    this.refresh();
  },

  async handleCreateCompliance() {
    const instId = document.getElementById('modal-comp-inst').value;
    const title = document.getElementById('modal-comp-title').value.trim();
    const cat = document.getElementById('modal-comp-cat').value;
    const due = document.getElementById('modal-comp-due').value;

    if (!title) {
      this.toast('Please enter obligation title.', 'error');
      return;
    }

    const newComp = await API.createCompliance({
      institution_id: instId,
      title,
      category: cat,
      due_date: due,
      status: "Upcoming"
    });

    this.closeModal();
    this.toast(`Compliance obligation ${newComp.id} registered.`, 'success');
    this.refresh();
  },

  async handleCreateComplaint() {
    const instId = document.getElementById('modal-cplt-inst').value;
    const bureau = document.getElementById('modal-cplt-bureau').value;
    const cat = document.getElementById('modal-cplt-cat').value;
    const summary = document.getElementById('modal-cplt-summary').value.trim();

    if (!summary) {
      this.toast('Please enter summary of allegation.', 'error');
      return;
    }

    const newCase = await API.createComplaint({
      institution_id: instId,
      bureau,
      category: cat,
      summary,
      due_date: "2026-11-20"
    });

    this.closeModal();
    this.toast(`Grievance ${newCase.id} registered successfully.`, 'success');
    this.refresh();
  },

  async handleCreateTask() {
    const title = document.getElementById('modal-task-title').value.trim();
    const bureau = document.getElementById('modal-task-bureau').value;
    const prio = document.getElementById('modal-task-prio').value;
    const due = document.getElementById('modal-task-due').value;
    const assignee = document.getElementById('modal-task-assignee').value.trim();

    if (!title) {
      this.toast('Please enter task title.', 'error');
      return;
    }

    await API.createTask({
      title,
      assigned_bureau: bureau,
      priority: prio,
      due_date: due,
      assigned_to: assignee || "Assigned Officer"
    });

    this.closeModal();
    this.toast('Governance action task created.', 'success');
    this.refresh();
  },

  toast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    const styles = {
      success: 'bg-emerald-800 text-white border-l-4 border-emerald-400',
      error: 'bg-red-800 text-white border-l-4 border-red-400',
      warning: 'bg-amber-800 text-white border-l-4 border-amber-400',
      info: 'bg-navy-900 text-white border-l-4 border-blue-400'
    }[type] || 'bg-navy-900 text-white';

    toast.className = `p-3 rounded shadow-lg flex items-center justify-between text-xs font-medium animate-fade-in ${styles}`;
    toast.innerHTML = `
      <div class="flex items-center gap-2">
        <span>${message}</span>
      </div>
      <button class="ml-4 text-white opacity-60 hover:opacity-100" onclick="this.parentElement.remove()">&times;</button>
    `;

    container.appendChild(toast);
    setTimeout(() => {
      toast.classList.add('opacity-0', 'transition-opacity');
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  },

  toggleSidebar(forceState = null) {
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');
    if (!sidebar) return;

    const isOpen = forceState !== null ? forceState : !sidebar.classList.contains('translate-x-0');
    if (isOpen) {
      sidebar.classList.remove('-translate-x-full');
      sidebar.classList.add('translate-x-0');
      if (backdrop) backdrop.classList.remove('hidden');
      document.body.classList.add('overflow-hidden', 'md:overflow-auto');
    } else {
      sidebar.classList.remove('translate-x-0');
      sidebar.classList.add('-translate-x-full');
      if (backdrop) backdrop.classList.add('hidden');
      document.body.classList.remove('overflow-hidden', 'md:overflow-auto');
    }
  }
};

window.App = App;

document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
