/**
 * Module 5: Dedicated Scrutiny & Workflow Engine (Module 2 in Reference)
 * "Bharat Civic-Sovereign Tech" Design System
 */
const ScrutinyModule = {
  selectedAppId: "APP-2026-0842",

  async render() {
    const apps = localStore.db.applications.filter(a => /scrutiny|validation/i.test(a.current_stage));
    const activeApp = localStore.db.applications.find(a => a.id === this.selectedAppId) || apps[0] || localStore.db.applications[0];
    const docs = localStore.db.documents.filter(d => d.institution_id === activeApp.institution_id);

    return `
      <div class="space-y-6">
        
        <!-- Sovereign Header -->
        <div class="flex flex-col xl:flex-row xl:items-end justify-between gap-4 pb-2 border-b border-slate-200/80">
          <div class="space-y-1">
            <div class="flex items-center gap-2">
              <span class="font-mono text-xs uppercase tracking-wider text-[#a73a00] font-bold">Statutory Workflow Engine</span>
              <span class="w-1.5 h-1.5 rounded-full bg-slate-300"></span>
              <span class="font-mono text-xs text-slate-500">Reg: AICTE Act 1987 §10(k)</span>
            </div>
            <div class="flex items-baseline gap-3 flex-wrap">
              <h1 class="font-headline text-2xl lg:text-3xl font-extrabold text-[#001332] tracking-tight">APH 2026-27 Scrutiny & Deficiency Workflow</h1>
              <span class="font-mono text-[11px] font-bold px-2 py-0.5 rounded bg-[#ffdad6] text-[#93000a]">CUTOFF: 11d 14h 22m</span>
            </div>
            <p class="text-xs text-slate-600 max-w-4xl">
              Examine statutory checklists, evaluate document evidence, flag regulatory deficiencies, and issue legal rectification notices.
            </p>
          </div>

          <div class="flex flex-wrap items-center gap-2 bg-slate-100/80 p-1.5 rounded-lg border border-slate-200">
            <button class="px-3 py-1.5 bg-[#001332] text-white font-semibold text-xs rounded-md shadow-xs hover:bg-[#0f284e] transition-colors flex items-center gap-1.5" 
              onclick="ScrutinyModule.openForwardEVC('${activeApp.id}')">
              <span class="material-symbols-outlined text-[16px]">forward</span>
              <span>Forward to EVC Committee</span>
            </button>
            <button class="px-3 py-1.5 bg-[#ba1a1a] text-white font-semibold text-xs rounded-md shadow-xs hover:bg-[#93000a] transition-colors flex items-center gap-1.5" 
              onclick="ScrutinyModule.openDeficiencyNotice('${activeApp.id}')">
              <span class="material-symbols-outlined text-[16px]">assignment_late</span>
              <span>Issue Deficiency Checklist</span>
            </button>
          </div>
        </div>

        <!-- 1. DYNAMIC STAGE PROGRESSION STEPPER -->
        <section class="bg-white p-5 rounded-xl border border-slate-200/90 shadow-xs space-y-3">
          <div class="flex items-center justify-between pb-2 border-b border-slate-100">
            <div>
              <span class="text-[10px] font-bold uppercase tracking-wider text-[#a73a00]">Statutory Approval Lifecycle</span>
              <h3 class="font-headline font-bold text-sm text-[#001332]">APH 2026-27 Approval Lifecycle & Rule Scrutiny</h3>
            </div>
            <div class="flex items-center gap-1.5 font-mono text-[11px] text-slate-500 bg-slate-50 px-2.5 py-1 rounded border border-slate-200">
              <span class="w-2 h-2 rounded-full bg-[#23a274] animate-pulse"></span>
              <span>Active Stage: Stage 03</span>
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            <!-- Stage 1 -->
            <div class="p-3 rounded-lg bg-slate-50 border border-slate-200/80 flex flex-col justify-between">
              <div>
                <div class="flex items-center justify-between mb-1">
                  <span class="font-mono text-[10px] text-slate-500 font-bold">STAGE 01</span>
                  <span class="material-symbols-outlined text-[#23a274] text-[16px]">check_circle</span>
                </div>
                <div class="font-bold text-xs text-[#001332] mb-0.5">Intake & TER Fee</div>
                <div class="text-[11px] text-slate-500">₹4,50,000 via Bharatkosh. Ref #BK-99023418.</div>
              </div>
              <div class="mt-2 pt-1 border-t border-slate-200/60">
                <span class="text-[10px] font-bold px-1.5 py-0.2 rounded bg-[#002f1e] text-[#23a274]">Cleared (Auto)</span>
              </div>
            </div>

            <!-- Stage 2 -->
            <div class="p-3 rounded-lg bg-slate-50 border border-slate-200/80 flex flex-col justify-between">
              <div>
                <div class="flex items-center justify-between mb-1">
                  <span class="font-mono text-[10px] text-slate-500 font-bold">STAGE 02</span>
                  <span class="material-symbols-outlined text-[#23a274] text-[16px]">rule</span>
                </div>
                <div class="font-bold text-xs text-[#001332] mb-0.5">Rule Engine Ingestion</div>
                <div class="text-[11px] text-slate-500">NLP cross-ref with Land & Faculty Registers.</div>
              </div>
              <div class="mt-2 pt-1 border-t border-slate-200/60">
                <span class="text-[10px] font-bold px-1.5 py-0.2 rounded bg-[#ffdbce] text-[#571a00]">2 Anomaly Flags</span>
              </div>
            </div>

            <!-- Stage 3 (Active) -->
            <div class="p-3 rounded-lg bg-[#ffdad6]/40 border-2 border-[#ba1a1a] flex flex-col justify-between shadow-xs">
              <div>
                <div class="flex items-center justify-between mb-1">
                  <span class="font-mono text-[10px] text-[#ba1a1a] font-bold">STAGE 03 • ACTIVE</span>
                  <span class="material-symbols-outlined text-[#ba1a1a] text-[16px]">warning</span>
                </div>
                <div class="font-bold text-xs text-[#93000a] mb-0.5">Scrutiny Committee</div>
                <div class="text-[11px] text-slate-700">Deficiencies returned: Land Lease & Faculty Cadre.</div>
              </div>
              <div class="mt-2 pt-1 border-t border-red-200">
                <span class="text-[10px] font-bold px-1.5 py-0.2 rounded bg-[#ba1a1a] text-white animate-pulse">Rectification Notice</span>
              </div>
            </div>

            <!-- Stage 4 -->
            <div class="p-3 rounded-lg bg-slate-50 border border-slate-200/80 flex flex-col justify-between opacity-75">
              <div>
                <div class="flex items-center justify-between mb-1">
                  <span class="font-mono text-[10px] text-slate-400 font-bold">STAGE 04</span>
                  <span class="material-symbols-outlined text-slate-400 text-[16px]">pending_actions</span>
                </div>
                <div class="font-bold text-xs text-slate-700 mb-0.5">EVC Inspection</div>
                <div class="text-[11px] text-slate-400">Physical surprise inspection standing by.</div>
              </div>
              <div class="mt-2 pt-1 border-t border-slate-200/60">
                <span class="text-[10px] font-bold px-1.5 py-0.2 rounded bg-slate-200 text-slate-600">Standby (Gate Q3)</span>
              </div>
            </div>

            <!-- Stage 5 -->
            <div class="p-3 rounded-lg bg-slate-50 border border-slate-200/80 flex flex-col justify-between opacity-60">
              <div>
                <div class="flex items-center justify-between mb-1">
                  <span class="font-mono text-[10px] text-slate-400 font-bold">STAGE 05</span>
                  <span class="material-symbols-outlined text-slate-400 text-[16px]">gavel</span>
                </div>
                <div class="font-bold text-xs text-slate-700 mb-0.5">SHC / SAC Appeal</div>
                <div class="text-[11px] text-slate-400">Standing Hearing Committee statutory docket.</div>
              </div>
              <div class="mt-2 pt-1 border-t border-slate-200/60">
                <span class="text-[10px] font-bold px-1.5 py-0.2 rounded bg-slate-200 text-slate-600">Post-EVC Review</span>
              </div>
            </div>
          </div>
        </section>

        <!-- Main Scrutiny Layout -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-5">
          
          <!-- Left 8 Columns: Active Application Scrutiny Checklist -->
          <div class="lg:col-span-8 bg-white rounded-xl border border-slate-200/90 shadow-xs p-5 space-y-4">
            <div class="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <h3 class="font-headline font-bold text-base text-[#001332]">Statutory Scrutiny Checklist · ${activeApp.id}</h3>
                <p class="text-xs text-slate-500">${escapeHtml(activeApp.institution_name)} (${activeApp.permanent_id})</p>
              </div>
              ${renderPill(activeApp.status)}
            </div>

            <div class="space-y-3">
              <div class="p-3.5 rounded-lg border border-slate-200 bg-slate-50/60">
                <div class="flex items-center justify-between">
                  <strong class="text-xs text-[#001332]">1. Land Area & Registered Lease Deed</strong>
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-[#ffdbce] text-[#571a00]">Approaching Expiry</span>
                </div>
                <p class="text-xs text-slate-600 my-1">
                  Sub-Registrar registered deed on file: 12.5 Acres. Registered lease expires on 31-March-2026. Extension deed submission mandatory.
                </p>
                <div class="text-[11px] text-[#0f284e] font-mono font-semibold">Rule: AICTE APH 2026 Chapter I Clause 1.4</div>
              </div>

              <div class="p-3.5 rounded-lg border border-slate-200 bg-slate-50/60">
                <div class="flex items-center justify-between">
                  <strong class="text-xs text-[#001332]">2. Fire & Life Safety Clearance</strong>
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-[#002f1e] text-[#23a274]">Verified</span>
                </div>
                <p class="text-xs text-slate-600 my-1">
                  State Fire Services NOC valid for academic block and hostel complexes. Automatic sprinkler and hydrant test certified.
                </p>
                <div class="text-[11px] text-[#0f284e] font-mono font-semibold">Rule: National Building Code (NBC) Part IV</div>
              </div>

              <div class="p-3.5 rounded-lg border border-slate-200 bg-slate-50/60">
                <div class="flex items-center justify-between">
                  <strong class="text-xs text-[#001332]">3. Faculty Cadre Ratio & Qualification</strong>
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-[#ffdad6] text-[#93000a]">Deficiency Flagged</span>
                </div>
                <p class="text-xs text-slate-600 my-1">
                  Prescribed cadre ratio is 1:2:6. Extracted declaration indicates Professor deficiency in Computer Science department.
                </p>
                <div class="text-[11px] text-[#0f284e] font-mono font-semibold">Rule: AICTE Pay Scales & Cadre Qualifications Regulations</div>
              </div>

              <div class="p-3.5 rounded-lg border border-slate-200 bg-slate-50/60">
                <div class="flex items-center justify-between">
                  <strong class="text-xs text-[#001332]">4. Anti-Ragging Measures & Ombudsman</strong>
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-[#002f1e] text-[#23a274]">Satisfied</span>
                </div>
                <p class="text-xs text-slate-600 my-1">
                  Institution has notified anti-ragging squad, web portal display, and appointed Retired District Judge as student ombudsman.
                </p>
                <div class="text-[11px] text-[#0f284e] font-mono font-semibold">Rule: AICTE Redressal of Grievance Regulations 2019</div>
              </div>
            </div>

            <div class="flex items-center gap-3 pt-3 border-t border-slate-100">
              <button class="px-4 py-2 bg-[#001332] text-white font-semibold text-xs rounded-lg hover:bg-[#0f284e] transition-colors shadow-xs" 
                onclick="ScrutinyModule.approveScrutiny('${activeApp.id}')">
                ✓ Clear Scrutiny Stage
              </button>
              <button class="px-4 py-2 bg-[#ba1a1a] text-white font-semibold text-xs rounded-lg hover:bg-[#93000a] transition-colors shadow-xs" 
                onclick="ScrutinyModule.openDeficiencyNotice('${activeApp.id}')">
                Return with Deficiency Checklist
              </button>
            </div>
          </div>

          <!-- Right 4 Columns: Case Selector & Evidence Documents -->
          <div class="lg:col-span-4 space-y-4">
            
            <div class="bg-white rounded-xl border border-slate-200/90 shadow-xs p-4">
              <h3 class="font-headline font-bold text-sm text-[#001332] pb-2 mb-2 border-b border-slate-100">Scrutiny Queue</h3>
              <div class="space-y-2">
                ${apps.map(a => `
                  <div
                    class="p-3 rounded-lg border transition-all cursor-pointer ${a.id === activeApp.id ? 'border-[#001332] bg-[#eaedff]/60 shadow-xs' : 'border-slate-200 bg-white hover:bg-slate-50'}"
                    onclick="ScrutinyModule.selectApp('${a.id}')"
                  >
                    <div class="flex items-center justify-between font-mono font-bold text-xs text-[#001332]">
                      <span>${a.id}</span>
                      ${renderPill(a.status)}
                    </div>
                    <div class="text-xs font-semibold text-slate-800 mt-1 truncate">${escapeHtml(a.institution_name)}</div>
                    <div class="text-[10px] text-slate-500 mt-0.5">${escapeHtml(a.type)} · Owner: ${escapeHtml(a.owner)}</div>
                  </div>
                `).join("")}
              </div>
            </div>

            <div class="bg-white rounded-xl border border-slate-200/90 shadow-xs p-4">
              <div class="flex items-center justify-between pb-2 mb-2 border-b border-slate-100">
                <h3 class="font-headline font-bold text-sm text-[#001332]">Evidence Documents</h3>
                <button class="text-[11px] font-semibold text-[#0f284e] hover:underline" onclick="App.navigate('verification')">Open Module →</button>
              </div>
              <div class="space-y-2">
                ${docs.map(d => `
                  <div class="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100 text-xs">
                    <div>
                      <div class="font-bold text-[#001332] truncate max-w-[160px]">${escapeHtml(d.name)}</div>
                      <div class="text-[10px] text-slate-500">${escapeHtml(d.document_type)} · ${d.confidence}</div>
                    </div>
                    ${renderPill(d.status)}
                  </div>
                `).join("") || '<p class="text-xs text-slate-400">No documents uploaded.</p>'}
              </div>
            </div>

          </div>
        </div>

      </div>
    `;
  },

  selectApp(id) {
    this.selectedAppId = id;
    App.refresh();
  },

  async approveScrutiny(id) {
    await API.transitionApplication(id, "EVC scheduling", "EVC pending", "Scrutiny Committee", "Scrutiny Committee satisfied with preliminary documents; queued for physical EVC inspection.");
    App.toast("Application cleared scrutiny. Queued for EVC scheduling.");
    App.refresh();
  },

  openForwardEVC(id) {
    App.navigate("evc", { appId: id });
  },

  openDeficiencyNotice(id) {
    const app = localStore.db.applications.find(a => a.id === id);
    App.openModal(
      `Issue Statutory Deficiency Memorandum · ${id}`,
      `
        <p class="text-xs text-slate-600 mb-3">
          The following deficiencies will be formally communicated to <b>${escapeHtml(app.institution_name)}</b> with a 15-day rectification window:
        </p>
        <div class="space-y-2 text-xs mb-3">
          <label class="flex items-center gap-2"><input type="checkbox" checked /> Land lease registered deed approaching expiry (Expires 31-March-2026)</label>
          <label class="flex items-center gap-2"><input type="checkbox" checked /> Cadre ratio deficit: 1 Professor required in Computer Science</label>
          <label class="flex items-center gap-2"><input type="checkbox" /> Fire & Life safety certificate renewal pending</label>
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Scrutiny Officer Observations</label>
          <textarea class="w-full text-xs p-2 rounded-lg border border-slate-200 bg-white" id="deficiency-remarks" rows="3">Institution is required to upload registered lease renewal and ratified faculty appointment order within 15 days.</textarea>
        </div>
      `,
      `
        <button class="px-3 py-1.5 text-xs font-semibold rounded bg-slate-100 text-slate-700 hover:bg-slate-200" onclick="App.closeModal()">Cancel</button>
        <button class="px-3 py-1.5 text-xs font-semibold rounded bg-[#ba1a1a] text-white hover:bg-[#93000a]" onclick="ScrutinyModule.confirmDeficiency('${id}')">Dispatch Deficiency Notice</button>
      `
    );
  },

  async confirmDeficiency(id) {
    const remarks = document.getElementById("deficiency-remarks").value;
    await API.transitionApplication(id, "Re-scrutiny", "Returned for rectification", "Scrutiny Officer", remarks, [
      "Land lease registered deed renewal required",
      "Professor cadre ratio deficit in CSE"
    ]);
    App.closeModal();
    App.toast("Deficiency notice dispatched. Application returned for rectification.");
    App.refresh();
  }
};

window.ScrutinyModule = ScrutinyModule;
