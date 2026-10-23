/**
 * Module 13: AI Copilot — Evidence-Grounded Institutional Intelligence
 */
const CopilotModule = {
  chatHistory: [
    {
      sender: "bot",
      text: "Hello, Officer. I am the **AICTE ONE Institutional Intelligence Assistant**. I synthesize ground-truth records across institutional registries, application scrutiny checklists, document verification findings, and multi-bureau grievance dossiers. Every answer references verified stored entity IDs.",
      citations: [],
      provider: "AICTE ONE Regulatory Rule Engine"
    }
  ],

  async render() {
    const historyHtml = this.chatHistory.map(msg => `
      <div class="chat-bubble ${msg.sender}">
        <div style="white-space:pre-line">${this.formatMarkdown(msg.text)}</div>
        ${msg.citations && msg.citations.length ? `
          <div style="margin-top:8px;padding-top:6px;border-top:1px solid rgba(0,0,0,0.08);display:flex;gap:6px;flex-wrap:wrap">
            <span style="font-size:10px;font-weight:700;color:#64748b;margin-right:4px">Citations:</span>
            ${msg.citations.map(c => `
              <span class="pill blue" style="font-size:10px;cursor:pointer" onclick="CopilotModule.jumpToCitation('${c.record_type}', '${c.record_id}')">
                ${c.record_id} (${c.record_type})
              </span>
            `).join("")}
          </div>
        ` : ''}
        ${msg.provider ? `<div style="font-size:9.5px;color:#94a3b8;margin-top:4px">Source: ${escapeHtml(msg.provider)}</div>` : ''}
      </div>
    `).join("");

    return `
      <div class="page-header" style="display:flex;align-items:center;gap:16px">
        <img src="assets/img/shankh-logo.png" alt="SHANKH AI" style="width:52px;height:52px;object-fit:contain;background:#fff;border-radius:12px;padding:4px;border:1px solid #cbd5e1;box-shadow:0 2px 4px rgba(0,0,0,0.06);flex-shrink:0">
        <div style="flex:1">
          <div class="page-eyebrow">Project SHANKH · Cognitive Reasoning Engine</div>
          <h1>AI Copilot</h1>
          <p>Evidence-grounded case analysis, statutory rule explanation, and cross-dossier synthesis.</p>
        </div>
        <div class="header-action-group">
          <div style="display:flex;align-items:center;gap:8px">
            <label style="font-size:11px;font-weight:600;color:#64748b">AI Provider:</label>
            <select class="filter-select" id="copilot-provider-select" onchange="CopilotModule.handleProviderChange(this.value)">
              <option value="local">Embedded Regulatory Rules Engine (Offline)</option>
              <option value="gemini">Google Gemini 2.5 Flash API (Connected)</option>
            </select>
          </div>
          <button class="btn sm" onclick="CopilotModule.openApiKeyModal()">⚙ Set Gemini Key</button>
        </div>
      </div>

      <!-- Main Layout -->
      <div class="grid-2">
        <!-- Chatbox Container -->
        <div class="copilot-container">
          <div class="copilot-messages" id="copilot-chat-box">
            ${historyHtml}
          </div>

          <!-- Prompt Chips -->
          <div class="prompt-chips">
            <button class="prompt-chip" onclick="CopilotModule.askPrompt('Why was APP-2026-0842 flagged?')">Why was APP-2026-0842 flagged?</button>
            <button class="prompt-chip" onclick="CopilotModule.askPrompt('Which compliance deadlines need immediate attention?')">Upcoming compliance deadlines</button>
            <button class="prompt-chip" onclick="CopilotModule.askPrompt('Show potential overlapping complaint cases')">Cross-Bureau complaint overlaps</button>
            <button class="prompt-chip" onclick="CopilotModule.askPrompt('Summarize Noida Institute of Engineering & Technology')">Institution 360° summary</button>
          </div>

          <!-- Input Bar -->
          <div class="chat-input-row">
            <input
              id="copilot-input"
              placeholder="Ask a question about an institution, application, or compliance deadline…"
              onkeydown="if(event.key==='Enter')CopilotModule.sendChat()"
            />
            <button class="btn primary" onclick="CopilotModule.sendChat()">Send ↑</button>
          </div>
        </div>

        <!-- Right Side: Grounding Principles & Capabilities -->
        <div style="display:flex;flex-direction:column;gap:18px">
          <div class="panel">
            <div class="panel-header"><h3>Evidence-Linked Retrieval Architecture</h3></div>
            <div class="panel-body" style="font-size:12px;color:#334155;line-height:1.6">
              <div style="display:flex;gap:10px;margin-bottom:12px">
                <span class="pill green" style="align-self:flex-start">✓</span>
                <div>
                  <strong>Deterministic Rule Verification:</strong>
                  <p class="muted" style="font-size:11px">Compares dates, Permanent IDs, and checklist items against stored records.</p>
                </div>
              </div>
              <div style="display:flex;gap:10px;margin-bottom:12px">
                <span class="pill blue" style="align-self:flex-start">⌕</span>
                <div>
                  <strong>Specific Record Citations:</strong>
                  <p class="muted" style="font-size:11px">Every answer quotes verified entity IDs (e.g. <code>APP-2026-0842</code>, <code>DOC-7809</code>) with clickable links.</p>
                </div>
              </div>
              <div style="display:flex;gap:10px">
                <span class="pill amber" style="align-self:flex-start">!</span>
                <div>
                  <strong>No Fabricated Regulatory Advice:</strong>
                  <p class="muted" style="font-size:11px">Clearly differentiates retrieved institutional facts, rule findings, and administrative recommendations.</p>
                </div>
              </div>
            </div>
          </div>

          <div class="panel">
            <div class="panel-header"><h3>Example Investigative Queries</h3></div>
            <div class="panel-body" style="font-size:11.5px;color:#475569;display:flex;flex-direction:column;gap:10px">
              <div style="background:#f8fafc;padding:9px;border-radius:6px;border:1px solid #e2e8f0;cursor:pointer" onclick="CopilotModule.askPrompt('What evidence is still outstanding before the next review for APP-2026-0842?')">
                <b>Stage Readiness:</b> "What evidence is still outstanding before the next review?"
              </div>
              <div style="background:#f8fafc;padding:9px;border-radius:6px;border:1px solid #e2e8f0;cursor:pointer" onclick="CopilotModule.askPrompt('Which pending document could block an application stage?')">
                <b>Bottleneck Analysis:</b> "Which pending document could block an application stage?"
              </div>
              <div style="background:#f8fafc;padding:9px;border-radius:6px;border:1px solid #e2e8f0;cursor:pointer" onclick="CopilotModule.askPrompt('Why were PGRC-26-01842 and RB-26-00917 flagged as potentially overlapping?')">
                <b>Case Correlation:</b> "Why were PGRC-26-01842 and RB-26-00917 flagged as related?"
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  },

  formatMarkdown(text) {
    if (!text) return "";
    return escapeHtml(text)
      .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
      .replace(/\*(.*?)\*/g, '<i>$1</i>')
      .replace(/`([^`]+)`/g, '<code style="background:#f1f5f9;padding:1px 4px;border-radius:4px;color:#2563eb">$1</code>');
  },

  async sendChat() {
    const input = document.getElementById("copilot-input");
    const query = input.value.trim();
    if (!query) return;

    this.chatHistory.push({ sender: "user", text: query });
    input.value = "";
    App.refresh();

    // Scroll chat to bottom
    setTimeout(() => {
      const box = document.getElementById("copilot-chat-box");
      if (box) box.scrollTop = box.scrollHeight;
    }, 50);

    const providerSelect = document.getElementById("copilot-provider-select");
    const useGemini = providerSelect ? providerSelect.value === "gemini" : false;
    const apiKey = localStorage.getItem("aicte_gemini_api_key") || "";

    const response = await API.queryCopilot(query, useGemini, apiKey);

    this.chatHistory.push({
      sender: "bot",
      text: response.answer,
      citations: response.citations || [],
      provider: response.provider
    });

    App.refresh();
    setTimeout(() => {
      const box = document.getElementById("copilot-chat-box");
      if (box) box.scrollTop = box.scrollHeight;
    }, 50);
  },

  askPrompt(q) {
    const input = document.getElementById("copilot-input");
    if (input) {
      input.value = q;
      this.sendChat();
    }
  },

  jumpToCitation(type, id) {
    if (type.toLowerCase() === 'application') App.navigate('applications', { id });
    else if (type.toLowerCase() === 'document') App.navigate('verification', { id });
    else if (type.toLowerCase() === 'compliance') App.navigate('compliance', { id });
    else if (type.toLowerCase() === 'complaint') App.navigate('complaints', { id });
    else if (type.toLowerCase() === 'institution') App.navigate('digitalTwin', { id });
  },

  handleProviderChange(val) {
    if (val === "gemini" && !localStorage.getItem("aicte_gemini_api_key")) {
      this.openApiKeyModal();
    }
  },

  openApiKeyModal() {
    const existing = localStorage.getItem("aicte_gemini_api_key") || "";
    App.openModal(
      "Configure Google Gemini API Provider",
      `
        <p style="font-size:12px;color:#64748b;margin-bottom:12px">
          Optionally provide a Google Gemini API key to enable generative synthesis grounded in AICTE ONE institutional records.
        </p>
        <div class="form-group full">
          <label class="form-label">Gemini API Key</label>
          <input class="form-control" type="password" id="gemini-key-input" value="${escapeHtml(existing)}" placeholder="AIzaSy..." />
        </div>
        <p style="font-size:11px;color:#94a3b8;margin-top:8px">
          The API key is securely stored in this browser session only. If omitted, the platform uses the high-precision embedded Regulatory Rules Engine.
        </p>
      `,
      `
        <button class="btn" onclick="App.closeModal()">Cancel</button>
        <button class="btn primary" onclick="CopilotModule.saveApiKey()">Save API Key</button>
      `
    );
  },

  saveApiKey() {
    const key = document.getElementById("gemini-key-input").value.trim();
    if (key) {
      localStorage.setItem("aicte_gemini_api_key", key);
      App.toast("Gemini API key configured for Copilot.");
    } else {
      localStorage.removeItem("aicte_gemini_api_key");
      App.toast("Reverted to local rule engine.");
    }
    App.closeModal();
    App.refresh();
  }
};

window.CopilotModule = CopilotModule;
