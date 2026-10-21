/**
 * Module 9: Complaints and Grievances Intelligence (Module 1 in Reference)
 * "Bharat Civic-Sovereign Tech" Design System
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
      <tr class="hover:bg-slate-50/80 transition-colors border-b border-slate-100">
        <td class="py-3 px-3">
          <div class="font-bold text-[#001332] font-mono text-xs">${escapeHtml(c.id)}</div>
          <div class="text-[10px] text-slate-400 font-mono">${formatDate(c.received_date)}</div>
        </td>
        <td class="py-3 px-3">
          <div class="font-semibold text-[#001332] text-xs">${escapeHtml(c.institution_name)}</div>
          <div class="text-[11px] text-slate-500">${escapeHtml(c.channel || 'CPGRAMS')}</div>
        </td>
        <td class="py-3 px-3">
          <span class="px-2 py-0.5 rounded text-[11px] font-semibold bg-[#eaedff] text-[#001332] border border-[#dae2fd]">
            ${escapeHtml(c.bureau)}
          </span>
        </td>
        <td class="py-3 px-3 max-w-xs">
          <div class="font-semibold text-[#001332] text-xs">${escapeHtml(c.category)}</div>
          <div class="text-[11px] text-slate-600 line-clamp-2">${escapeHtml(c.summary)}</div>
        </td>
        <td class="py-3 px-3">
          <div class="text-xs text-slate-700">${escapeHtml(c.assigned_to)}</div>
        </td>
        <td class="py-3 px-3">
          ${renderPill(c.status)}
        </td>
        <td class="py-3 px-3">
          ${c.related_case_id ? `
            <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-[#ffdbce] text-[#571a00] border border-[#ffb599] cursor-pointer hover:bg-[#ffb599] transition-colors" onclick="App.navigate('coordination')">
              <span class="material-symbols-outlined text-[12px]">link</span>
              <span>Linked: ${escapeHtml(c.related_case_id)}</span>
            </span>
          ` : '<span class="text-slate-300 font-mono text-xs">—</span>'}
        </td>
        <td class="py-3 px-3 text-right">
          <div class="flex items-center justify-end gap-1.5">
            <button class="px-2 py-1 text-xs font-semibold rounded bg-slate-100 text-[#001332] hover:bg-slate-200 transition-colors" 
              onclick="ComplaintsModule.openTransferModal('${c.id}')">
              Transfer
            </button>
            <button class="px-2 py-1 text-xs font-semibold rounded bg-[#001332] text-white hover:bg-[#0f284e] transition-colors shadow-xs" 
              onclick="ComplaintsModule.openDisposeModal('${c.id}')">
              Dispose
            </button>
          </div>
        </td>
      </tr>
    `).join("");

    const openCount = list.filter(c => !/closed|disposed/i.test(c.status)).length;
    const overlapCount = list.filter(c => c.related_case_id).length;

    return `
      <div class="space-y-6">
        
        <!-- Sovereign Header -->
        <div class="flex flex-col xl:flex-row xl:items-end justify-between gap-4 pb-2 border-b border-slate-200/80">
          <div class="space-y-1">
            <div class="flex items-center gap-2">
              <span class="font-mono text-xs uppercase tracking-wider text-[#a73a00] font-bold">Institutional Grievance Intelligence</span>
              <span class="w-1.5 h-1.5 rounded-full bg-slate-300"></span>
              <span class="font-mono text-xs text-slate-500">Cross-Bureau Coordination Protocol PS-26264</span>
            </div>
            <div class="flex items-baseline gap-3 flex-wrap">
              <h1 class="font-headline text-2xl lg:text-3xl font-extrabold text-[#001332] tracking-tight">Central Complaints & Grievance Registry</h1>
              <span class="font-mono text-[11px] font-bold px-2 py-0.5 rounded bg-[#002f1e] text-[#23a274]">INSPECTION GATEWAY: SYNCHRONIZED</span>
            </div>
            <p class="text-xs text-slate-600 max-w-4xl">
              Unifies grievance intake across Public Grievance Redressal Cell (PGRC), Regulation Bureau, and Regional Directorates with automated cross-bureau overlap detection.
            </p>
          </div>

          <div class="flex flex-wrap items-center gap-2 bg-slate-100/80 p-1.5 rounded-lg border border-slate-200">
            <button class="px-3 py-1.5 bg-white text-[#001332] font-semibold text-xs rounded-md shadow-xs hover:bg-slate-50 border border-slate-200 transition-colors flex items-center gap-1.5" 
              onclick="CSVUtil.downloadCSV('aicte_complaints_register.csv', localStore.db.complaints)">
              <span class="material-symbols-outlined text-[16px]">file_download</span>
              <span>Export CSV</span>
            </button>
            <button class="px-3 py-1.5 bg-[#001332] text-white font-semibold text-xs rounded-md shadow-xs hover:bg-[#0f284e] transition-colors flex items-center gap-1.5" 
              onclick="App.navigate('coordination')">
              <span class="material-symbols-outlined text-[16px]">alt_route</span>
              <span>Bureau Coordination</span>
            </button>
            <button class="px-3 py-1.5 bg-[#fd651e] text-white font-semibold text-xs rounded-md shadow-xs hover:bg-[#a73a00] transition-colors flex items-center gap-1.5" 
              onclick="ComplaintsModule.openRegisterModal()">
              <span class="material-symbols-outlined text-[16px]">add_circle</span>
              <span>Register Grievance</span>
            </button>
          </div>
        </div>

        <!-- Overlap Intelligence Banner -->
        <div class="bg-[#eaedff]/60 rounded-xl p-4 border border-[#dae2fd] shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div class="flex items-start gap-3">
            <div class="w-10 h-10 rounded-lg bg-[#a73a00] text-white flex items-center justify-center shrink-0 shadow-sm">
              <span class="material-symbols-outlined text-[22px]">crisis_alert</span>
            </div>
            <div class="space-y-0.5">
              <div class="flex flex-wrap items-center gap-2">
                <span class="font-headline font-bold text-sm text-[#001332]">Statutory Overlap Intelligence Detector</span>
                <span class="px-2 py-0.5 rounded bg-[#ffdad6] text-[#93000a] font-bold text-[10px]">142 Active Inquiries Clashed</span>
              </div>
              <p class="text-xs text-slate-600">
                PGRC citizen complaints and Regulation Bureau surprise audits are checked against the shared Institution Digital Twin to prevent conflicting dispositions or unauthorized approvals during ongoing inquiries.
              </p>
            </div>
          </div>
          <button class="px-3 py-1.5 bg-[#001332] text-white font-semibold text-xs rounded-md shadow-xs hover:bg-[#0f284e] transition-colors flex items-center gap-1.5 shrink-0" 
            onclick="App.navigate('coordination')">
            <span>View Clashes Matrix</span>
            <span class="material-symbols-outlined text-[14px]">arrow_forward</span>
          </button>
        </div>

        <!-- Bento KPI Grid -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div class="bg-white p-4 rounded-xl border border-slate-200/90 shadow-xs flex flex-col justify-between">
            <div class="flex items-start justify-between">
              <span class="text-[11px] font-bold uppercase tracking-wider text-slate-500">Open Grievances</span>
              <span class="material-symbols-outlined text-[#001332] text-[20px]">mark_email_unread</span>
            </div>
            <div class="my-2">
              <div class="font-headline text-2xl font-extrabold text-[#001332] tracking-tight">${openCount}</div>
              <div class="text-[11px] text-slate-500 mt-0.5">Active investigation files</div>
            </div>
            <div class="w-full bg-slate-100 h-1 rounded-full overflow-hidden">
              <div class="bg-[#001332] h-full" style="width: 65%"></div>
            </div>
          </div>

          <div class="bg-white p-4 rounded-xl border border-slate-200/90 shadow-xs flex flex-col justify-between">
            <div class="flex items-start justify-between">
              <span class="text-[11px] font-bold uppercase tracking-wider text-[#a73a00]">Overlapping Cases</span>
              <span class="material-symbols-outlined text-[#a73a00] text-[20px]">alt_route</span>
            </div>
            <div class="my-2">
              <div class="font-headline text-2xl font-extrabold text-[#a73a00] tracking-tight">${overlapCount}</div>
              <div class="text-[11px] text-slate-500 mt-0.5">Cross-bureau correlation detected</div>
            </div>
            <div class="w-full bg-slate-100 h-1 rounded-full overflow-hidden">
              <div class="bg-[#a73a00] h-full" style="width: 80%"></div>
            </div>
          </div>

          <div class="bg-white p-4 rounded-xl border border-slate-200/90 shadow-xs flex flex-col justify-between">
            <div class="flex items-start justify-between">
              <span class="text-[11px] font-bold uppercase tracking-wider text-slate-500">Participating Bureaus</span>
              <span class="material-symbols-outlined text-[#001332] text-[20px]">corporate_fare</span>
            </div>
            <div class="my-2">
              <div class="font-headline text-2xl font-extrabold text-[#001332] tracking-tight">${new Set(list.map(c => c.bureau)).size}</div>
              <div class="text-[11px] text-slate-500 mt-0.5">Coordinating administrative wings</div>
            </div>
            <div class="w-full bg-slate-100 h-1 rounded-full overflow-hidden">
              <div class="bg-[#0f284e] h-full" style="width: 100%"></div>
            </div>
          </div>

          <div class="bg-white p-4 rounded-xl border border-slate-200/90 shadow-xs flex flex-col justify-between">
            <div class="flex items-start justify-between">
              <span class="text-[11px] font-bold uppercase tracking-wider text-[#23a274]">Avg Disposal SLA</span>
              <span class="material-symbols-outlined text-[#23a274] text-[20px]">timer</span>
            </div>
            <div class="my-2">
              <div class="font-headline text-2xl font-extrabold text-[#23a274] tracking-tight">14 Days</div>
              <div class="text-[11px] text-slate-500 mt-0.5">Citizen charter compliance benchmark</div>
            </div>
            <div class="w-full bg-slate-100 h-1 rounded-full overflow-hidden">
              <div class="bg-[#23a274] h-full" style="width: 88%"></div>
            </div>
          </div>
        </div>

        <!-- Complaints Table Container -->
        <div class="bg-white rounded-xl border border-slate-200/90 shadow-xs p-5 space-y-4">
          
          <!-- Filter Controls -->
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-2 border-b border-slate-100">
            <div class="flex-1 max-w-md relative">
              <span class="material-symbols-outlined absolute left-3 top-2 text-slate-400 text-[18px]">search</span>
              <input
                class="w-full pl-9 pr-4 py-1.5 text-xs rounded-lg border border-slate-200 bg-slate-50/80 focus:bg-white focus:outline-none focus:border-[#001332] focus:ring-1 focus:ring-[#001332] transition-all placeholder:text-slate-400"
                placeholder="Search complaint ID, institution name, or summary…"
                value="${escapeHtml(this.state.search)}"
                oninput="ComplaintsModule.handleSearch(this.value)"
              />
            </div>
            <div class="flex flex-wrap items-center gap-2">
              <select class="text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none" 
                onchange="ComplaintsModule.handleFilter('bureau', this.value)">
                <option value="">All Bureaus / Cells</option>
                <option value="PGRC" ${this.state.bureau === 'PGRC' ? 'selected' : ''}>PGRC</option>
                <option value="Regulation Bureau" ${this.state.bureau === 'Regulation Bureau' ? 'selected' : ''}>Regulation Bureau</option>
                <option value="Regional Office" ${this.state.bureau === 'Regional Office' ? 'selected' : ''}>Regional Office</option>
                <option value="Approval Bureau" ${this.state.bureau === 'Approval Bureau' ? 'selected' : ''}>Approval Bureau</option>
              </select>
              <select class="text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none" 
                onchange="ComplaintsModule.handleFilter('status', this.value)">
                <option value="">All Statuses</option>
                <option value="Received" ${this.state.status === 'Received' ? 'selected' : ''}>Received</option>
                <option value="Assigned" ${this.state.status === 'Assigned' ? 'selected' : ''}>Assigned</option>
                <option value="Under process" ${this.state.status === 'Under process' ? 'selected' : ''}>Under process</option>
                <option value="Awaiting information" ${this.state.status === 'Awaiting information' ? 'selected' : ''}>Awaiting information</option>
                <option value="Disposed or closed" ${this.state.status === 'Disposed or closed' ? 'selected' : ''}>Disposed or closed</option>
              </select>
              <span class="text-xs text-slate-500 font-mono pl-2"><b>${filtered.length}</b> cases</span>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs font-sans">
              <thead class="bg-slate-50 text-[11px] font-bold uppercase tracking-wider text-slate-500 border-b border-slate-200">
                <tr>
                  <th class="py-2.5 px-3">CASE ID</th>
                  <th class="py-2.5 px-3">INSTITUTION</th>
                  <th class="py-2.5 px-3">BUREAU / CELL</th>
                  <th class="py-2.5 px-3">CATEGORY & SUMMARY</th>
                  <th class="py-2.5 px-3">INVESTIGATOR</th>
                  <th class="py-2.5 px-3">STATUS</th>
                  <th class="py-2.5 px-3">CROSS-BUREAU LINK</th>
                  <th class="py-2.5 px-3 text-right">ACTIONS</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 font-medium">
                ${rows || '<tr><td colspan="8" class="text-center py-8 text-slate-400">No complaints found matching filters.</td></tr>'}
              </tbody>
            </table>
          </div>
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
        <form id="create-complaint-form" class="space-y-4">
          <div>
            <label class="block text-xs font-bold text-slate-700 mb-1">Institution Concerned *</label>
            <select class="w-full text-xs p-2 rounded-lg border border-slate-200 bg-white" id="cplt-inst-id" required>
              ${localStore.db.institutions.map(i => `<option value="${i.id}">${escapeHtml(i.name)} (${i.permanent_id})</option>`).join("")}
            </select>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-bold text-slate-700 mb-1">Receiving Bureau / Cell *</label>
              <select class="w-full text-xs p-2 rounded-lg border border-slate-200 bg-white" id="cplt-bureau">
                <option>PGRC</option>
                <option>Regulation Bureau</option>
                <option>Regional Office</option>
                <option>Approval Bureau</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-700 mb-1">Category *</label>
              <select class="w-full text-xs p-2 rounded-lg border border-slate-200 bg-white" id="cplt-category">
                <option>Student Admission & Intake</option>
                <option>Faculty & Staff Grievance</option>
                <option>Fee Refund / Overcharging</option>
                <option>Infrastructure Deficiency</option>
                <option>Institutional Records Discrepancy</option>
              </select>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-bold text-slate-700 mb-1">Intake Channel</label>
              <select class="w-full text-xs p-2 rounded-lg border border-slate-200 bg-white" id="cplt-channel">
                <option>Central Grievance Portal (CPGRAMS)</option>
                <option>Online Grievance Submission</option>
                <option>Internal Audit Alert</option>
                <option>Regional Office Referral</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-700 mb-1">Assigned Investigator</label>
              <input class="w-full text-xs p-2 rounded-lg border border-slate-200 bg-white" id="cplt-owner" value="M. Joshi (Grievance Officer)" />
            </div>
          </div>
          <div>
            <label class="block text-xs font-bold text-slate-700 mb-1">Grievance Summary *</label>
            <textarea class="w-full text-xs p-2 rounded-lg border border-slate-200 bg-white" id="cplt-summary" rows="3" required placeholder="Clear summary of allegations or audit discrepancy..."></textarea>
          </div>
        </form>
      `,
      `
        <button class="px-3 py-1.5 text-xs font-semibold rounded bg-slate-100 text-slate-700 hover:bg-slate-200" onclick="App.closeModal()">Cancel</button>
        <button class="px-3 py-1.5 text-xs font-semibold rounded bg-[#001332] text-white hover:bg-[#0f284e]" onclick="ComplaintsModule.confirmRegister()">Register Dossier</button>
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
        <div class="text-xs mb-3 text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
          <div><b>Case:</b> ${c.id} (${escapeHtml(c.bureau)})</div>
          <div><b>Institution:</b> ${escapeHtml(c.institution_name)}</div>
        </div>
        <div class="space-y-3">
          <div>
            <label class="block text-xs font-bold text-slate-700 mb-1">Transfer To Bureau / Cell *</label>
            <select class="w-full text-xs p-2 rounded-lg border border-slate-200 bg-white" id="transfer-bureau">
              <option>Regulation Bureau</option>
              <option>Approval Bureau</option>
              <option>PGRC</option>
              <option>Regional Office</option>
              <option>Central Vigilance Cell</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-bold text-slate-700 mb-1">Transfer Rationale</label>
            <textarea class="w-full text-xs p-2 rounded-lg border border-slate-200 bg-white" id="transfer-reason" rows="2">Transferred for coordinated regulatory audit.</textarea>
          </div>
        </div>
      `,
      `
        <button class="px-3 py-1.5 text-xs font-semibold rounded bg-slate-100 text-slate-700 hover:bg-slate-200" onclick="App.closeModal()">Cancel</button>
        <button class="px-3 py-1.5 text-xs font-semibold rounded bg-[#001332] text-white hover:bg-[#0f284e]" onclick="ComplaintsModule.confirmTransfer('${id}')">Execute Transfer</button>
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
        <div class="text-xs mb-3 text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
          <div><b>Summary:</b> ${escapeHtml(c.summary)}</div>
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">Final Disposal Order / Resolution Notes *</label>
          <textarea class="w-full text-xs p-2 rounded-lg border border-slate-200 bg-white" id="disposal-notes" rows="4" placeholder="Record inquiry outcome, compliance deed verified, or corrective directives issued..."></textarea>
        </div>
      `,
      `
        <button class="px-3 py-1.5 text-xs font-semibold rounded bg-slate-100 text-slate-700 hover:bg-slate-200" onclick="App.closeModal()">Cancel</button>
        <button class="px-3 py-1.5 text-xs font-semibold rounded bg-[#001332] text-white hover:bg-[#0f284e]" onclick="ComplaintsModule.confirmDispose('${id}')">Disposed & Close File</button>
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
