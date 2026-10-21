/**
 * Module 11: Tasks, Action Queue & Escalations
 */
const TasksModule = {
  state: {
    priority: "",
    status: ""
  },

  async render() {
    let list = localStore.db.tasks;
    if (this.state.priority) list = list.filter(t => t.priority === this.state.priority);
    if (this.state.status) list = list.filter(t => t.status === this.state.status);

    const rows = list.map(t => `
      <tr>
        <td><b>${t.id}</b></td>
        <td>
          <div class="primary-cell-text">${escapeHtml(t.title)}</div>
          <div class="secondary-cell-text">${escapeHtml(t.category)}</div>
        </td>
        <td>
          <div class="primary-cell-text">${escapeHtml(t.institution_name || 'Central')}</div>
        </td>
        <td>
          <span class="pill ${t.priority === 'Critical' ? 'red' : t.priority === 'High' ? 'amber' : 'blue'}">
            ${t.priority}
          </span>
        </td>
        <td>${escapeHtml(t.assigned_to)} <div class="secondary-cell-text">${escapeHtml(t.bureau)}</div></td>
        <td><b>${formatDate(t.due_date)}</b></td>
        <td>${renderPill(t.status)}</td>
        <td>
          <div style="display:flex;gap:6px">
            ${t.status === 'Pending' ? `
              <button class="btn sm" onclick="TasksModule.acknowledge('${t.id}')">Acknowledge</button>
            ` : ''}
            ${t.status !== 'Completed' ? `
              <button class="btn sm primary" onclick="TasksModule.openCompleteModal('${t.id}')">Complete</button>
              <button class="btn sm danger" onclick="TasksModule.openEscalateModal('${t.id}')">Escalate</button>
            ` : `
              <span class="pill green">✓ Closed</span>
            `}
          </div>
        </td>
      </tr>
    `).join("");

    return `
      <div class="page-header">
        <div>
          <div class="page-eyebrow">Officer Operations & Accountability</div>
          <h1>Central Task Management & Escalations</h1>
          <p>Prioritized action queue for regulatory officers, scrutiny teams, and bureau coordinators with deadline tracking.</p>
        </div>
        <div class="header-action-group">
          <button class="btn" onclick="CSVUtil.downloadCSV('aicte_tasks_queue.csv', localStore.db.tasks)">⇩ Export Tasks</button>
          <button class="btn primary" onclick="TasksModule.openCreateModal()">＋ Create Operational Task</button>
        </div>
      </div>

      <!-- Stats Grid -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-header"><span>ACTIVE TASKS</span><span>▤</span></div>
          <div class="stat-number">${list.filter(t => t.status !== 'Completed').length}</div>
          <div class="stat-subtext">Pending officer action</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>CRITICAL PRIORITY</span><span style="color:#b91c1c">!</span></div>
          <div class="stat-number">${list.filter(t => t.priority === 'Critical' && t.status !== 'Completed').length}</div>
          <div class="stat-subtext">Immediate intervention needed</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>IN PROGRESS</span><span>◷</span></div>
          <div class="stat-number">${list.filter(t => t.status === 'In Progress').length}</div>
          <div class="stat-subtext">Under active review</div>
        </div>
        <div class="stat-card">
          <div class="stat-header"><span>COMPLETED TASKS</span><span style="color:#15803d">✓</span></div>
          <div class="stat-number">${list.filter(t => t.status === 'Completed').length}</div>
          <div class="stat-subtext">Closed action items</div>
        </div>
      </div>

      <!-- Tasks Panel -->
      <div class="panel">
        <div class="filter-toolbar">
          <select class="filter-select" onchange="TasksModule.handleFilter('priority', this.value)">
            <option value="">All Priorities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
          <select class="filter-select" onchange="TasksModule.handleFilter('status', this.value)">
            <option value="">All Statuses</option>
            <option value="Pending">Pending</option>
            <option value="In Progress">In Progress</option>
            <option value="Escalated">Escalated</option>
            <option value="Completed">Completed</option>
          </select>
          <span style="font-size:11px;color:#64748b;margin-left:auto"><b>${list.length}</b> tasks queued</span>
        </div>

        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>TASK ID</th>
                <th>TASK DIRECTIVE</th>
                <th>RELATED INSTITUTION</th>
                <th>PRIORITY</th>
                <th>ASSIGNED OFFICER / BUREAU</th>
                <th>TARGET DEADLINE</th>
                <th>STATUS</th>
                <th>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              ${rows || '<tr><td colspan="8" style="text-align:center;padding:24px;color:#64748b">No tasks in queue.</td></tr>'}
            </tbody>
          </table>
        </div>
      </div>
    `;
  },

  handleFilter(key, val) {
    this.state[key] = val;
    App.refresh();
  },

  acknowledge(id) {
    const t = localStore.db.tasks.find(x => x.id === id);
    if (t) {
      t.status = "In Progress";
      localStore.log(t.assigned_to, "Assigned Officer", "Acknowledged Task", "Task", t.id, `Commenced work on task: ${t.title}.`);
      localStore.save();
    }
    App.toast("Task acknowledged and set to In Progress.");
    App.refresh();
  },

  openCompleteModal(id) {
    const t = localStore.db.tasks.find(x => x.id === id);
    App.openModal(
      `Complete Task · ${t.id}`,
      `
        <div style="font-size:12px;margin-bottom:12px">
          <b>Task:</b> ${escapeHtml(t.title)}<br>
          <b>Institution:</b> ${escapeHtml(t.institution_name)}
        </div>
        <div class="form-group full">
          <label class="form-label">Resolution Summary & Action Taken *</label>
          <textarea class="form-control" id="task-res-notes" placeholder="Summarize findings, report reference, or decision rendered..."></textarea>
        </div>
      `,
      `
        <button class="btn" onclick="App.closeModal()">Cancel</button>
        <button class="btn primary" onclick="TasksModule.confirmComplete('${id}')">Record Completion</button>
      `
    );
  },

  confirmComplete(id) {
    const t = localStore.db.tasks.find(x => x.id === id);
    if (t) {
      t.status = "Completed";
      t.resolution_notes = document.getElementById("task-res-notes").value;
      localStore.log(t.assigned_to, "Officer", "Completed Task", "Task", t.id, `Completed task: ${t.resolution_notes.slice(0, 60)}...`);
      localStore.save();
    }
    App.closeModal();
    App.toast("Task marked completed.");
    App.refresh();
  },

  openEscalateModal(id) {
    const t = localStore.db.tasks.find(x => x.id === id);
    App.openModal(
      `Escalate Task · ${t.id}`,
      `
        <div style="font-size:12px;margin-bottom:12px">
          <b>Task:</b> ${escapeHtml(t.title)}<br>
          <b>Current Assignee:</b> ${escapeHtml(t.assigned_to)}
        </div>
        <div class="form-group full">
          <label class="form-label">Escalate To Official / Committee *</label>
          <select class="form-control" id="escalate-target">
            <option>Bureau Head (Central Regulation Bureau)</option>
            <option>Member Secretary, AICTE</option>
            <option>Chairman, Standing Appellate Committee</option>
            <option>Chief Vigilance Officer</option>
          </select>
        </div>
        <div class="form-group full" style="margin-top:10px">
          <label class="form-label">Statutory Reason for Escalation *</label>
          <textarea class="form-control" id="escalate-reason" placeholder="Explain deadline breach, non-compliance, or required executive intervention..."></textarea>
        </div>
      `,
      `
        <button class="btn" onclick="App.closeModal()">Cancel</button>
        <button class="btn danger" onclick="TasksModule.confirmEscalate('${id}')">Execute Escalation</button>
      `
    );
  },

  confirmEscalate(id) {
    const t = localStore.db.tasks.find(x => x.id === id);
    if (t) {
      t.priority = "Critical";
      t.status = "Escalated";
      const target = document.getElementById("escalate-target").value;
      const reason = document.getElementById("escalate-reason").value;
      t.assigned_to = target;
      t.resolution_notes = `[Escalated to ${target}: ${reason}]`;
      localStore.log("Escalation Officer", "Adjudicator", "Escalated Task", "Task", t.id, `Escalated to ${target}. Reason: ${reason}`);
      localStore.save();
    }
    App.closeModal();
    App.toast("Task escalated to senior authority.");
    App.refresh();
  },

  openCreateModal() {
    App.openModal(
      "Create New Operational Task",
      `
        <form id="create-task-form" class="form-grid">
          <div class="form-group full">
            <label class="form-label">Task Directive Title *</label>
            <input class="form-control" id="new-task-title" required placeholder="e.g. Verify renewed land lease registration with sub-registrar" />
          </div>
          <div class="form-group">
            <label class="form-label">Category</label>
            <select class="form-control" id="new-task-cat">
              <option>Compliance Review</option>
              <option>Case Coordination</option>
              <option>EVC Coordination</option>
              <option>Document Verification</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Priority Level</label>
            <select class="form-control" id="new-task-priority">
              <option>Critical</option>
              <option>High</option>
              <option selected>Medium</option>
              <option>Low</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Assigned Official *</label>
            <input class="form-control" id="new-task-owner" required value="R. Sharma (Scrutiny Officer)" />
          </div>
          <div class="form-group">
            <label class="form-label">Bureau / Unit</label>
            <select class="form-control" id="new-task-bureau">
              <option>Approval Bureau</option>
              <option>Regulation Bureau</option>
              <option>Regional Office</option>
              <option>PGRC</option>
            </select>
          </div>
          <div class="form-group full">
            <label class="form-label">Related Institution</label>
            <select class="form-control" id="new-task-inst">
              ${localStore.db.institutions.map(i => `<option value="${i.id}">${escapeHtml(i.name)} (${i.permanent_id})</option>`).join("")}
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Completion Due Date *</label>
            <input class="form-control" id="new-task-due" type="date" required value="2026-11-05" />
          </div>
        </form>
      `,
      `
        <button class="btn" onclick="App.closeModal()">Cancel</button>
        <button class="btn primary" onclick="TasksModule.confirmCreate()">Create Task</button>
      `
    );
  },

  confirmCreate() {
    const instId = document.getElementById("new-task-inst").value;
    const inst = localStore.db.institutions.find(i => i.id === instId);
    const newTask = {
      id: "TSK-2026-" + Math.floor(1000 + Math.random() * 9000),
      title: document.getElementById("new-task-title").value,
      category: document.getElementById("new-task-cat").value,
      priority: document.getElementById("new-task-priority").value,
      status: "Pending",
      due_date: document.getElementById("new-task-due").value,
      assigned_to: document.getElementById("new-task-owner").value,
      bureau: document.getElementById("new-task-bureau").value,
      institution_id: instId,
      institution_name: inst ? inst.name : "Institution",
      resolution_notes: ""
    };

    localStore.db.tasks.unshift(newTask);
    localStore.log("Workflow Engine", "System", "Created Task", "Task", newTask.id, `Created task '${newTask.title}'.`);
    localStore.save();
    App.closeModal();
    App.toast("Action task created and queued.");
    App.refresh();
  }
};

window.TasksModule = TasksModule;
