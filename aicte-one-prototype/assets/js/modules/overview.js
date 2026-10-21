/**
 * Module 1: Executive Overview Dashboard
 */
const OverviewModule = {
  async render() {
    const metrics = await API.getDashboardMetrics();
    const sum = metrics.summary;

    const attentionCount = metrics.compliance_health.due_soon + metrics.compliance_health.overdue;
    const pendingDocs = metrics.document_outcomes.pending + metrics.document_outcomes.mismatch + metrics.document_outcomes.expiry;

    // Recent applications (slice 4)
    const recentApps = await API.getApplications();
    const appRows = recentApps.slice(0, 5).map(a => `
      <tr>
        <td>
          <div class="primary-cell-text">${a.id}</div>
          <div class="secondary-cell-text">${a.type}</div>
        </td>
        <td>
          <div class="primary-cell-text">${escapeHtml(a.institution_name)}</div>
          <div class="secondary-cell-text">${a.permanent_id}</div>
        </td>
        <td><span class="pill blue">${escapeHtml(a.current_stage)}</span></td>
        <td>
          <div style="display:flex;align-items:center;gap:8px">
            <div style="flex:1;background:#e2e8f0;height:6px;border-radius:10px;overflow:hidden;width:70px">
              <div style="background:#2563eb;height:100%;width:${a.progress}%;border-radius:10px"></div>
            </div>
            <span style="font-size:11px;font-weight:600">${a.progress}%</span>
          </div>
        </td>
        <td>${renderPill(a.status)}</td>
        <td>
          <button class="btn sm" onclick="App.navigate('applications', { id: '${a.id}' })">Inspect →</button>
        </td>
      </tr>
    `).join("");

    // Priority alerts
    const alerts = localStore.db.compliance.filter(c => /overdue|due soon|action/i.test(c.status)).slice(0, 4);
    const alertHtml = alerts.map(c => `
      <div style="display:flex;gap:12px;padding:10px 0;border-bottom:1px solid #f1f5f9;align-items:flex-start">
        <span class="pill ${c.status === 'Overdue' ? 'red' : 'amber'}" style="margin-top:2px">!</span>
        <div style="flex:1">
          <strong style="font-size:12px;display:block;color:#0f172a">${escapeHtml(c.title)}</strong>
          <span style="font-size:11px;color:#64748b">${escapeHtml(c.institution_name)} · Due ${formatDate(c.due_date)}</span>
        </div>
        <button class="btn sm" onclick="App.navigate('compliance', { id: '${c.id}' })">Review</button>
      </div>
    `).join("");

    // Recent activity audit timeline
    const audits = localStore.db.audit.slice(0, 5);
    const auditHtml = audits.map(a => `
      <div style="display:grid;grid-template-columns:24px 1fr;gap:12px;padding-bottom:14px;position:relative">
        <div style="width:24px;height:24px;border-radius:6px;background:#eff6ff;color:#2563eb;display:grid;place-items:center;font-size:11px;font-weight:700">●</div>
        <div>
          <strong style="font-size:12px;color:#0f172a">${escapeHtml(a.action)}</strong>
          <p style="font-size:11px;color:#64748b;margin:2px 0">${escapeHtml(a.detail)}</p>
          <small style="font-size:10px;color:#94a3b8">${escapeHtml(a.actor)} (${escapeHtml(a.role)}) · ${escapeHtml(a.time)}</small>
        </div>
      </div>
    `).join("");

    return `
      <div class="page-header">
        <div>
          <div class="page-eyebrow">National Institutional Governance Dashboard</div>
          <h1>Executive Overview</h1>
          <p>Real-time regulatory pulse across institutional approval workflows, compliance deadlines, and grievance coordination.</p>
        </div>
        <div class="header-action-group">
          <button class="btn" onclick="CSVUtil.downloadCSV('aicte_executive_snapshot.csv', localStore.db.applications)">⇩ Export Snapshot</button>
          <button class="btn primary" onclick="App.openCreateModal('application')">＋ Lodgement New Application</button>
        </div>
      </div>

      <!-- Stat Cards -->
      <div class="stats-grid">
        <div class="stat-card" onclick="App.navigate('institutions')">
          <div class="stat-header">
            <span>REGISTERED INSTITUTIONS</span>
            <span class="stat-icon-wrapper" style="background:#eff6ff;color:#2563eb">▦</span>
          </div>
          <div class="stat-number">${sum.institutions}</div>
          <div class="stat-subtext">Across technical education categories</div>
        </div>

        <div class="stat-card" onclick="App.navigate('applications')">
          <div class="stat-header">
            <span>APPLICATIONS IN WORKFLOW</span>
            <span class="stat-icon-wrapper" style="background:#eff6ff;color:#2563eb">▤</span>
          </div>
          <div class="stat-number">${sum.applications}</div>
          <div class="stat-subtext">${sum.applications} active across scrutiny & EVC</div>
        </div>

        <div class="stat-card" onclick="App.navigate('verification')">
          <div class="stat-header">
            <span>DOCUMENTS FOR REVIEW</span>
            <span class="stat-icon-wrapper" style="background:#fffbeb;color:#b45309">◈</span>
          </div>
          <div class="stat-number">${pendingDocs}</div>
          <div class="stat-subtext">${metrics.document_outcomes.mismatch} discrepancies flagged</div>
        </div>

        <div class="stat-card" onclick="App.navigate('compliance')">
          <div class="stat-header">
            <span>COMPLIANCE OBLIGATIONS</span>
            <span class="stat-icon-wrapper" style="background:#fef2f2;color:#b91c1c">◷</span>
          </div>
          <div class="stat-number">${attentionCount}</div>
          <div class="stat-subtext">${metrics.compliance_health.overdue} overdue · ${metrics.compliance_health.due_soon} due soon</div>
        </div>
      </div>

      <!-- Main Layout Grid -->
      <div class="grid-2">
        <!-- Approval Pipeline Distribution -->
        <div class="panel">
          <div class="panel-header">
            <div>
              <h3>Approval Workflow Pipeline</h3>
              <p>Applications distributed by statutory processing stage</p>
            </div>
            <button class="btn sm" onclick="App.navigate('applications')">View Full Register →</button>
          </div>
          <div class="panel-body">
            <div style="display:grid;gap:12px;margin-bottom:20px">
              ${[
                ['Preliminary validation', metrics.stage_distribution['Preliminary validation'] || 0],
                ['Scrutiny & Re-scrutiny', (metrics.stage_distribution['Scrutiny'] || 0) + (metrics.stage_distribution['Re-scrutiny'] || 0)],
                ['EVC scheduling & visits', (metrics.stage_distribution['EVC scheduling'] || 0) + (metrics.stage_distribution['EVC completed'] || 0)],
                ['SAC / SHC Committee Review', metrics.stage_distribution['SAC/SHC review'] || 0],
                ['Authorized disposition', metrics.stage_distribution['Authorized disposition'] || 0]
              ].map(([stg, count]) => {
                const pct = Math.max(8, Math.round((count / Math.max(1, sum.applications)) * 100));
                return `
                  <div>
                    <div style="display:flex;justify-content:space-between;font-size:11.5px;font-weight:600;margin-bottom:4px">
                      <span>${stg}</span>
                      <span>${count} applications</span>
                    </div>
                    <div style="height:7px;background:#f1f5f9;border-radius:6px;overflow:hidden">
                      <div style="height:100%;background:#2563eb;width:${pct}%;border-radius:6px"></div>
                    </div>
                  </div>
                `;
              }).join("")}
            </div>

            <div class="table-responsive">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>APPLICATION</th>
                    <th>INSTITUTION</th>
                    <th>STAGE</th>
                    <th>PROGRESS</th>
                    <th>STATUS</th>
                    <th>ACTION</th>
                  </tr>
                </thead>
                <tbody>
                  ${appRows}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Right Side: Priority Alerts & Bureau Workload -->
        <div style="display:flex;flex-direction:column;gap:20px">
          <!-- Priority Actions -->
          <div class="panel">
            <div class="panel-header">
              <h3>Priority Administrative Alerts</h3>
              <span class="pill amber">${alerts.length} Immediate</span>
            </div>
            <div class="panel-body" style="padding-top:10px">
              ${alertHtml || '<p class="muted">No priority alerts outstanding.</p>'}
            </div>
          </div>

          <!-- Cross-Bureau Coordination Notice -->
          <div class="panel">
            <div class="panel-header">
              <h3>Cross-Bureau Coordination</h3>
              <span class="pill blue">${sum.overlapping_cases} Suggested Overlaps</span>
            </div>
            <div class="panel-body">
              <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:12px;margin-bottom:12px">
                <div style="display:flex;align-items:center;gap:8px;font-weight:700;color:#1e40af;font-size:12px">
                  <span>⌁</span> Overlapping Grievance Signal Detected
                </div>
                <p style="font-size:11.5px;color:#1e3a8a;margin-top:4px">
                  Public grievance <b>PGRC-26-01842</b> correlates with Regulation Bureau audit <b>RB-26-00917</b> regarding excess student admissions at Noida Institute of Engineering & Technology.
                </p>
              </div>
              <button class="btn sm primary" style="width:100%" onclick="App.navigate('coordination')">Open Coordination Workspace →</button>
            </div>
          </div>

          <!-- Activity Audit Stream -->
          <div class="panel">
            <div class="panel-header">
              <h3>Recent Governance Audit Trail</h3>
              <button class="btn sm" onclick="App.navigate('audit')">Full Audit →</button>
            </div>
            <div class="panel-body" style="padding-top:14px">
              ${auditHtml}
            </div>
          </div>
        </div>
      </div>
    `;
  }
};

window.OverviewModule = OverviewModule;
