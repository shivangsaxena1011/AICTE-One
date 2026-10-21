/**
 * Dual-Mode API Bridge for AICTE ONE
 * Automatically detects live FastAPI backend; gracefully falls back to localStore
 * Supports both API and ApiService namespaces interchangeably
 */
const API = {
  baseUrl: (window.location.protocol === 'file:' ? 'http://localhost:8000/api' : `${window.location.origin}/api`),
  isBackendLive: false,

  getHeaders(extra = {}) {
    const role = (window.App && typeof App.getCurrentRole === 'function') ? App.getCurrentRole() : null;
    return {
      "Content-Type": "application/json",
      "X-Role": role ? role.id : "ADMIN",
      "X-Actor": role ? role.email : "admin@aicte-india.org",
      ...extra
    };
  },

  async init() {
    try {
      const res = await fetch(`${this.baseUrl}/health`, { signal: AbortSignal.timeout(1500) });
      if (res.ok) {
        this.isBackendLive = true;
        console.log("🟢 Connected to live FastAPI AICTE ONE backend at:", this.baseUrl);
      } else {
        this.isBackendLive = false;
      }
    } catch (e) {
      this.isBackendLive = false;
      console.log("🟡 Backend offline; operating in high-fidelity standalone browser mode.");
    }
    return this.isBackendLive;
  },

  async checkBackendHealth() {
    return await this.init();
  },

  isBackendConnected() {
    return this.isBackendLive;
  },

  // Helper to attach items/data aliases to arrays so callers using either property succeed
  wrapCollection(arr, extra = {}) {
    if (!Array.isArray(arr)) {
      if (typeof arr === 'object' && arr !== null) {
        if (!arr.items && arr.data) arr.items = arr.data;
        if (!arr.data && arr.items) arr.data = arr.items;
      }
      return arr;
    }
    const res = [...arr];
    res.items = arr;
    res.data = arr;
    Object.assign(res, extra);
    return res;
  },

  // 1. Executive Analytics
  async getDashboardMetrics() {
    if (this.isBackendLive) {
      try {
        const res = await fetch(`${this.baseUrl}/analytics/dashboard`, { headers: this.getHeaders() });
        if (res.ok) return await res.json();
      } catch (e) { console.warn("API fallback:", e); }
    }
    // Client-side computation
    const db = localStore.db;
    const stageCounts = {};
    db.applications.forEach(a => {
      const st = a.current_stage || a.stage;
      stageCounts[st] = (stageCounts[st] || 0) + 1;
    });

    const docOutcomes = {
      verified: db.documents.filter(d => /verified/i.test(d.status)).length,
      pending: db.documents.filter(d => /pending/i.test(d.status)).length,
      mismatch: db.documents.filter(d => /mismatch/i.test(d.status)).length,
      expiry: db.documents.filter(d => /expir/i.test(d.status)).length,
      anomalies: db.documents.filter(d => d.is_anomaly).length
    };

    const compHealth = {
      on_track: db.compliance.filter(c => /on track|satisfied/i.test(c.status)).length,
      due_soon: db.compliance.filter(c => /due soon|action/i.test(c.status)).length,
      overdue: db.compliance.filter(c => /overdue/i.test(c.status)).length,
      review_pending: db.compliance.filter(c => /pending|submitted/i.test(c.status)).length
    };

    const bureauCounts = {};
    db.complaints.forEach(c => {
      bureauCounts[c.bureau] = (bureauCounts[c.bureau] || 0) + 1;
    });

    const overlapCount = Math.floor(db.complaints.filter(c => c.related_case_id).length / 2);

    return {
      summary: {
        institutions: db.institutions.length,
        applications: db.applications.length,
        documents: db.documents.length,
        compliance: db.compliance.length,
        complaints: db.complaints.length,
        tasks: db.tasks.length,
        overlapping_cases: overlapCount
      },
      stage_distribution: stageCounts,
      document_outcomes: docOutcomes,
      compliance_health: compHealth,
      bureau_workload: bureauCounts,
      evc_metrics: {
        scheduled: db.evc_schedules.filter(e => e.status === "Scheduled").length,
        completed: db.evc_schedules.filter(e => e.status === "Completed").length,
        pending_reports: db.evc_schedules.filter(e => !e.report_submitted).length
      },
      task_metrics: {
        critical: db.tasks.filter(t => t.priority === "Critical" && t.status !== "Completed").length,
        high: db.tasks.filter(t => t.priority === "High" && t.status !== "Completed").length,
        in_progress: db.tasks.filter(t => t.status === "In Progress").length,
        pending: db.tasks.filter(t => t.status === "Pending").length
      },
      applications: {
        total: db.applications.length,
        with_deficiencies: db.applications.filter(a => (a.deficiency_count > 0 || (a.deficiencies && a.deficiencies.length > 0))).length
      }
    };
  },

  async getAnalytics() {
    return await this.getDashboardMetrics();
  },

  // 2. Institutions
  async getInstitutions(params = {}) {
    if (this.isBackendLive) {
      try {
        const cleanParams = {};
        Object.keys(params).forEach(k => {
          if (params[k] !== undefined && params[k] !== null && params[k] !== "") {
            cleanParams[k] = params[k];
          }
        });
        const qs = new URLSearchParams(cleanParams).toString();
        const res = await fetch(`${this.baseUrl}/institutions?${qs}`, { headers: this.getHeaders() });
        if (res.ok) {
          const json = await res.json();
          if (json && json.data) {
            json.items = json.data;
          }
          return json;
        }
      } catch (e) { console.warn("API fallback:", e); }
    }

    let list = [...localStore.db.institutions];
    const q = (params.q || params.search || "").toLowerCase();
    if (q) {
      list = list.filter(i => (i.name + (i.permanent_id || '') + (i.city || '') + (i.district || '') + (i.state || '')).toLowerCase().includes(q));
    }
    if (params.state) list = list.filter(i => i.state === params.state);
    if (params.category) list = list.filter(i => i.category === params.category);
    if (params.institution_type) list = list.filter(i => i.institution_type === params.institution_type);
    if (params.approval_status) list = list.filter(i => i.approval_status === params.approval_status);

    const page = parseInt(params.page) || 1;
    const limit = parseInt(params.limit) || 25;
    const total = list.length;
    const offset = (page - 1) * limit;

    const data = list.slice(offset, offset + limit).map(inst => ({
      ...inst,
      applications_count: localStore.db.applications.filter(a => a.institution_id === inst.id).length,
      documents_count: localStore.db.documents.filter(d => d.institution_id === inst.id).length,
      compliance_count: localStore.db.compliance.filter(c => c.institution_id === inst.id).length,
      complaints_count: localStore.db.complaints.filter(c => c.institution_id === inst.id).length
    }));

    return { total, page, limit, pages: Math.ceil(total / limit) || 1, data, items: data };
  },

  async getInstitutionDigitalTwin(id) {
    if (this.isBackendLive) {
      try {
        const res = await fetch(`${this.baseUrl}/institutions/${id}`, { headers: this.getHeaders() });
        if (res.ok) return await res.json();
      } catch (e) { console.warn("API fallback:", e); }
    }

    const inst = localStore.db.institutions.find(i => i.id === id || i.permanent_id === id) || localStore.db.institutions[0];
    if (!inst) return null;

    const apps = localStore.db.applications.filter(a => a.institution_id === inst.id);
    const docs = localStore.db.documents.filter(d => d.institution_id === inst.id);
    const comps = localStore.db.compliance.filter(c => c.institution_id === inst.id);
    const cases = localStore.db.complaints.filter(c => c.institution_id === inst.id);
    const tasks = localStore.db.tasks.filter(t => t.institution_id === inst.id);
    const audits = localStore.db.audit.filter(a => a.record === inst.id || a.record === inst.permanent_id || (a.detail || "").includes(inst.name)).slice(0, 10);

    return {
      institution: inst,
      applications: apps,
      documents: docs,
      compliance: comps,
      complaints: cases,
      tasks: tasks,
      activity_timeline: audits
    };
  },

  async createInstitution(data) {
    if (this.isBackendLive) {
      try {
        const res = await fetch(`${this.baseUrl}/institutions`, {
          method: "POST",
          headers: this.getHeaders(),
          body: JSON.stringify(data)
        });
        if (res.ok) return await res.json();
      } catch (e) { console.warn("API fallback:", e); }
    }

    const newInst = {
      id: "INST-" + Math.floor(10000 + Math.random() * 90000),
      ...data,
      last_verified: new Date().toISOString().slice(0, 10)
    };
    localStore.db.institutions.unshift(newInst);
    localStore.log("Admin Officer", "Administrator", "Created Institution Record", "Institution", newInst.id, `Added ${newInst.name} (${newInst.permanent_id}) to directory.`);
    localStore.save();
    return newInst;
  },

  // 3. Applications
  async getApplications(params = {}) {
    if (this.isBackendLive) {
      try {
        const cleanParams = {};
        Object.keys(params).forEach(k => {
          if (params[k] !== undefined && params[k] !== null && params[k] !== "") {
            cleanParams[k] = params[k];
          }
        });
        const qs = new URLSearchParams(cleanParams).toString();
        const res = await fetch(`${this.baseUrl}/applications?${qs}`, { headers: this.getHeaders() });
        if (res.ok) {
          const list = await res.json();
          return this.wrapCollection(list);
        }
      } catch (e) { console.warn("API fallback:", e); }
    }

    let list = [...localStore.db.applications];
    if (params.stage) list = list.filter(a => a.current_stage === params.stage);
    if (params.status) list = list.filter(a => a.status === params.status);
    if (params.institution_id) list = list.filter(a => a.institution_id === params.institution_id);
    const q = (params.q || params.search || "").toLowerCase();
    if (q) {
      list = list.filter(a => (a.id + (a.institution_name || '') + (a.permanent_id || '') + (a.type || '')).toLowerCase().includes(q));
    }
    return this.wrapCollection(list);
  },

  async createApplication(data) {
    if (this.isBackendLive) {
      try {
        const res = await fetch(`${this.baseUrl}/applications`, {
          method: "POST",
          headers: this.getHeaders(),
          body: JSON.stringify(data)
        });
        if (res.ok) return await res.json();
      } catch (e) { console.warn("API fallback:", e); }
    }

    const inst = localStore.db.institutions.find(i => i.id === data.institution_id || i.permanent_id === data.institution_id);
    const newApp = {
      id: "APP-2026-" + Math.floor(1000 + Math.random() * 9000),
      institution_id: inst ? inst.id : data.institution_id,
      institution_name: inst ? inst.name : "Technical Institute",
      permanent_id: inst ? inst.permanent_id : "1-000000",
      category: data.category || "Engineering and Technology",
      type: data.type || "Extension of Approval",
      academic_year: data.academic_year || "2026-2027",
      current_stage: "Preliminary validation",
      status: "New submission",
      owner: data.owner || "Intake Officer",
      progress: 15,
      submitted_at: new Date().toISOString().slice(0, 10),
      due_date: data.due_date || "2026-11-15",
      deficiency_count: 0,
      last_action: "Application submitted for preliminary scrutiny",
      next_action: "Perform automated document verification checklist"
    };
    localStore.db.applications.unshift(newApp);
    localStore.log(newApp.owner, "Approval Officer", "Created Approval Application", "Application", newApp.id, `Created ${newApp.type} for ${newApp.institution_name}.`);
    localStore.save();
    return newApp;
  },

  async transitionApplication(id, stage, status, actor, remarks = "", deficiencies = []) {
    if (this.isBackendLive) {
      try {
        const res = await fetch(`${this.baseUrl}/applications/${id}/transition`, {
          method: "POST",
          headers: this.getHeaders(),
          body: JSON.stringify({ next_stage: stage, status, actor, remarks, deficiencies })
        });
        if (res.ok) return await res.json();
      } catch (e) { console.warn("API fallback:", e); }
    }

    const app = localStore.db.applications.find(a => a.id === id);
    if (app) {
      const oldStage = app.current_stage;
      app.current_stage = stage;
      app.status = status;
      app.owner = actor;
      app.last_action = remarks || `Transitioned from ${oldStage} to ${stage}`;
      if (deficiencies.length) app.deficiency_count = deficiencies.length;
      localStore.log(actor, "Scrutiny Officer", "Stage Transition", "Application", app.id, `Advanced from ${oldStage} to ${stage}. Status: ${status}.`);
      localStore.save();
    }
    return { success: true, current_stage: stage, status };
  },

  // 4. Documents & OCR
  async getDocuments(params = {}) {
    if (this.isBackendLive) {
      try {
        const cleanParams = {};
        Object.keys(params).forEach(k => {
          if (params[k] !== undefined && params[k] !== null && params[k] !== "") {
            cleanParams[k] = params[k];
          }
        });
        const qs = new URLSearchParams(cleanParams).toString();
        const res = await fetch(`${this.baseUrl}/documents?${qs}`, { headers: this.getHeaders() });
        if (res.ok) {
          const list = await res.json();
          return this.wrapCollection(list);
        }
      } catch (e) { console.warn("API fallback:", e); }
    }

    let list = [...localStore.db.documents];
    if (params.institution_id) list = list.filter(d => d.institution_id === params.institution_id);
    if (params.application_id) list = list.filter(d => d.application_id === params.application_id);
    if (params.status) list = list.filter(d => d.status === params.status);
    return this.wrapCollection(list);
  },

  async verifyDocumentAuthority(id) {
    if (this.isBackendLive) {
      try {
        const res = await fetch(`${this.baseUrl}/documents/${id}/verify-authority`, {
          method: "POST",
          headers: this.getHeaders()
        });
        if (res.ok) return await res.json();
      } catch (e) { console.warn("API fallback:", e); }
    }

    const doc = localStore.db.documents.find(d => d.id === id);
    if (doc) {
      doc.status = "Verified (demo)";
      doc.verification_source = "DigiLocker Authority Adapter (Sandbox)";
      doc.verification_response = `Reference #${doc.authority_ref || doc.id} matched verified registry database. (Simulated test source)`;
      localStore.log("Verification Adapter", "Authority Gateway", "Authority Verification Check", "Document", doc.id, `Verified with ${doc.verification_source}.`);
      localStore.save();
      return { status: doc.status, source: doc.verification_source, evidence: doc.verification_response };
    }
    return null;
  },

  async getValidationReport(id) {
    if (this.isBackendLive) {
      try {
        const res = await fetch(`${this.baseUrl}/documents/${id}/report`, { headers: this.getHeaders() });
        if (res.ok) return await res.json();
      } catch (e) { console.warn("API fallback:", e); }
    }
    const doc = localStore.db.documents.find(d => d.id === id) || localStore.db.documents[0];
    const inst = localStore.db.institutions.find(i => i.id === doc.institution_id) || localStore.db.institutions[0];
    return {
      document_id: doc.id,
      institution_name: inst.name,
      permanent_id: inst.permanent_id,
      document_name: doc.name,
      document_type: doc.document_type,
      status: doc.status,
      confidence_score: doc.confidence_score,
      findings: doc.findings,
      authority_verification: doc.verification_source,
      official_disposition: "Requires authorized administrative sign-off prior to approval advancement."
    };
  },

  // 5. Compliance
  async getCompliance(params = {}) {
    if (this.isBackendLive) {
      try {
        const cleanParams = {};
        Object.keys(params).forEach(k => {
          if (params[k] !== undefined && params[k] !== null && params[k] !== "") {
            cleanParams[k] = params[k];
          }
        });
        const qs = new URLSearchParams(cleanParams).toString();
        const res = await fetch(`${this.baseUrl}/compliance?${qs}`, { headers: this.getHeaders() });
        if (res.ok) {
          const list = await res.json();
          return this.wrapCollection(list);
        }
      } catch (e) { console.warn("API fallback:", e); }
    }
    return this.wrapCollection(localStore.db.compliance);
  },

  // 6. Complaints & Coordination
  async getComplaints(params = {}) {
    if (this.isBackendLive) {
      try {
        const cleanParams = {};
        Object.keys(params).forEach(k => {
          if (params[k] !== undefined && params[k] !== null && params[k] !== "") {
            cleanParams[k] = params[k];
          }
        });
        const qs = new URLSearchParams(cleanParams).toString();
        const res = await fetch(`${this.baseUrl}/complaints?${qs}`, { headers: this.getHeaders() });
        if (res.ok) {
          const list = await res.json();
          return this.wrapCollection(list);
        }
      } catch (e) { console.warn("API fallback:", e); }
    }
    return this.wrapCollection(localStore.db.complaints);
  },

  async linkCoordination(caseAId, caseBId, rationale, actor = "Central Administration Officer") {
    if (this.isBackendLive) {
      try {
        const res = await fetch(`${this.baseUrl}/complaints/link-coordination`, {
          method: "POST",
          headers: this.getHeaders(),
          body: JSON.stringify({ case_a_id: caseAId, case_b_id: caseBId, rationale })
        });
        if (res.ok) return await res.json();
      } catch (e) { console.warn("API fallback:", e); }
    }

    const a = localStore.db.complaints.find(c => c.id === caseAId);
    const b = localStore.db.complaints.find(c => c.id === caseBId);
    if (a && b) {
      a.related_case_id = caseBId;
      b.related_case_id = caseAId;
      localStore.log(actor, "Coordination Officer", "Confirmed Case Relationship", "Coordination", `${caseAId}|${caseBId}`, `Linked ${caseAId} (${a.bureau}) and ${caseBId} (${b.bureau}). Rationale: ${rationale}`);
      localStore.save();
    }
    return { success: true };
  },

  // 7. Tasks
  async getTasks(params = {}) {
    if (this.isBackendLive) {
      try {
        const cleanParams = {};
        Object.keys(params).forEach(k => {
          if (params[k] !== undefined && params[k] !== null && params[k] !== "") {
            cleanParams[k] = params[k];
          }
        });
        const qs = new URLSearchParams(cleanParams).toString();
        const res = await fetch(`${this.baseUrl}/tasks?${qs}`, { headers: this.getHeaders() });
        if (res.ok) {
          const list = await res.json();
          return this.wrapCollection(list);
        }
      } catch (e) { console.warn("API fallback:", e); }
    }
    return this.wrapCollection(localStore.db.tasks);
  },

  async createTask(data) {
    if (this.isBackendLive) {
      try {
        const res = await fetch(`${this.baseUrl}/tasks`, {
          method: "POST",
          headers: this.getHeaders(),
          body: JSON.stringify(data)
        });
        if (res.ok) return await res.json();
      } catch (e) { console.warn("API fallback:", e); }
    }
    const newTask = {
      id: "TSK-" + Math.floor(1000 + Math.random() * 9000),
      ...data,
      status: "Pending",
      created_at: new Date().toISOString()
    };
    localStore.db.tasks.unshift(newTask);
    localStore.log("Workflow Engine", "System", "Created Task", "Task", newTask.id, `Created task '${newTask.title}'.`);
    localStore.save();
    return newTask;
  },

  async updateTaskStatus(id, status, notes = "") {
    if (this.isBackendLive) {
      try {
        const res = await fetch(`${this.baseUrl}/tasks/${id}/status`, {
          method: "POST",
          headers: this.getHeaders(),
          body: JSON.stringify({ status, resolution_notes: notes })
        });
        if (res.ok) return await res.json();
      } catch (e) { console.warn("API fallback:", e); }
    }
    const t = localStore.db.tasks.find(x => x.id === id);
    if (t) {
      t.status = status;
      if (notes) t.resolution_notes = notes;
      localStore.log("Assigned Officer", "Officer", `Updated Task to ${status}`, "Task", t.id, notes || `Status changed to ${status}`);
      localStore.save();
    }
    return { success: true };
  },

  async escalateTask(id, escalatedTo, reason) {
    if (this.isBackendLive) {
      try {
        const res = await fetch(`${this.baseUrl}/tasks/${id}/escalate`, {
          method: "POST",
          headers: this.getHeaders(),
          body: JSON.stringify({ escalated_to: escalatedTo, reason })
        });
        if (res.ok) return await res.json();
      } catch (e) { console.warn("API fallback:", e); }
    }
    const t = localStore.db.tasks.find(x => x.id === id);
    if (t) {
      t.status = "Escalated";
      t.priority = "Critical";
      localStore.log("Escalation Authority", "Adjudicator", "Escalated Task", "Task", t.id, `Escalated to ${escalatedTo}. Reason: ${reason}`);
      localStore.save();
    }
    return { success: true };
  },

  // 8. Notifications
  async getNotifications(params = {}) {
    if (this.isBackendLive) {
      try {
        const res = await fetch(`${this.baseUrl}/notifications`, { headers: this.getHeaders() });
        if (res.ok) {
          const list = await res.json();
          return this.wrapCollection(list);
        }
      } catch (e) { console.warn("API fallback:", e); }
    }
    return this.wrapCollection(localStore.db.notifications);
  },

  async markNotificationRead(id) {
    if (this.isBackendLive) {
      try {
        const res = await fetch(`${this.baseUrl}/notifications/${id}/read`, {
          method: "POST",
          headers: this.getHeaders()
        });
        if (res.ok) return await res.json();
      } catch (e) { console.warn("API fallback:", e); }
    }
    const n = localStore.db.notifications.find(x => x.id === id);
    if (n) {
      n.is_read = true;
      localStore.save();
    }
    return { success: true };
  },

  // 9. Audit Logs
  async getAuditLogs(params = {}) {
    if (this.isBackendLive) {
      try {
        const cleanParams = {};
        Object.keys(params).forEach(k => {
          if (params[k] !== undefined && params[k] !== null && params[k] !== "") {
            cleanParams[k] = params[k];
          }
        });
        const qs = new URLSearchParams(cleanParams).toString();
        const res = await fetch(`${this.baseUrl}/audit?${qs}`, { headers: this.getHeaders() });
        if (res.ok) {
          const json = await res.json();
          return this.wrapCollection(json);
        }
      } catch (e) { console.warn("API fallback:", e); }
    }

    let list = [...localStore.db.audit];
    const q = (params.search || "").toLowerCase();
    if (q) {
      list = list.filter(l => (l.actor + (l.action || '') + (l.record || '') + (l.detail || '')).toLowerCase().includes(q));
    }
    if (params.entity_type) {
      list = list.filter(l => (l.entity_type || '').toUpperCase() === params.entity_type.toUpperCase());
    }

    const page = parseInt(params.page) || 1;
    const limit = parseInt(params.limit) || 25;
    const total = list.length;
    const offset = (page - 1) * limit;
    const items = list.slice(offset, offset + limit).map(l => ({
      id: l.id,
      timestamp: l.time,
      actor: l.actor,
      role: l.role,
      action: l.action,
      entity_type: l.entity_type,
      entity_id: l.record,
      ip_address: "127.0.0.1",
      payload: l.detail
    }));

    return { total, page, limit, items, data: items };
  },

  // 10. Graph
  async getGraphData(institutionId = null) {
    if (this.isBackendLive) {
      try {
        const url = institutionId ? `${this.baseUrl}/graph?institution_id=${institutionId}` : `${this.baseUrl}/graph`;
        const res = await fetch(url, { headers: this.getHeaders() });
        if (res.ok) return await res.json();
      } catch (e) { console.warn("API fallback:", e); }
    }

    // Client-side graph builder
    const db = localStore.db;
    const nodes = [];
    const edges = [];
    const nodeIds = new Set();

    const addNode = (id, label, type, status, details = "") => {
      if (!nodeIds.has(id)) {
        nodeIds.add(id);
        const colorMap = {
          institution: "#1a365d",
          application: "#2563eb",
          document: "#0d9488",
          compliance: "#d97706",
          complaint: "#dc2626",
          evc: "#7c3aed",
          task: "#4f46e5"
        };
        nodes.push({ id, label, type, status, color: colorMap[type] || "#64748b", details });
      }
    };

    const addEdge = (source, target, label) => {
      if (nodeIds.has(source) && nodeIds.has(target)) {
        edges.push({ source, target, label });
      }
    };

    const insts = institutionId ? db.institutions.filter(i => i.id === institutionId) : db.institutions.slice(0, 8);

    insts.forEach(inst => {
      addNode(inst.id, inst.name, "institution", inst.approval_status, `Permanent ID: ${inst.permanent_id}`);

      db.applications.filter(a => a.institution_id === inst.id).forEach(a => {
        addNode(a.id, `${a.type} (${a.current_stage || a.stage})`, "application", a.status, `Progress: ${a.progress}%`);
        addEdge(inst.id, a.id, "SUBMITTED");

        db.evc_schedules.filter(e => e.application_id === a.id).forEach(e => {
          addNode(e.id, `EVC: ${e.scheduled_date}`, "evc", e.status, `Chair: ${e.committee_chair}`);
          addEdge(a.id, e.id, "SCHEDULED_EVC");
        });

        db.documents.filter(d => d.application_id === a.id).forEach(d => {
          addNode(d.id, d.name, "document", d.status, `Type: ${d.document_type || d.type}`);
          addEdge(a.id, d.id, "REQUIRES_DOCUMENT");
        });
      });

      db.compliance.filter(c => c.institution_id === inst.id).forEach(c => {
        addNode(c.id, c.title || c.item, "compliance", c.status, `Due: ${c.due_date || c.due}`);
        addEdge(inst.id, c.id, "OBLIGATED_TO");
      });

      db.complaints.filter(c => c.institution_id === inst.id).forEach(c => {
        addNode(c.id, `${c.bureau}: ${c.category}`, "complaint", c.status, (c.summary || '').slice(0, 50));
        addEdge(inst.id, c.id, "SUBJECT_OF_COMPLAINT");
        if (c.related_case_id && nodeIds.has(c.related_case_id)) {
          addEdge(c.id, c.related_case_id, "POTENTIAL_OVERLAP");
        }
      });
    });

    return { nodes, edges, total_nodes: nodes.length, total_edges: edges.length };
  },

  // 11. Copilot
  async queryCopilot(query, useGemini = false, apiKey = "") {
    if (this.isBackendLive) {
      try {
        const res = await fetch(`${this.baseUrl}/copilot/chat`, {
          method: "POST",
          headers: this.getHeaders(),
          body: JSON.stringify({ query, use_gemini: useGemini, api_key: apiKey })
        });
        if (res.ok) return await res.json();
      } catch (e) { console.warn("API fallback:", e); }
    }

    // Client-side rule engine
    const s = query.toLowerCase();
    const db = localStore.db;
    const citations = [];
    const facts = [];
    const ruleResults = [];
    const recommendations = [];

    if (/flag|deficien|returned|why was|issue|app-/i.test(s)) {
      const app = db.applications[0];
      const docs = db.documents.filter(d => d.institution_id === app.institution_id);
      citations.push({ record_id: app.id, record_type: "Application", title: app.type, status: app.status });
      docs.forEach(d => citations.push({ record_id: d.id, record_type: "Document", title: d.name, status: d.status }));
      facts.push(`Application ${app.id} for ${app.institution_name} is at stage '${app.current_stage || app.stage}' with ${app.deficiency_count || 0} recorded deficiencies.`);
      ruleResults.push("Land lease renewal date is approaching (25-Oct-2026). Faculty cadre ratio requires signed compliance deed.");
      recommendations.push("Issue formal deficiency checklist to institution prior to scheduling Expert Visiting Committee (EVC).");

      return {
        answer: `Application **${app.id}** (${app.type}) was flagged for the following regulatory items:\n\n` +
          docs.map(d => `• **[${d.id}] ${d.name}**: ${d.findings}`).join("\n") +
          `\n\nCurrent stage is **${app.current_stage || app.stage}** assigned to **${app.owner}**.`,
        citations,
        facts,
        rule_results: ruleResults,
        recommendations,
        provider: "Embedded Institutional Knowledge Engine"
      };
    } else if (/deadline|due|compliance|undertaking/i.test(s)) {
      const items = db.compliance.filter(c => /overdue|due soon|action/i.test(c.status));
      items.forEach(c => citations.push({ record_id: c.id, record_type: "Compliance", title: c.title || c.item, status: c.status }));
      facts.push(`Identified ${items.length} obligations requiring attention.`);
      ruleResults.push("Lease deed expiry is within 5 days threshold.");
      recommendations.push("Dispatch reminder notices and verify uploaded renewal deeds.");

      return {
        answer: `There are **${items.length} compliance items** needing attention:\n\n` +
          items.map(c => `• **[${c.id}] ${c.title || c.item}** (${c.institution_name}) — Due: ${c.due_date || c.due} (Status: \`${c.status}\`)`).join("\n"),
        citations,
        facts,
        rule_results: ruleResults,
        recommendations,
        provider: "Embedded Institutional Knowledge Engine"
      };
    } else if (/overlap|case|pgrc|complaint|coordinat/i.test(s)) {
      const pairs = db.complaints.filter(c => c.related_case_id);
      pairs.forEach(c => citations.push({ record_id: c.id, record_type: "Complaint", title: `${c.bureau}: ${c.category}`, status: c.status }));
      facts.push("Detected cross-Bureau correlation on exact Institution Permanent ID match.");
      ruleResults.push("Overlap score: 94%. Subject matter: Excess intake admissions.");
      recommendations.push("Authorize joint hearing while maintaining separate case records.");

      return {
        answer: `**Potential Case Overlap Detected:**\n\n` +
          `• **[PGRC-26-01842]** (Public Grievance Redressal Cell): Excess intake complaint.\n` +
          `• **[RB-26-00917]** (Regulation Bureau): Internal audit admission discrepancy query.\n\n` +
          `**Rationale:** Exact Institution ID match (\`1-10482931\`). Both matters concern B.Tech CSE intake. Coordination link recommended.`,
        citations,
        facts,
        rule_results: ruleResults,
        recommendations,
        provider: "Embedded Institutional Knowledge Engine"
      };
    } else {
      const inst = db.institutions[0];
      citations.push({ record_id: inst.id, record_type: "Institution", title: inst.name, status: inst.approval_status });
      facts.push(`Institution ${inst.name} holds approval for ${inst.programmes_count} programmes with ${inst.total_intake} total intake.`);
      ruleResults.push("Permanent ID 1-10482931 verified against AICTE Directory.");
      recommendations.push("Check active applications and ensure timely lease deed submission.");

      return {
        answer: `### Institution Summary: **${inst.name}**\n\n` +
          `• **Permanent ID:** \`${inst.permanent_id}\` | **State:** ${inst.state}\n` +
          `• **Status:** \`${inst.approval_status}\` (${inst.approval_period})\n` +
          `• **Affiliation:** ${inst.affiliation}\n` +
          `• **Intake:** ${inst.total_intake} seats across ${inst.programmes_count} approved programmes.`,
        citations,
        facts,
        rule_results: ruleResults,
        recommendations,
        provider: "Embedded Institutional Knowledge Engine"
      };
    }
  }
};

// Expose universally
window.API = API;
window.ApiService = API;

// Auto-check connectivity
API.init();
