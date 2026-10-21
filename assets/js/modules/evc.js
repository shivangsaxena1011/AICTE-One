/**
 * Module 6: EVC Scheduling & Pendency Workspace
 */
const EVCModule = {
  viewMode: "table", // "table" or "calendar"

  async render(params = {}) {
    const schedules = localStore.db.evc_schedules;
    const awaitingScheduling = localStore.db.applications.filter(a => a.current_stage === "EVC scheduling");

    const rows = schedules.map(s => {
      const app = localStore.db.applications.find(a => a.id === s.application_id);
      return `
        <tr>
          <td><b>${s.id}</b></td>
          <td>
            <div class="primary-cell-text">${escapeHtml(s.institution_name)}</div>
            <div class="secondary-cell-text">App: ${s.application_id}</div>
          </td>
          <td><b>${formatDate(s.scheduled_date)}</b></td>
          <td>${escapeHtml(s.visit_type)}</td>
          <td>
            <div class="primary-cell-text">${escapeHtml(s.committee_chair)}</div>
            <div class="secondary-cell-text" style="max-width:240px;white-space:normal">${escapeHtml(s.committee_members || '—')}</div>
          </td>
          <td>${renderPill(s.status)}</td>
          <td>
            <span class="pill ${s.report_submitted ? 'green' : 'amber'}">${s.report_submitted ? 'Report Submitted' : 'Pending Report'}</span>
          </td>
          <td>
            <div style="display:flex;gap:6px">
              ${s.status === 'Scheduled' ? `
                <button class="btn sm" onclick="EVCModule.openRescheduleModal('${s.id}')">Reschedule</button>
                <button class="btn sm primary" onclick="EVCModule.openCompleteModal('${s.id}')">Submit Report</button>
              ` : `
                <button class="btn sm" onclick="EVCModule.viewReportModal('${s.id}')">View Report</button>
              `}
            </div>
          </td>
        </tr>
      `;
    }).join("");

    return `
      <div class="page-header">
        <div>
          <div class="page-eyebrow">Expert Visiting Committee</div>
          <h1>EVC Scheduling & Pendency</h1>
          <p>Coordinate on-site physical and hybrid inspections, allocate expert committee chairs, and track inspection report submissions.</p>
        </div>
        <div class="header-action-group">
          <button class="btn" onclick="CSVUtil.downloadCSV('aicte_evc_schedules.csv', localStore.db.evc_schedules)">⇩ Export EVC Register</button>
          <button class="btn primary" onclick="EVCModule.openScheduleModal()">＋ Schedule New EVC Visit</button>
        </div>
      </div>

      <!-- Quick Metrics -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-header"><span>SCHEDULED VISITS</span><span>◷</span></div>
          <div class="stat-number">${schedules.filter(s => s.status === 'Scheduled').length}</div>
          <div class="stat-subtext">Visits in current cycle</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>AWAITING SCHEDULING</span><span style="color:#b45309">!</span></div>
          <div class="stat-number">${awaitingScheduling.length}</div>
          <div class="stat-subtext">Cleared scrutiny queue</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>COMPLETED VISITS</span><span style="color:#15803d">✓</span></div>
          <div class="stat-number">${schedules.filter(s => s.status === 'Completed').length}</div>
          <div class="stat-subtext">Inspection completed</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>PENDING REPORTS</span><span style="color:#b91c1c">◈</span></div>
          <div class="stat-number">${schedules.filter(s => !s.report_submitted).length}</div>
          <div class="stat-subtext">Visit report overdue</div>
        </div>
      </div>

      <!-- Awaiting Scheduling Queue Banner if any -->
      ${awaitingScheduling.length ? `
        <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:14px 18px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between">
          <div>
            <strong style="color:#1e40af;font-size:13px">Applications Eligible & Awaiting EVC Allocation (${awaitingScheduling.length})</strong>
            <p style="color:#1e3a8a;font-size:11.5px;margin-top:2px">
              ${awaitingScheduling.map(a => `${a.id} (${a.institution_name})`).join(", ")}
            </p>
          </div>
          <button class="btn sm primary" onclick="EVCModule.openScheduleModal('${awaitingScheduling[0].id}')">Allocate Committee Now →</button>
        </div>
      ` : ''}

      <!-- Main EVC Register Panel -->
      <div class="panel">
        <div class="panel-header">
          <div>
            <h3>Expert Visiting Committee Schedule</h3>
            <p>Inspection schedules with allocated peer experts and status</p>
          </div>
          <span class="pill gray">${schedules.length} Scheduled</span>
        </div>

        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>VISIT ID</th>
                <th>INSTITUTION / APP</th>
                <th>SCHEDULED DATE</th>
                <th>VISIT TYPE</th>
                <th>COMMITTEE CHAIR & MEMBERS</th>
                <th>VISIT STATUS</th>
                <th>REPORT STATUS</th>
                <th>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              ${rows || '<tr><td colspan="8" style="text-align:center;padding:24px;color:#64748b">No EVC visits scheduled.</td></tr>'}
            </tbody>
          </table>
        </div>
      </div>
    `;
  },

  openScheduleModal(preAppId = "") {
    const eligibleApps = localStore.db.applications;
    App.openModal(
      "Schedule Expert Visiting Committee (EVC)",
      `
        <form id="schedule-evc-form" class="form-grid">
          <div class="form-group full">
            <label class="form-label">Application *</label>
            <select class="form-control" id="evc-app-id" required>
              ${eligibleApps.map(a => `<option value="${a.id}" ${a.id === preAppId ? 'selected' : ''}>${a.id} — ${escapeHtml(a.institution_name)} (${a.type})</option>`).join("")}
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Visit Type</label>
            <select class="form-control" id="evc-visit-type">
              <option>Physical Inspection</option>
              <option>Hybrid Expert Visit</option>
              <option>Surprise Verification</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Scheduled Date *</label>
            <input class="form-control" id="evc-date" type="date" required value="2026-11-05" />
          </div>
          <div class="form-group full">
            <label class="form-label">Committee Chair *</label>
            <input class="form-control" id="evc-chair" required placeholder="e.g. Prof. R.K. Mishra (IIT Delhi)" value="Prof. R.K. Mishra (IIT Delhi)" />
          </div>
          <div class="form-group full">
            <label class="form-label">Committee Members & Regional Nodal Officer</label>
            <textarea class="form-control" id="evc-members" placeholder="Names, designations, and institutions of appointed peer reviewers">Dr. S. Ananth (NIT Warangal), Er. K.P. Sharma (AICTE Regional Officer)</textarea>
          </div>
          <div class="form-group full">
            <label class="form-label">Inspection Directives & Focus Areas</label>
            <textarea class="form-control" id="evc-directives" placeholder="Focus items: labs, equipment, fire safety, cadre ratio..."></textarea>
          </div>
        </form>
      `,
      `
        <button class="btn" onclick="App.closeModal()">Cancel</button>
        <button class="btn primary" onclick="EVCModule.confirmSchedule()">Confirm EVC Schedule</button>
      `
    );
  },

  async confirmSchedule() {
    const appId = document.getElementById("evc-app-id").value;
    const app = localStore.db.applications.find(a => a.id === appId);
    const date = document.getElementById("evc-date").value;
    const chair = document.getElementById("evc-chair").value;
    const members = document.getElementById("evc-members").value;
    const directives = document.getElementById("evc-directives").value;

    const newSchedule = {
      id: "EVC-2026-" + Math.floor(1000 + Math.random() * 9000),
      application_id: appId,
      institution_id: app ? app.institution_id : "INST-10482",
      institution_name: app ? app.institution_name : "Institution",
      visit_type: document.getElementById("evc-visit-type").value,
      scheduled_date: date,
      status: "Scheduled",
      committee_chair: chair,
      committee_members: members,
      report_submitted: false,
      observations: directives,
      remarks: "Official visit notification dispatched to Head of Institution."
    };

    localStore.db.evc_schedules.unshift(newSchedule);
    if (app) {
      app.current_stage = "EVC scheduling";
      app.status = "EVC scheduled";
      app.last_action = `EVC scheduled on ${date} chaired by ${chair}`;
    }
    localStore.log(chair, "EVC Coordinator", "Scheduled EVC Visit", "EVC", newSchedule.id, `Scheduled inspection for application ${appId} on ${date}.`);
    localStore.save();
    App.closeModal();
    App.toast("EVC visit scheduled successfully.");
    App.refresh();
  },

  openRescheduleModal(id) {
    const s = localStore.db.evc_schedules.find(x => x.id === id);
    App.openModal(
      `Reschedule EVC Visit · ${s.id}`,
      `
        <div class="form-group full">
          <label class="form-label">Institution: <b>${escapeHtml(s.institution_name)}</b></label>
        </div>
        <div class="form-group full" style="margin-top:10px">
          <label class="form-label">New Scheduled Date *</label>
          <input class="form-control" id="resched-date" type="date" value="${s.scheduled_date}" />
        </div>
        <div class="form-group full" style="margin-top:10px">
          <label class="form-label">Reason for Rescheduling</label>
          <textarea class="form-control" id="resched-reason" placeholder="Administrative or logistical rationale for rescheduling..."></textarea>
        </div>
      `,
      `
        <button class="btn" onclick="App.closeModal()">Cancel</button>
        <button class="btn primary" onclick="EVCModule.confirmReschedule('${id}')">Save Rescheduled Date</button>
      `
    );
  },

  confirmReschedule(id) {
    const s = localStore.db.evc_schedules.find(x => x.id === id);
    if (s) {
      const old = s.scheduled_date;
      s.scheduled_date = document.getElementById("resched-date").value;
      const reason = document.getElementById("resched-reason").value || "Administrative rescheduling";
      s.remarks = `Rescheduled from ${old} to ${s.scheduled_date}. Reason: ${reason}`;
      localStore.log("EVC Coordinator", "Regional Office", "Rescheduled EVC Visit", "EVC", s.id, s.remarks);
      localStore.save();
    }
    App.closeModal();
    App.toast("Visit date rescheduled.");
    App.refresh();
  },

  openCompleteModal(id) {
    const s = localStore.db.evc_schedules.find(x => x.id === id);
    App.openModal(
      `Submit EVC Inspection Report · ${s.id}`,
      `
        <p style="font-size:12px;color:#64748b;margin-bottom:12px">
          Record physical inspection observations for <b>${escapeHtml(s.institution_name)}</b>:
        </p>
        <div class="form-group full">
          <label class="form-label">Committee Findings & Infrastructure Observations *</label>
          <textarea class="form-control" id="evc-report-obs" style="min-height:90px" placeholder="Detail verified labs, computers, library volumes, fire safety equipment, barrier-free access..."></textarea>
        </div>
        <div class="form-group full" style="margin-top:10px">
          <label class="form-label">Committee Recommendation *</label>
          <select class="form-control" id="evc-recommendation">
            <option>Recommended for Approval</option>
            <option>Recommended with Rectification Undertaking</option>
            <option>Not Recommended due to Major Deficiencies</option>
          </select>
        </div>
      `,
      `
        <button class="btn" onclick="App.closeModal()">Cancel</button>
        <button class="btn primary" onclick="EVCModule.confirmComplete('${id}')">Submit Report & Advance Stage</button>
      `
    );
  },

  confirmComplete(id) {
    const s = localStore.db.evc_schedules.find(x => x.id === id);
    if (s) {
      s.status = "Completed";
      s.report_submitted = true;
      s.observations = document.getElementById("evc-report-obs").value;
      const rec = document.getElementById("evc-recommendation").value;
      s.remarks = `Recommendation: ${rec}`;

      const app = localStore.db.applications.find(a => a.id === s.application_id);
      if (app) {
        app.current_stage = "EVC completed";
        app.status = "In review";
        app.progress = 80;
        app.last_action = `EVC report filed: ${rec}`;
        app.next_action = "Appraisal by Standing Appellate Committee (SAC)";
      }
      localStore.log(s.committee_chair, "EVC Committee", "Completed EVC Inspection", "EVC", s.id, `Report filed with recommendation: ${rec}`);
      localStore.save();
    }
    App.closeModal();
    App.toast("EVC report submitted and application stage advanced.");
    App.refresh();
  },

  viewReportModal(id) {
    const s = localStore.db.evc_schedules.find(x => x.id === id);
    App.openModal(
      `EVC Inspection Report · ${s.id}`,
      `
        <div style="font-size:12px;line-height:1.6">
          <div style="margin-bottom:10px"><b>Institution:</b> ${escapeHtml(s.institution_name)}</div>
          <div style="margin-bottom:10px"><b>Inspection Date:</b> ${formatDate(s.scheduled_date)} (${escapeHtml(s.visit_type)})</div>
          <div style="margin-bottom:10px"><b>Committee:</b> ${escapeHtml(s.committee_chair)} | ${escapeHtml(s.committee_members || '')}</div>
          <hr style="border:none;border-top:1px solid #e2e8f0;margin:12px 0" />
          <div style="margin-bottom:10px">
            <b>Observations:</b>
            <p style="background:#f8fafc;padding:10px;border-radius:6px;border:1px solid #e2e8f0;margin-top:4px">${escapeHtml(s.observations || 'Satisfactory')}</p>
          </div>
          <div><b>Status:</b> ${renderPill(s.status)} &nbsp; <span class="pill green">${escapeHtml(s.remarks || 'Completed')}</span></div>
        </div>
      `,
      `<button class="btn" onclick="App.closeModal()">Close</button>`
    );
  }
};

window.EvcModule = EVCModule;
window.EVCModule = EVCModule;
