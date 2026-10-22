/**
 * Module 1: Executive Intelligence Command Center
 * "Bharat Civic-Sovereign Tech" Design System
 */
const OverviewModule = {
  async render() {
    const metrics = await API.getDashboardMetrics();
    const sum = metrics.summary || {
      institutions: 8842,
      applications: 8,
      pending_verification: 0,
      compliance_alerts: 1,
      overlapping_cases: 3
    };
    const kpis = metrics.kpis || metrics;
    const totalAppsCount = (sum.applications || kpis.active_applications || 0);
    const queueCount = ((kpis.evc_scheduled || 0) + (kpis.applications_in_active_stages || 0) || (metrics.stage_distribution && (metrics.stage_distribution['Scrutiny'] || 0)) || 2);
    const overlapsCount = (sum.overlapping_cases || kpis.high_priority_and_critical_cases || 0);
    const anomaliesCount = (sum.pending_verification || kpis.documents_awaiting_verification || 0);
    const atRiskCount = (sum.compliance_alerts || kpis.failed_or_overdue_compliance || 0);

    // Applications for the live pipeline table
    const recentApps = await API.getApplications();
    const appList = recentApps.items || recentApps.data || recentApps || [];
    const appRows = appList.slice(0, 6).map(a => `
      <tr class="hover:bg-slate-50/80 transition-colors border-b border-slate-100">
        <td class="py-3 px-3">
          <div class="font-bold text-[#001332] font-mono text-xs">${escapeHtml(a.id)}</div>
          <div class="text-[11px] text-slate-500">${escapeHtml(a.type || a.application_type || 'Approval')}</div>
        </td>
        <td class="py-3 px-3">
          <div class="font-semibold text-[#001332] text-xs">${escapeHtml(a.institution_name || a.name || 'AICTE Institute')}</div>
          <div class="text-[10px] text-slate-400 font-mono">${escapeHtml(a.permanent_id || a.institution_id || '')}</div>
        </td>
        <td class="py-3 px-3">
          <span class="px-2 py-0.5 rounded text-[11px] font-semibold bg-[#eaedff] text-[#001332] border border-[#dae2fd]">
            ${escapeHtml(a.current_stage || a.stage_code || 'SCRUTINY')}
          </span>
        </td>
        <td class="py-3 px-3">
          <div class="flex items-center gap-2">
            <div class="flex-1 bg-slate-200 h-1.5 rounded-full overflow-hidden w-20">
              <div class="bg-[#0f284e] h-full rounded-full" style="width:${a.progress || 35}%"></div>
            </div>
            <span class="text-[11px] font-mono font-bold text-slate-700">${a.progress || 35}%</span>
          </div>
        </td>
        <td class="py-3 px-3">
          ${renderPill(a.status || 'Under Review')}
        </td>
        <td class="py-3 px-3 text-right">
          <button class="px-2.5 py-1 text-xs font-semibold rounded bg-slate-100 text-[#001332] hover:bg-[#001332] hover:text-white transition-all shadow-xs" 
            onclick="App.navigate('applications', { id: '${a.id}' })">
            Inspect →
          </button>
        </td>
      </tr>
    `).join("");

    // Priority alerts
    const compRecords = await API.getCompliance();
    const compList = compRecords.items || compRecords.data || compRecords || [];
    const alerts = compList.filter(c => /overdue|due soon|action|pending/i.test(c.status || '')).slice(0, 4);
    const alertHtml = alerts.map(c => `
      <div class="flex items-start gap-3 py-2.5 border-b border-slate-100 last:border-none">
        <span class="px-1.5 py-0.5 rounded text-[10px] font-bold ${c.status === 'Overdue' ? 'bg-[#ffdad6] text-[#93000a]' : 'bg-[#ffdbce] text-[#571a00]'}">
          !
        </span>
        <div class="flex-1 min-w-0">
          <div class="text-xs font-bold text-[#001332] truncate">${escapeHtml(c.title || c.obligation_name || 'Mandatory Undertaking')}</div>
          <div class="text-[11px] text-slate-500 truncate">${escapeHtml(c.institution_name || c.institution_id || 'Institution')} · Due ${formatDate(c.due_date || c.deadline)}</div>
        </div>
        <button class="px-2 py-0.5 text-[11px] font-semibold rounded bg-slate-100 text-[#001332] hover:bg-slate-200 shrink-0" 
          onclick="App.navigate('compliance', { id: '${c.id}' })">
          Review
        </button>
      </div>
    `).join("") || '<p class="text-xs text-slate-400 py-2">No critical compliance alerts outstanding.</p>';

    // Audit logs
    const auditRes = await API.getAuditLogs();
    const auditList = auditRes.items || auditRes.data || auditRes || [];
    const audits = auditList.slice(0, 4);
    const auditHtml = audits.map(a => `
      <div class="flex items-start gap-3 py-2 border-b border-slate-100 last:border-none">
        <div class="w-6 h-6 rounded bg-[#eaedff] text-[#001332] flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
          ●
        </div>
        <div class="flex-1 min-w-0">
          <div class="text-xs font-semibold text-[#001332] truncate">${escapeHtml(a.action)}</div>
          <div class="text-[11px] text-slate-500 truncate">${escapeHtml(a.details || a.detail || a.entity_id || '')}</div>
          <div class="text-[10px] text-slate-400 font-mono">${escapeHtml(a.actor)} (${escapeHtml(a.role || 'OFFICER')}) · ${escapeHtml(a.created_at || a.time || '')}</div>
        </div>
      </div>
    `).join("") || '<p class="text-xs text-slate-400 py-2">No recent audit log entries.</p>';

    return `
      <div class="space-y-6">
        
        <!-- Sovereign Header & Telemetry Strip -->
        <div class="flex flex-col xl:flex-row xl:items-end justify-between gap-4 pb-2 border-b border-slate-200/80">
          <div class="space-y-1">
            <div class="flex items-center gap-2">
              <span class="font-mono text-xs uppercase tracking-wider text-[#a73a00] font-bold">Apex Regulatory Governance Matrix</span>
              <span class="w-1.5 h-1.5 rounded-full bg-slate-300"></span>
              <span class="font-mono text-xs text-slate-500">Session Cycle: APH 2026–27 (Phase II Scrutiny)</span>
            </div>
            <div class="flex items-baseline gap-2 sm:gap-3 flex-wrap">
              <h1 class="font-headline text-xl sm:text-2xl lg:text-3xl font-extrabold text-[#001332] tracking-tight">National Executive Regulatory Command</h1>
              <span class="font-mono text-[10px] sm:text-[11px] font-bold px-2 py-0.5 rounded bg-[#002f1e] text-[#23a274]">SYNC INTERVAL: 30s REAL-TIME</span>
            </div>
            <p class="text-xs text-slate-600 max-w-4xl">
              Unified ministerial vantage integrating Module 1 (PGRC Grievances), Module 2 (Scrutiny & EVC Workflows), and Module 3 (Forensic OCR & DigiLocker Telemetry) across 11,482 approved institutions.
            </p>
          </div>

          <!-- Quick Action Buttons -->
          <div class="flex flex-wrap items-center gap-2 bg-slate-100/80 p-1.5 rounded-lg border border-slate-200">
            <button class="px-3 py-1.5 bg-[#001332] text-white font-semibold text-xs rounded-md flex items-center gap-1.5 hover:bg-[#0f284e] transition-all shadow-xs" 
              onclick="CSVUtil.downloadCSV('aicte_executive_snapshot.csv', localStore.db.applications)">
              <span class="material-symbols-outlined text-[16px]">file_download</span>
              <span>Cabinet Summary CSV</span>
            </button>
            <button class="px-3 py-1.5 bg-[#fd651e] text-white font-semibold text-xs rounded-md flex items-center gap-1.5 hover:bg-[#a73a00] transition-all shadow-xs" 
              onclick="App.openCreateModal('application')">
              <span class="material-symbols-outlined text-[16px]">add_circle</span>
              <span>Lodgement New Application</span>
            </button>
          </div>
        </div>

        <!-- 1. Executive Bento KPI Metric Tier -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          
          <!-- Card 1: Total Active Applications -->
          <div class="bg-white p-4 rounded-xl border border-slate-200/90 shadow-xs hover:shadow-md transition-all flex flex-col justify-between cursor-pointer" onclick="App.navigate('applications')">
            <div class="flex items-start justify-between">
              <span class="text-[11px] font-bold uppercase tracking-wider text-slate-500">Total Submissions</span>
              <span class="material-symbols-outlined text-[#001332] text-[20px]">account_balance</span>
            </div>
            <div class="my-2">
              <div class="font-headline text-2xl font-extrabold text-[#001332] tracking-tight">${totalAppsCount.toLocaleString()}</div>
              <div class="flex items-center gap-1 mt-0.5">
                <span class="text-[11px] text-[#23a274] font-bold flex items-center">
                  <span class="material-symbols-outlined text-[13px]">trending_up</span> Live
                </span>
                <span class="text-[11px] text-slate-500">Academic Year 2026–27</span>
              </div>
            </div>
            <div class="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden flex">
              <div class="bg-[#001332]" style="width: 68%" title="Cleared"></div>
              <div class="bg-[#a73a00]" style="width: 20%" title="Scrutiny"></div>
              <div class="bg-[#ba1a1a]" style="width: 12%" title="Deficient"></div>
            </div>
            <div class="flex justify-between font-mono text-[10px] text-slate-500 mt-1.5">
              <span>Cleared: ${(kpis.new_approvals_period || 0).toLocaleString()}</span>
              <span>In Review: ${(kpis.applications_in_active_stages || totalAppsCount).toLocaleString()}</span>
            </div>
          </div>

          <!-- Card 2: Scrutiny / EVC Latency -->
          <div class="bg-white p-4 rounded-xl border border-slate-200/90 shadow-xs hover:shadow-md transition-all flex flex-col justify-between cursor-pointer" onclick="App.navigate('scrutiny')">
            <div class="flex items-start justify-between">
              <span class="text-[11px] font-bold uppercase tracking-wider text-slate-500">Scrutiny / EVC Queue</span>
              <span class="material-symbols-outlined text-[#a73a00] text-[20px]">hourglass_top</span>
            </div>
            <div class="my-2">
              <div class="font-headline text-2xl font-extrabold text-[#001332] tracking-tight">${queueCount.toLocaleString()}</div>
              <div class="flex items-center gap-1.5 mt-0.5">
                <span class="text-[10px] px-1.5 py-0.2 rounded bg-[#ffdad6] text-[#93000a] font-bold">${(kpis.evc_scheduled || 0)} Scheduled</span>
                <span class="text-[11px] text-slate-500">SLA Standard: &lt; 7 Days</span>
              </div>
            </div>
            <div>
              <div class="flex justify-between text-[11px] text-slate-500 mb-1">
                <span>EVC Completed</span>
                <span class="font-bold text-[#001332]">${(kpis.evc_completed || 0)} Inspected</span>
              </div>
              <div class="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                <div class="bg-[#0f284e] h-full" style="width: 78%"></div>
              </div>
            </div>
          </div>

          <!-- Card 3: Cross-Bureau Complaint Overlaps -->
          <div class="bg-white p-4 rounded-xl border border-slate-200/90 shadow-xs hover:shadow-md transition-all flex flex-col justify-between cursor-pointer relative overflow-hidden" onclick="App.navigate('coordination')">
            <div class="absolute top-0 left-0 w-full h-1 bg-[#fd651e]"></div>
            <div class="flex items-start justify-between">
              <span class="text-[11px] font-bold uppercase tracking-wider text-[#a73a00]">Bureau Clashes</span>
              <span class="material-symbols-outlined text-[#fd651e] text-[20px]">crisis_alert</span>
            </div>
            <div class="my-2">
              <div class="font-headline text-2xl font-extrabold text-[#a73a00] tracking-tight">${overlapsCount.toLocaleString()}</div>
              <div class="text-[11px] text-slate-600 font-semibold mt-0.5">PGRC ⟷ Regulation Bureau</div>
            </div>
            <div class="bg-slate-50 p-1.5 rounded flex items-center justify-between border border-slate-100">
              <span class="text-[11px] text-slate-600">Active Grievances</span>
              <span class="font-mono text-[10px] font-bold text-[#a73a00] bg-[#ffdbce] px-1.5 py-0.2 rounded">${(kpis.active_complaints || 0)} Tracked</span>
            </div>
          </div>

          <!-- Card 4: Document Anomaly & Forensic OCR -->
          <div class="bg-white p-4 rounded-xl border border-slate-200/90 shadow-xs hover:shadow-md transition-all flex flex-col justify-between cursor-pointer" onclick="App.navigate('verification')">
            <div class="flex items-start justify-between">
              <span class="text-[11px] font-bold uppercase tracking-wider text-slate-500">Document Verification Queue</span>
              <span class="material-symbols-outlined text-[#001332] text-[20px]">document_scanner</span>
            </div>
            <div class="my-2">
              <div class="font-headline text-2xl font-extrabold text-[#001332] tracking-tight">${anomaliesCount.toLocaleString()}</div>
              <div class="text-[11px] text-slate-500 mt-0.5">Awaiting Statutory Verification</div>
            </div>
            <div class="flex items-center justify-between text-[11px] pt-1 border-t border-slate-100">
              <span class="font-mono text-[#a73a00] font-bold">${(kpis.document_validity_critical || 0)} Expiry Critical</span>
              <a href="https://documentverify-two.vercel.app/" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation();" class="text-[10px] font-semibold text-[#a73a00] hover:text-[#8f3200] flex items-center gap-0.5" title="Open Document Verification in new tab">
                <span>Document Verification</span>
                <span class="material-symbols-outlined text-[12px]">open_in_new</span>
              </a>
            </div>
          </div>

          <!-- Card 5: Time-Bound Undertakings at Risk -->
          <div class="bg-white p-4 rounded-xl border border-slate-200/90 shadow-xs hover:shadow-md transition-all flex flex-col justify-between cursor-pointer" onclick="App.navigate('compliance')">
            <div class="flex items-start justify-between">
              <span class="text-[11px] font-bold uppercase tracking-wider text-[#ba1a1a]">Undertakings At Risk</span>
              <span class="material-symbols-outlined text-[#ba1a1a] text-[20px]">event_busy</span>
            </div>
            <div class="my-2">
              <div class="font-headline text-2xl font-extrabold text-[#ba1a1a] tracking-tight">${atRiskCount.toLocaleString()}</div>
              <div class="flex items-center gap-1 mt-0.5">
                <span class="text-[10px] font-semibold px-1.5 py-0.2 rounded bg-slate-100 text-slate-700">&lt; 60 Days Expiry</span>
              </div>
            </div>
            <div class="flex items-center justify-between text-[11px] pt-1 border-t border-slate-100">
              <span class="text-slate-600">Pending Actions</span>
              <span class="font-mono text-[10px] font-bold text-[#ba1a1a] bg-[#ffdad6] px-1.5 py-0.2 rounded">${(kpis.undertakings_breached || 0)} Breached</span>
            </div>
          </div>
        </div>

        <!-- Active Priority Regulatory Advisory Banner -->
        <div class="bg-[#eaedff]/60 rounded-xl p-3.5 sm:p-4 border border-[#dae2fd] shadow-xs flex flex-col lg:flex-row lg:items-center justify-between gap-3 sm:gap-4">
          <div class="flex items-start gap-3">
            <div class="w-9 h-9 sm:w-10 sm:h-10 rounded-lg bg-[#0f284e] text-white flex items-center justify-center shrink-0 shadow-sm mt-0.5 sm:mt-0">
              <span class="material-symbols-outlined text-[20px] sm:text-[22px]">balance</span>
            </div>
            <div class="space-y-1">
              <div class="flex flex-wrap items-center gap-1.5 sm:gap-2">
                <span class="font-headline font-bold text-xs sm:text-sm text-[#001332]">Priority Regulatory Attention: Gurugram Institute of Technology & Management</span>
                <span class="font-mono text-[10px] sm:text-[11px] px-2 py-0.5 rounded bg-white text-[#001332] font-bold border border-slate-200">PID: 1-10482931</span>
                <span class="text-[9px] sm:text-[10px] px-2 py-0.5 rounded bg-[#ffdad6] text-[#93000a] font-bold">Active Coordinated Review</span>
              </div>
              <p class="text-[11px] sm:text-xs text-slate-600 leading-relaxed">
                Registered land deed lease expires 31-March-2027. Concurrently flagged under PGRC Grievance #GR-2026-904 for infrastructure expansion scrutiny. Clearance pending review across Regulation Bureau (RB).
              </p>
            </div>
          </div>
          <div class="flex flex-wrap sm:flex-nowrap items-center gap-2 shrink-0 w-full lg:w-auto pt-2 lg:pt-0 border-t border-[#dae2fd]/60 lg:border-t-0">
            <button class="flex-1 sm:flex-initial px-3 py-1.5 bg-white text-[#001332] font-semibold text-xs rounded-md shadow-xs hover:bg-slate-100 border border-slate-200 transition-colors flex items-center justify-center gap-1.5" 
              onclick="App.navigate('digitalTwin', { id: 'INST-10482' })">
              <span class="material-symbols-outlined text-[16px]">visibility</span>
              <span>Digital Twin Dossier</span>
            </button>
            <button class="flex-1 sm:flex-initial px-3 py-1.5 bg-[#a73a00] text-white font-semibold text-xs rounded-md shadow-xs hover:bg-[#fd651e] transition-colors flex items-center justify-center gap-1.5" 
              onclick="App.navigate('coordination')">
              <span class="material-symbols-outlined text-[16px]">gavel</span>
              <span>Summon Hearing</span>
            </button>
          </div>
        </div>

        <!-- 2. National Regulatory Regional Directorate Processing Velocity -->
        <div class="bg-white rounded-xl border border-slate-200/90 shadow-xs p-5 space-y-4">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-100">
            <div>
              <h2 class="font-headline font-bold text-base text-[#001332]">Regional Directorate Processing Velocity</h2>
              <p class="text-xs text-slate-500">Statutory compliance benchmarks under AICTE Approval Process Handbook (APH 2026–27)</p>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-[11px] font-mono text-slate-500 bg-slate-100 px-2.5 py-1 rounded-md border border-slate-200">
                SLA Standard: &lt; 7 Days
              </span>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs font-sans">
              <thead class="bg-slate-50 text-[11px] font-bold uppercase tracking-wider text-slate-500 border-b border-slate-200">
                <tr>
                  <th class="py-2.5 px-3">Regional Bureau & Office</th>
                  <th class="py-2.5 px-3">Submissions</th>
                  <th class="py-2.5 px-3">Throughput Velocity</th>
                  <th class="py-2.5 px-3">Avg Latency</th>
                  <th class="py-2.5 px-3">EVC Completion</th>
                  <th class="py-2.5 px-3 text-right">Flagged %</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 font-medium">
                <tr class="hover:bg-slate-50/60 transition-colors">
                  <td class="py-3 px-3">
                    <div class="font-bold text-[#001332]">NWRO — Chandigarh</div>
                    <div class="text-[11px] text-slate-500">Punjab, Haryana, HP, J&K, Ladakh</div>
                  </td>
                  <td class="py-3 px-3 font-mono font-bold">2,314</td>
                  <td class="py-3 px-3">
                    <div class="w-36">
                      <div class="flex justify-between font-mono text-[10px] mb-1">
                        <span>72.4%</span>
                        <span class="text-slate-400">1,675 cleared</span>
                      </div>
                      <div class="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                        <div class="bg-[#001332] h-full" style="width: 72.4%"></div>
                      </div>
                    </div>
                  </td>
                  <td class="py-3 px-3 font-mono">6.2 Days</td>
                  <td class="py-3 px-3">
                    <span class="px-2 py-0.5 rounded-full bg-[#002f1e] text-[#23a274] text-[10px] font-bold">91.8% Done</span>
                  </td>
                  <td class="py-3 px-3 text-right font-mono text-[#a73a00] font-bold">2.4%</td>
                </tr>

                <tr class="hover:bg-slate-50/60 transition-colors">
                  <td class="py-3 px-3">
                    <div class="font-bold text-[#001332]">SRO — Chennai</div>
                    <div class="text-[11px] text-slate-500">Tamil Nadu, Puducherry, A&N</div>
                  </td>
                  <td class="py-3 px-3 font-mono font-bold">3,490</td>
                  <td class="py-3 px-3">
                    <div class="w-36">
                      <div class="flex justify-between font-mono text-[10px] mb-1">
                        <span>84.1%</span>
                        <span class="text-slate-400">2,935 cleared</span>
                      </div>
                      <div class="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                        <div class="bg-[#001332] h-full" style="width: 84.1%"></div>
                      </div>
                    </div>
                  </td>
                  <td class="py-3 px-3 font-mono text-[#23a274] font-bold">4.8 Days</td>
                  <td class="py-3 px-3">
                    <span class="px-2 py-0.5 rounded-full bg-[#002f1e] text-[#23a274] text-[10px] font-bold">96.2% Done</span>
                  </td>
                  <td class="py-3 px-3 text-right font-mono text-slate-600 font-bold">1.1%</td>
                </tr>

                <tr class="hover:bg-slate-50/60 transition-colors">
                  <td class="py-3 px-3">
                    <div class="font-bold text-[#001332]">WRO — Mumbai</div>
                    <div class="text-[11px] text-slate-500">Maharashtra, Goa, DNH & DD</div>
                  </td>
                  <td class="py-3 px-3 font-mono font-bold">2,880</td>
                  <td class="py-3 px-3">
                    <div class="w-36">
                      <div class="flex justify-between font-mono text-[10px] mb-1">
                        <span>61.2%</span>
                        <span class="text-slate-400">1,762 cleared</span>
                      </div>
                      <div class="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                        <div class="bg-[#fd651e] h-full" style="width: 61.2%"></div>
                      </div>
                    </div>
                  </td>
                  <td class="py-3 px-3 font-mono text-[#a73a00] font-bold">11.4 Days</td>
                  <td class="py-3 px-3">
                    <span class="px-2 py-0.5 rounded-full bg-[#ffdbce] text-[#571a00] text-[10px] font-bold">68.4% Done</span>
                  </td>
                  <td class="py-3 px-3 text-right font-mono text-[#ba1a1a] font-bold">5.8%</td>
                </tr>

                <tr class="hover:bg-slate-50/60 transition-colors">
                  <td class="py-3 px-3">
                    <div class="font-bold text-[#001332]">SWRO — Bengaluru</div>
                    <div class="text-[11px] text-slate-500">Karnataka, Kerala, Lakshadweep</div>
                  </td>
                  <td class="py-3 px-3 font-mono font-bold">2,150</td>
                  <td class="py-3 px-3">
                    <div class="w-36">
                      <div class="flex justify-between font-mono text-[10px] mb-1">
                        <span>79.5%</span>
                        <span class="text-slate-400">1,709 cleared</span>
                      </div>
                      <div class="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                        <div class="bg-[#001332] h-full" style="width: 79.5%"></div>
                      </div>
                    </div>
                  </td>
                  <td class="py-3 px-3 font-mono text-[#23a274] font-bold">5.3 Days</td>
                  <td class="py-3 px-3">
                    <span class="px-2 py-0.5 rounded-full bg-[#002f1e] text-[#23a274] text-[10px] font-bold">94.0% Done</span>
                  </td>
                  <td class="py-3 px-3 text-right font-mono text-slate-600 font-bold">1.8%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 3. Workflow Table & Intelligence Panels Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-5">
          
          <!-- Left 8 Columns: Live Approval Register -->
          <div class="lg:col-span-8 bg-white rounded-xl border border-slate-200/90 shadow-xs p-5 space-y-4">
            <div class="flex items-center justify-between pb-2 border-b border-slate-100">
              <div>
                <h3 class="font-headline font-bold text-base text-[#001332]">Approval Workflow Pipeline</h3>
                <p class="text-xs text-slate-500">Applications undergoing statutory scrutiny & EVC verification</p>
              </div>
              <button class="px-2.5 py-1 text-xs font-semibold rounded bg-slate-100 text-[#001332] hover:bg-slate-200 transition-colors" 
                onclick="App.navigate('applications')">
                View Full Register →
              </button>
            </div>

            <!-- Stage distribution meter -->
            <div class="grid grid-cols-2 sm:grid-cols-5 gap-2 pb-2">
              ${[
                ['Validation', metrics.stage_distribution['Preliminary validation'] || 0, 'bg-slate-200 text-slate-700'],
                ['Scrutiny', (metrics.stage_distribution['Scrutiny'] || 0) + (metrics.stage_distribution['Re-scrutiny'] || 0), 'bg-[#eaedff] text-[#001332]'],
                ['EVC Visits', (metrics.stage_distribution['EVC scheduling'] || 0) + (metrics.stage_distribution['EVC completed'] || 0), 'bg-[#ffdbce] text-[#571a00]'],
                ['SAC/SHC', metrics.stage_distribution['SAC/SHC review'] || 0, 'bg-[#ffdad6] text-[#93000a]'],
                ['Disposition', metrics.stage_distribution['Authorized disposition'] || 0, 'bg-[#002f1e] text-[#23a274]']
              ].map(([stg, count, cls]) => `
                <div class="p-2 rounded-lg bg-slate-50 border border-slate-100 text-center">
                  <div class="text-[10px] text-slate-500 uppercase font-semibold">${stg}</div>
                  <div class="font-mono font-bold text-sm text-[#001332] mt-0.5">${count}</div>
                </div>
              `).join("")}
            </div>

            <div class="overflow-x-auto">
              <table class="w-full text-left text-xs font-sans">
                <thead class="bg-slate-50 text-[11px] font-bold uppercase tracking-wider text-slate-500 border-b border-slate-200">
                  <tr>
                    <th class="py-2.5 px-3">APPLICATION</th>
                    <th class="py-2.5 px-3">INSTITUTION</th>
                    <th class="py-2.5 px-3">STAGE</th>
                    <th class="py-2.5 px-3">PROGRESS</th>
                    <th class="py-2.5 px-3">STATUS</th>
                    <th class="py-2.5 px-3 text-right">ACTION</th>
                  </tr>
                </thead>
                <tbody>
                  ${appRows}
                </tbody>
              </table>
            </div>
          </div>

          <!-- Right 4 Columns: Priority Alerts & Bureau Stream -->
          <div class="lg:col-span-4 space-y-4">
            
            <!-- Priority Administrative Alerts -->
            <div class="bg-white rounded-xl border border-slate-200/90 shadow-xs p-4">
              <div class="flex items-center justify-between pb-2 mb-2 border-b border-slate-100">
                <h3 class="font-headline font-bold text-sm text-[#001332]">Priority Alerts</h3>
                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-[#ffdbce] text-[#571a00]">
                  ${alerts.length} Immediate
                </span>
              </div>
              <div>
                ${alertHtml}
              </div>
            </div>

            <!-- Cross-Bureau Coordination Radar -->
            <div class="bg-white rounded-xl border border-slate-200/90 shadow-xs p-4">
              <div class="flex items-center justify-between pb-2 mb-2 border-b border-slate-100">
                <h3 class="font-headline font-bold text-sm text-[#001332]">Bureau Coordination</h3>
                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-[#eaedff] text-[#001332]">
                  ${sum.overlapping_cases} Clashes
                </span>
              </div>
              <div class="bg-[#eff6ff] border border-[#bfdbfe] rounded-lg p-3 space-y-1 mb-3">
                <div class="flex items-center gap-1.5 font-bold text-[#1e40af] text-xs">
                  <span class="material-symbols-outlined text-[16px]">crisis_alert</span>
                  <span>Overlap Signal Active</span>
                </div>
                <p class="text-[11px] text-[#1e3a8a] leading-relaxed">
                  Public grievance <b>PGRC-26-01842</b> correlates with Regulation Bureau audit <b>RB-26-00917</b> regarding excess student admissions at Noida Institute.
                </p>
              </div>
              <button class="w-full py-1.5 bg-[#001332] text-white font-semibold text-xs rounded-md hover:bg-[#0f284e] transition-colors flex items-center justify-center gap-1.5 shadow-xs" 
                onclick="App.navigate('coordination')">
                <span>Open Coordination Workspace</span>
                <span class="material-symbols-outlined text-[14px]">arrow_forward</span>
              </button>
            </div>

            <!-- Recent Governance Audit Trail -->
            <div class="bg-white rounded-xl border border-slate-200/90 shadow-xs p-4">
              <div class="flex items-center justify-between pb-2 mb-2 border-b border-slate-100">
                <h3 class="font-headline font-bold text-sm text-[#001332]">Recent Audit Trail</h3>
                <button class="text-[11px] font-semibold text-[#0f284e] hover:underline" onclick="App.navigate('audit')">Full Trail →</button>
              </div>
              <div class="space-y-1">
                ${auditHtml}
              </div>
            </div>

          </div>
        </div>

      </div>
    `;
  }
};

window.OverviewModule = OverviewModule;
