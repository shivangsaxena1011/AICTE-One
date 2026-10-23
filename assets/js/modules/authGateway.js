/**
 * AICTE ONE - Role Selection & Multi-Step Authentication Gateway
 * Judge-Ready Sovereign Tech UI with FIDO2/WebAuthn Passkey, Visual Verification, and Demo Mode
 */
const AuthGateway = {
  containerId: 'auth-gateway-overlay',
  step: 1, // 1 = Role Selection, 2 = Credentials + Verification
  selectedRole: null,
  captchaCode: '',
  isJudgeDemo: false,
  error: null,
  loading: false,
  mfaRequired: false,
  mfaTempCredentials: null,

  // 8 Statutory AICTE Roles Defined by Regulation
  ROLES: [
    {
      code: 'SUPER_ADMIN',
      name: 'Super Administrator',
      hindi: 'मुख्य प्रशासक',
      icon: 'shield_person',
      badge: 'Statutory Apex',
      color: 'blue',
      privileged: true,
      description: 'Full statutory authority across central bureaus, institutions, approval workflows, and immutable audit logs.',
      defaultUsernameHint: 'superadmin'
    },
    {
      code: 'SECURITY_OFFICER',
      name: 'Security Officer',
      hindi: 'सुरक्षा अधिकारी',
      icon: 'security',
      badge: 'Cyber & Vigilance',
      color: 'indigo',
      privileged: true,
      description: 'Security incident surveillance, document forensic anomaly review, threat monitoring, and system safeguards.',
      defaultUsernameHint: 'security.officer'
    },
    {
      code: 'POLICY_COMPLIANCE_OFFICER',
      name: 'Policy & Compliance Officer',
      hindi: 'नीति एवं अनुपालन अधिकारी',
      icon: 'policy',
      badge: 'Academic Bureau',
      color: 'amber',
      privileged: false,
      description: 'Regulatory compliance audits, land lease deed tracking, FDR monitoring, and deficiency cure management.',
      defaultUsernameHint: 'compliance.officer'
    },
    {
      code: 'COMPLAINT_OFFICER',
      name: 'Complaint & Vigilance Officer',
      hindi: 'शिकायत एवं सतर्कता अधिकारी',
      icon: 'gavel',
      badge: 'Grievance Cell',
      color: 'red',
      privileged: false,
      description: 'Grievance intake, cross-bureau clash detection, vigilance case investigation, and CPGRAMS matter disposal.',
      defaultUsernameHint: 'complaint.officer'
    },
    {
      code: 'ANTI_RAGGING_OFFICER',
      name: 'Anti-Ragging Officer',
      hindi: 'एंटी-रैगिंग समिति',
      icon: 'campaign',
      badge: 'Student Safety',
      color: 'rose',
      privileged: false,
      description: 'Student safety enforcement, rapid campus squad alerts, urgent hearing notices, and victim protection monitoring.',
      defaultUsernameHint: 'antiragging.officer'
    },
    {
      code: 'INSTITUTE_HEAD',
      name: 'Institute Principal / Head',
      hindi: 'संस्थान प्राचार्य / निदेशक',
      icon: 'account_balance',
      badge: 'Tenant Isolated',
      color: 'cyan',
      privileged: false,
      description: 'Tenant-isolated institutional portal for digital twin inspection, EoA applications, and compliance filings.',
      defaultUsernameHint: 'principal.gitm'
    },
    {
      code: 'STUDENT_COMPLAINANT',
      name: 'Student / Complainant',
      hindi: 'छात्र / शिकायतकर्ता',
      icon: 'school',
      badge: 'Citizen Access',
      color: 'emerald',
      privileged: false,
      description: 'Citizen grievance lodging, ragging reporting, digital evidence submission, and real-time case milestone tracking.',
      defaultUsernameHint: 'student.aarav'
    },
    {
      code: 'PUBLIC_VISITOR',
      name: 'Public Visitor',
      hindi: 'सार्वजनिक नागरिक',
      icon: 'visibility',
      badge: 'Open Registry',
      color: 'slate',
      privileged: false,
      description: 'Open public directory search across 8,800+ approved institutions, approval status verification, and official records.',
      defaultUsernameHint: 'public.visitor'
    }
  ],

  init() {
    this.createOverlay();
    this.checkStoredSession();
  },

  createOverlay() {
    let el = document.getElementById(this.containerId);
    if (!el) {
      el = document.createElement('div');
      el.id = this.containerId;
      el.className = 'fixed inset-0 z-[100] bg-[#001332] text-slate-100 flex flex-col overflow-y-auto transition-opacity duration-300';
      document.body.appendChild(el);
    }
  },

  checkStoredSession() {
    const isDemo = sessionStorage.getItem('aicte_judge_demo') === 'true';
    if (isDemo) {
      this.isJudgeDemo = true;
      this.mountDemoBanner();
      this.hide();
      return;
    }

    const token = API.getToken();
    if (token) {
      // Validate session with backend
      API.getCurrentUser().then(user => {
        if (user) {
          App.currentUser = user;
          App.currentRole = {
            id: user.role,
            name: user.full_name,
            email: user.email,
            bureau: user.department || user.role,
            perms: (user.permissions || []).join(', ')
          };
          App.updateRoleDisplay();
          this.hide();
        } else {
          API.setToken(null);
          this.show();
        }
      }).catch(() => {
        API.setToken(null);
        this.show();
      });
    } else {
      this.show();
    }
  },

  show() {
    const el = document.getElementById(this.containerId);
    if (!el) this.createOverlay();
    document.getElementById(this.containerId).style.display = 'flex';
    document.body.style.overflow = 'hidden';
    this.render();
  },

  hide() {
    const el = document.getElementById(this.containerId);
    if (el) {
      el.style.display = 'none';
    }
    document.body.style.overflow = '';
  },

  generateCaptcha() {
    const chars = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ';
    let code = '';
    for (let i = 0; i < 6; i++) {
      code += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    this.captchaCode = code;
    return code;
  },

  renderCaptchaCanvas() {
    const canvas = document.getElementById('visual-captcha-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;

    // Background gradient with noise
    const grad = ctx.createLinearGradient(0, 0, w, h);
    grad.addColorStop(0, '#0f172a');
    grad.addColorStop(1, '#1e293b');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);

    // Random background lines
    for (let i = 0; i < 4; i++) {
      ctx.strokeStyle = `rgba(${Math.random()*150+50}, ${Math.random()*150+50}, 255, 0.25)`;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(Math.random() * w, Math.random() * h);
      ctx.bezierCurveTo(Math.random() * w, Math.random() * h, Math.random() * w, Math.random() * h, Math.random() * w, Math.random() * h);
      ctx.stroke();
    }

    // Draw characters with rotation & distortion
    ctx.font = 'bold 24px "JetBrains Mono", monospace';
    ctx.textBaseline = 'middle';
    const charSpacing = (w - 30) / 6;

    for (let i = 0; i < this.captchaCode.length; i++) {
      ctx.save();
      const x = 18 + i * charSpacing;
      const y = h / 2 + (Math.random() * 6 - 3);
      const angle = (Math.random() - 0.5) * 0.35;
      ctx.translate(x, y);
      ctx.rotate(angle);
      ctx.fillStyle = ['#38bdf8', '#fb923c', '#4ade80', '#e2e8f0', '#f472b6'][i % 5];
      ctx.shadowColor = 'rgba(0,0,0,0.6)';
      ctx.shadowBlur = 4;
      ctx.fillText(this.captchaCode[i], 0, 0);
      ctx.restore();
    }
  },

  refreshCaptcha() {
    this.generateCaptcha();
    this.renderCaptchaCanvas();
    const codeEl = document.getElementById('visual-captcha-text');
    if (codeEl) codeEl.textContent = this.captchaCode;
    const input = document.getElementById('gateway-captcha-input');
    if (input) input.value = '';
  },

  selectRole(roleCode) {
    const role = this.ROLES.find(r => r.code === roleCode);
    if (!role) return;

    if (role.code === 'PUBLIC_VISITOR') {
      this.selectedRole = role;
      this.step = 2;
      this.error = null;
      this.render();
      return;
    }

    this.selectedRole = role;
    this.step = 2;
    this.error = null;
    this.mfaRequired = false;
    this.generateCaptcha();
    this.render();
    setTimeout(() => this.renderCaptchaCanvas(), 50);
  },

  changeRole() {
    this.step = 1;
    this.selectedRole = null;
    this.error = null;
    this.mfaRequired = false;
    this.render();
  },

  async enterJudgeDemo() {
    this.isJudgeDemo = true;
    sessionStorage.setItem('aicte_judge_demo', 'true');
    this.mountDemoBanner();

    try {
      const res = await API.createDemoSession();
      if (res && res.user) App.currentUser = res.user;
    } catch (e) {
      console.warn('Demo session API fallback:', e);
    }

    if (!App.currentUser) {
      App.currentUser = {
        id: 'USR-DEMO-JUDGE',
        username: 'demo.judge',
        full_name: 'Honorable Evaluation Committee / Judge',
        role: 'DEMO_JUDGE',
        department: 'National Evaluation Bureau',
        institution_id: null,
        permissions: ['READ_ALL', 'EXPLORE_PROTOTYPE', 'DEMO_SANDBOX']
      };
    }
    App.currentRole = {
      id: 'DEMO_JUDGE',
      name: 'Honorable Evaluation Committee / Judge',
      email: 'judge@aicte-india.org',
      bureau: 'National Evaluation Bureau (Demo)',
      perms: 'Full Evaluation & Sandbox Exploration Mode (Read-Only Safety)'
    };
    App.updateRoleDisplay();
    this.hide();
    App.toast("Welcome, Honorable Judge. AICTE ONE Demo Mode initialized.", "info");
    App.navigate('overview');
  },

  mountDemoBanner() {
    let banner = document.getElementById('judge-demo-banner');
    if (!banner) {
      banner = document.createElement('div');
      banner.id = 'judge-demo-banner';
      banner.className = 'w-full bg-[#3b0764] border-b border-purple-500/40 text-purple-200 px-4 py-1.5 text-xs flex items-center justify-between sticky top-1 z-40 shadow-sm';
      banner.innerHTML = `
        <div class="flex items-center gap-2 font-medium">
          <span class="px-1.5 py-0.2 bg-purple-800 text-purple-100 rounded text-[10px] font-bold tracking-wider uppercase border border-purple-600">DEMO MODE</span>
          <span class="truncate">Sample regulatory evaluation dataset. Real administrative database mutations are restricted.</span>
        </div>
        <div class="flex items-center gap-3 shrink-0">
          <button class="text-xs text-purple-300 hover:text-white underline font-semibold cursor-pointer" onclick="AuthGateway.exitDemoMode()">
            Exit Demo & Sign In →
          </button>
        </div>
      `;
      document.body.prepend(banner);
    }
  },

  exitDemoMode() {
    this.isJudgeDemo = false;
    sessionStorage.removeItem('aicte_judge_demo');
    const banner = document.getElementById('judge-demo-banner');
    if (banner) banner.remove();
    App.currentUser = null;
    App.currentRole = null;
    API.setToken(null);
    this.step = 1;
    this.selectedRole = null;
    this.show();
  },

  continueAsPublic() {
    App.currentUser = null;
    App.currentRole = {
      id: 'PUBLIC_VISITOR',
      name: 'Public Citizen / Visitor',
      email: 'citizen@bharat.in',
      bureau: 'Public Directory Access',
      perms: 'Public Institutional Directory, Digital Twin & Verification Gateway'
    };
    App.updateRoleDisplay();
    this.hide();
    App.toast("Continuing as Public Visitor. Institutional directories unlocked.", "info");
    App.navigate('institutions');
  },

  async handleCredentialsSubmit(e) {
    if (e) e.preventDefault();
    this.error = null;

    const usernameInput = document.getElementById('gateway-username');
    const passwordInput = document.getElementById('gateway-password');
    const captchaInput = document.getElementById('gateway-captcha-input');
    const mfaInput = document.getElementById('gateway-mfa-input');

    const username = (usernameInput ? usernameInput.value : '').trim();
    const password = passwordInput ? passwordInput.value : '';
    const captchaEntered = (captchaInput ? captchaInput.value : '').trim().toUpperCase();
    const mfaCode = mfaInput ? mfaInput.value.trim() : null;

    if (!username) {
      this.error = "Please enter your official username or registered email.";
      this.render();
      return;
    }
    if (!password) {
      this.error = "Please enter your statutory account password.";
      this.render();
      return;
    }

    // Validate Visual Captcha
    if (!captchaEntered || captchaEntered !== this.captchaCode) {
      this.error = "Invalid visual verification code. Please enter the characters displayed in the security box.";
      this.refreshCaptcha();
      this.render();
      return;
    }

    this.loading = true;
    this.render();

    try {
      const data = await API.login(username, password, mfaCode);

      // Validate that returned user's role matches selected role
      const returnedRole = data.user ? data.user.role : '';
      if (this.selectedRole && this.selectedRole.code !== returnedRole) {
        // Enforce role consistency
        API.setToken(null);
        this.error = `Role mismatch: This account belongs to the '${data.user.role}' jurisdiction, but you selected '${this.selectedRole.name}'. Please select the appropriate role card.`;
        this.loading = false;
        this.refreshCaptcha();
        this.render();
        return;
      }

      // Success
      App.currentUser = data.user;
      App.currentRole = {
        id: data.user.role,
        name: data.user.full_name,
        email: data.user.email,
        bureau: data.user.department || data.user.role,
        perms: (data.user.permissions || []).join(', ')
      };
      App.updateRoleDisplay();
      this.hide();
      App.toast(`Authenticated successfully as ${data.user.full_name}`, "success");
      const targetRoute = typeof RBAC !== 'undefined' ? RBAC.getDefaultRoute(data.user.role) : 'overview';
      App.navigate(targetRoute);

    } catch (err) {
      this.loading = false;
      const errMsg = err.message || "Authentication failed.";
      if (/MFA|TOTP|code required/i.test(errMsg)) {
        this.mfaRequired = true;
        this.error = "MFA Required: This privileged officer account enforces two-factor authentication. Please enter your 6-digit TOTP code (Default demo code: 123456).";
      } else {
        this.error = errMsg;
      }
      this.refreshCaptcha();
      this.render();
    }
  },

  async handleBiometricLogin() {
    this.error = null;
    const usernameInput = document.getElementById('gateway-username');
    const username = (usernameInput ? usernameInput.value : '').trim() || (this.selectedRole ? this.selectedRole.defaultUsernameHint : '');

    if (!username) {
      this.error = "Please enter your statutory username before initiating biometric / passkey verification.";
      this.render();
      return;
    }

    if (!window.PublicKeyCredential) {
      this.error = "Biometric Passkey / WebAuthn is not supported by this browser environment. Please use standard password authentication.";
      this.render();
      return;
    }

    this.loading = true;
    this.render();

    try {
      // Step 1: Request assertion challenge from server
      const options = await API.getWebAuthnLoginOptions(username);

      // Convert base64 / string challenge to Uint8Array for browser WebAuthn API
      const challengeBuffer = new TextEncoder().encode(options.challenge);
      const allowCredentials = (options.allowCredentials || []).map(c => ({
        type: 'public-key',
        id: new TextEncoder().encode(c.id)
      }));

      // Step 2: Invoke hardware authenticator
      let assertion;
      try {
        assertion = await navigator.credentials.get({
          publicKey: {
            challenge: challengeBuffer,
            timeout: options.timeout || 60000,
            rpId: options.rpId || window.location.hostname,
            allowCredentials: allowCredentials,
            userVerification: options.userVerification || 'preferred'
          }
        });
      } catch (domErr) {
        throw new Error(`Device authenticator error: ${domErr.message || 'Passkey assertion was cancelled or unavailable on this device.'}`);
      }

      if (!assertion) {
        throw new Error("No passkey credential returned from device.");
      }

      // Step 3: Verify with server
      const verifyPayload = {
        username: username,
        id: assertion.id,
        rawId: btoa(String.fromCharCode(...new Uint8Array(assertion.rawId))),
        type: assertion.type,
        response: {
          clientDataJSON: btoa(String.fromCharCode(...new Uint8Array(assertion.response.clientDataJSON))),
          authenticatorData: btoa(String.fromCharCode(...new Uint8Array(assertion.response.authenticatorData))),
          signature: btoa(String.fromCharCode(...new Uint8Array(assertion.response.signature)))
        }
      };

      const loginRes = await API.verifyWebAuthnLogin(verifyPayload);

      App.currentUser = loginRes.user;
      App.currentRole = {
        id: loginRes.user.role,
        name: loginRes.user.full_name,
        email: loginRes.user.email,
        bureau: loginRes.user.department || loginRes.user.role,
        perms: (loginRes.user.permissions || []).join(', ')
      };
      App.updateRoleDisplay();
      this.hide();
      App.toast(`Authenticated via Biometric Passkey as ${loginRes.user.full_name}`, "success");
      const targetRoute = typeof RBAC !== 'undefined' ? RBAC.getDefaultRoute(loginRes.user.role) : 'overview';
      App.navigate(targetRoute);

    } catch (err) {
      this.loading = false;
      this.error = `Passkey Notice: ${err.message || 'Biometric authentication could not complete.'} Please authenticate using standard password credentials.`;
      this.render();
    }
  },

  render() {
    const el = document.getElementById(this.containerId);
    if (!el) return;

    if (this.step === 1) {
      el.innerHTML = this.renderStep1();
    } else {
      el.innerHTML = this.renderStep2();
      this.renderCaptchaCanvas();
    }
  },

  renderStep1() {
    return `
      <!-- Sovereign Government Tricolor Header Stripe -->
      <div class="h-1 bg-gradient-to-r from-[#ea580c] via-white to-[#059669] w-full shrink-0"></div>

      <div class="flex-1 flex flex-col justify-between max-w-6xl mx-auto w-full px-4 py-5 sm:px-6 sm:py-6 lg:px-8">
        
        <!-- Header & Emblem -->
        <div class="text-center mb-5 sm:mb-6">
          <div class="inline-flex items-center justify-center gap-3.5 mb-2.5">
            <div style="width:52px;height:52px;min-width:52px;min-height:52px;max-width:52px;max-height:52px;" class="rounded-xl bg-white p-1 border border-blue-400/40 shadow-lg shrink-0 flex items-center justify-center overflow-hidden">
              <img src="assets/img/shankh-logo.png" alt="SHANKH Logo" style="width:100%;height:100%;max-width:44px;max-height:44px;object-fit:contain;" class="object-contain">
            </div>
            <div class="text-left">
              <div class="text-[11px] sm:text-xs font-semibold text-amber-400 font-sans tracking-wide flex items-center gap-2">
                <span>अखिल भारतीय तकनीकी शिक्षा परिषद</span>
                <span class="text-[10px] font-mono uppercase px-1.5 py-0.2 rounded bg-amber-950/70 text-amber-300 border border-amber-500/30">Project SHANKH</span>
              </div>
              <h1 class="text-lg sm:text-2xl font-extrabold text-white tracking-tight mt-0.5">AICTE ONE — Central Governance & Intelligence Platform</h1>
              <div class="text-[11px] text-blue-300 font-mono mt-0.5 font-medium">CODE • ANALYZE • SOLVE — Sovereign Autonomous Regulatory Engine</div>
            </div>
          </div>
          <p class="text-[11.5px] sm:text-xs text-slate-300/90 max-w-2xl mx-auto leading-relaxed">
            Official Role-Based Statutory Authentication Gateway under the AICTE Approval Process Handbook (APH 2024-27). Select your statutory persona to access authorized regulatory jurisdictions.
          </p>
        </div>

        <!-- Refined Compact Judge Demo Banner -->
        <div class="mb-5 bg-gradient-to-r from-[#1f0e38] via-[#2d154f] to-[#1f0e38] border border-purple-500/40 rounded-xl px-4 py-2.5 sm:px-5 sm:py-3 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-lg">
          <div class="flex items-center gap-3 text-left w-full sm:w-auto">
            <div class="w-8 h-8 rounded-lg bg-purple-900/90 border border-purple-400/40 flex items-center justify-center shrink-0">
              <span class="material-symbols-outlined text-purple-300 text-lg">verified</span>
            </div>
            <div class="min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-xs font-bold uppercase tracking-wider text-purple-200 font-mono">Judges & Prototype Evaluators</span>
                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-800/90 text-purple-200 border border-purple-500/40">No Password Required</span>
              </div>
              <p class="text-[11px] text-purple-300/80 truncate sm:whitespace-normal">Explore full prototype with pre-populated datasets across 8,800+ colleges, complaints, EVCs & document verification.</p>
            </div>
          </div>
          <button id="judge-demo-btn" class="w-full sm:w-auto px-4 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold text-xs shadow-md transition-all flex items-center justify-center gap-1.5 shrink-0 cursor-pointer active:scale-95 border border-purple-400/40" onclick="AuthGateway.enterJudgeDemo()">
            <span>Enter Judge Demo</span>
            <span class="material-symbols-outlined text-[15px]">arrow_forward</span>
          </button>
        </div>

        <!-- Role Selection Cards Grid with Uniform Heights & Accessible Focus -->
        <div>
          <div class="flex items-center justify-between mb-2.5 px-1">
            <span class="text-xs font-bold uppercase tracking-wider text-slate-300">Select Statutory Governance Persona</span>
            <span class="text-[11px] text-slate-400 font-mono">8 Roles Available</span>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            ${this.ROLES.map(r => `
              <div 
                id="role-card-${r.code.toLowerCase()}"
                data-role="${r.code}"
                tabindex="0"
                role="button"
                aria-label="Authenticate as ${r.name}"
                onclick="AuthGateway.selectRole('${r.code}')"
                onkeydown="if(event.key === 'Enter' || event.key === ' ') { event.preventDefault(); AuthGateway.selectRole('${r.code}'); }"
                class="group relative bg-[#091830] hover:bg-[#0e2448] focus:bg-[#0e2448] border border-slate-700/80 hover:border-blue-400 focus:border-blue-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 rounded-xl p-3.5 sm:p-4 transition-all duration-200 cursor-pointer shadow-md hover:shadow-blue-950/40 hover:-translate-y-0.5 flex flex-col justify-between min-h-[210px] sm:min-h-[225px]"
              >
                <div>
                  <div class="flex items-start justify-between mb-2.5">
                    <div class="w-9 h-9 rounded-lg bg-[#001332] border border-slate-700 group-hover:border-blue-400/60 group-focus:border-blue-400/60 flex items-center justify-center transition-colors">
                      <span class="material-symbols-outlined text-blue-400 group-hover:text-amber-400 group-focus:text-amber-400 text-lg transition-colors">${r.icon}</span>
                    </div>
                    <span class="text-[9.5px] font-mono font-bold uppercase px-2 py-0.5 rounded bg-slate-800/90 text-slate-300 border border-slate-700">
                      ${r.badge}
                    </span>
                  </div>

                  <h3 class="font-bold text-[13px] text-white group-hover:text-blue-300 transition-colors leading-snug">${r.name}</h3>
                  <div class="text-[11px] text-amber-400/90 font-medium mb-1.5 font-sans">${r.hindi}</div>
                  <p class="text-[11.5px] text-slate-300/90 leading-relaxed font-normal">${r.description}</p>
                </div>

                <div class="mt-3.5 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-blue-400 font-semibold group-hover:text-amber-400 group-focus:text-amber-400 transition-colors">
                  <span>${r.code === 'PUBLIC_VISITOR' ? 'Open Access' : 'Authenticate Role'}</span>
                  <span class="material-symbols-outlined text-[15px] group-hover:translate-x-1 group-focus:translate-x-1 transition-transform">arrow_forward</span>
                </div>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Footer Notice -->
        <div class="text-center text-[11px] text-slate-400 mt-5 pt-3.5 border-t border-slate-800/60 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>AICTE ONE Platform v2.4.0 · Statutory Architecture Compliant</span>
          <span>Security Notice: All administrative logins are cryptographically logged to the Sovereign Audit Trail</span>
        </div>

      </div>
    `;
  },

  renderStep2() {
    const role = this.selectedRole || this.ROLES[0];
    const isPublic = role.code === 'PUBLIC_VISITOR';

    return `
      <!-- Sovereign Government Tricolor Header Stripe -->
      <div class="h-1 bg-gradient-to-r from-[#ea580c] via-white to-[#059669] w-full shrink-0"></div>

      <div class="flex-1 flex items-center justify-center p-4 sm:p-6">
        <div class="w-full max-w-md bg-[#0a1a36] border border-slate-700/80 rounded-2xl shadow-2xl p-6 sm:p-8 backdrop-blur-md">
          
          <!-- Back / Change Role Header -->
          <div class="flex items-center justify-between mb-5 pb-3 border-b border-slate-800">
            <button id="back-to-roles-btn" class="text-xs text-slate-400 hover:text-white flex items-center gap-1 cursor-pointer transition-colors" onclick="AuthGateway.changeRole()">
              <span class="material-symbols-outlined text-[16px]">arrow_back</span>
              <span>Change Role</span>
            </button>
            <span class="text-[10px] font-mono uppercase text-slate-400 px-2 py-0.5 rounded bg-slate-900 border border-slate-800">Step 2 of 2</span>
          </div>

          <!-- Role Identity Badge with SHANKH Branding -->
          <div class="flex items-center gap-3.5 mb-5 bg-[#001332] border border-blue-900/60 rounded-xl p-3.5">
            <img src="assets/img/shankh-logo.png" alt="SHANKH Logo" style="width:48px;height:48px;min-width:48px;min-height:48px;max-width:48px;max-height:48px;object-fit:contain;" class="rounded-xl object-contain bg-white p-1 border border-blue-500/40 shrink-0 shadow-md">
            <div>
              <div class="text-[10px] text-amber-400 uppercase font-mono font-bold">${role.badge} · SHANKH</div>
              <h2 class="text-sm font-bold text-white">${role.name}</h2>
              <div class="text-[11px] text-slate-400 font-mono">Suggested Persona: ${role.defaultUsernameHint}</div>
            </div>
          </div>

          <!-- Error Alert -->
          ${this.error ? `
            <div class="mb-4 p-3 rounded-lg bg-red-950/80 border border-red-500/60 text-red-200 text-xs flex items-start gap-2.5">
              <span class="material-symbols-outlined text-red-400 text-[18px] shrink-0 mt-0.5">error</span>
              <div class="leading-relaxed">${this.error}</div>
            </div>
          ` : ''}

          ${isPublic ? `
            <!-- Public Visitor Direct Access -->
            <div class="text-center py-4">
              <p class="text-xs text-slate-300 mb-5 leading-relaxed">
                As a Public Visitor, you have open access to search 8,800+ AICTE-approved institutions across India, verify institutional approvals, and review open statutory reports without entering a password.
              </p>
              <button class="w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer" onclick="AuthGateway.continueAsPublic()">
                <span>Continue to Public Institutional Directory →</span>
              </button>
            </div>
          ` : `
            <!-- Form for Authenticated Roles -->
            <form onsubmit="AuthGateway.handleCredentialsSubmit(event)" class="space-y-4">
              
              <div>
                <label class="block text-xs font-semibold text-slate-300 mb-1">Official Username or Email</label>
                <div class="relative">
                  <span class="material-symbols-outlined absolute left-3 top-2.5 text-slate-500 text-[18px]">person</span>
                  <input 
                    type="text" 
                    id="gateway-username" 
                    required 
                    placeholder="e.g. ${role.defaultUsernameHint}"
                    class="w-full pl-9 pr-3 py-2 text-xs rounded-lg bg-[#001332] border border-slate-700 text-white placeholder-slate-500 focus:outline-hidden focus:border-blue-500 transition-colors"
                  />
                </div>
              </div>

              <div>
                <label class="block text-xs font-semibold text-slate-300 mb-1">Account Password</label>
                <div class="relative">
                  <span class="material-symbols-outlined absolute left-3 top-2.5 text-slate-500 text-[18px]">lock</span>
                  <input 
                    type="password" 
                    id="gateway-password" 
                    required 
                    placeholder="Enter statutory password (Demo: AicteOne@2026!)"
                    class="w-full pl-9 pr-3 py-2 text-xs rounded-lg bg-[#001332] border border-slate-700 text-white placeholder-slate-500 focus:outline-hidden focus:border-blue-500 transition-colors"
                  />
                </div>
              </div>

              <!-- Visual Captcha Security Verification Box -->
              <div>
                <label class="block text-xs font-semibold text-slate-300 mb-1">Visual Security Verification</label>
                <div class="flex items-center gap-2 mb-2">
                  <div class="relative shrink-0">
                    <canvas id="visual-captcha-canvas" width="180" height="42" class="rounded-lg border border-slate-700 shadow-inner block"></canvas>
                    <span id="visual-captcha-text" class="sr-only">${this.captchaCode}</span>
                  </div>
                  <button id="refresh-captcha-btn" type="button" class="btn sm btn-secondary text-xs flex items-center gap-1 shrink-0 py-2 px-2.5" onclick="AuthGateway.refreshCaptcha()" title="Refresh Security Code">
                    <span class="material-symbols-outlined text-[16px]">refresh</span>
                    <span>Refresh</span>
                  </button>
                </div>
                <input 
                  type="text" 
                  id="gateway-captcha-input" 
                  required 
                  maxlength="6"
                  placeholder="Enter 6-digit code shown above" 
                  class="w-full px-3 py-2 text-xs uppercase font-mono tracking-widest rounded-lg bg-[#001332] border border-slate-700 text-white placeholder-slate-500 focus:outline-hidden focus:border-blue-500 transition-colors"
                />
              </div>

              <!-- MFA Input (Visible if account requires TOTP) -->
              ${(this.mfaRequired || role.privileged) ? `
                <div class="p-3 rounded-lg bg-blue-950/40 border border-blue-500/30">
                  <div class="flex items-center justify-between mb-1">
                    <label class="text-xs font-semibold text-amber-300 flex items-center gap-1">
                      <span class="material-symbols-outlined text-[14px]">key</span>
                      <span>MFA / TOTP Security Code</span>
                    </label>
                    <span class="text-[10px] text-slate-400 font-mono">Demo: 123456</span>
                  </div>
                  <input 
                    type="text" 
                    id="gateway-mfa-input" 
                    maxlength="6" 
                    value="${role.privileged ? '123456' : ''}"
                    placeholder="Enter 6-digit MFA code" 
                    class="w-full px-3 py-2 text-xs font-mono tracking-widest text-center rounded bg-[#001332] border border-slate-700 text-white placeholder-slate-500 focus:outline-hidden focus:border-amber-500"
                  />
                </div>
              ` : ''}

              <!-- Submit Button -->
              <button 
                type="submit" 
                ${this.loading ? 'disabled' : ''}
                class="w-full py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs sm:text-sm shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                ${this.loading ? `
                  <span class="spinner w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  <span>Verifying Credentials...</span>
                ` : `
                  <span>Sign In as ${role.name} →</span>
                `}
              </button>

              <!-- Biometric / Passkey Login for Privileged Roles -->
              ${role.privileged ? `
                <div class="relative flex py-2 items-center">
                  <div class="grow border-t border-slate-800"></div>
                  <span class="shrink mx-3 text-[10px] text-slate-500 uppercase font-mono">Or Sovereign Passkey</span>
                  <div class="grow border-t border-slate-800"></div>
                </div>

                <button 
                  type="button" 
                  onclick="AuthGateway.handleBiometricLogin()"
                  class="w-full py-2 rounded-lg bg-[#0f284e] hover:bg-[#1a365d] border border-blue-500/40 text-blue-200 font-semibold text-xs transition-all flex items-center justify-center gap-2 cursor-pointer"
                >
                  <span class="material-symbols-outlined text-[18px] text-blue-400">fingerprint</span>
                  <span>Biometric / Passkey Login</span>
                </button>
              ` : ''}

            </form>
          `}

          <!-- Quick Demo Switcher -->
          <div class="mt-5 pt-3 border-t border-slate-800 text-center">
            <button type="button" class="text-xs text-purple-400 hover:text-purple-300 font-semibold cursor-pointer" onclick="AuthGateway.enterJudgeDemo()">
              ⚡ Prefer Judge Demo Mode? Skip credentials →
            </button>
          </div>

        </div>
      </div>
    `;
  }
};

window.AuthGateway = AuthGateway;
