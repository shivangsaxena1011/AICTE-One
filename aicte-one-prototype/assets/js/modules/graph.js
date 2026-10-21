/**
 * Module 12: Interactive Regulatory Intelligence Graph
 * HTML5 Canvas Node-Link Explorer with Physics Simulation & Inspector
 */
const GraphModule = {
  canvas: null,
  ctx: null,
  nodes: [],
  edges: [],
  selectedNode: null,
  filterTypes: {
    institution: true,
    application: true,
    document: true,
    compliance: true,
    complaint: true,
    task: true
  },
  transform: { x: 0, y: 0, scale: 1 },
  isDragging: false,
  draggedNode: null,
  lastMouse: { x: 0, y: 0 },
  animationId: null,

  async render() {
    return `
      <div class="page-header">
        <div>
          <div class="page-eyebrow">Visual Knowledge Graph</div>
          <h1>Regulatory Intelligence Graph</h1>
          <p>Interactive relationship graph mapping connections between institutions, applications, evidence documents, grievances, and officials.</p>
        </div>
        <div class="header-action-group">
          <button class="btn" onclick="GraphModule.resetView()">⟲ Reset Graph View</button>
          <button class="btn primary" onclick="GraphModule.loadData()">⚡ Re-layout Graph</button>
        </div>
      </div>

      <!-- Graph Toolbar & Filter Badges -->
      <div class="panel" style="margin-bottom:14px">
        <div style="padding:10px 16px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;font-size:11.5px">
          <b>Filter Entity Types:</b>
          <label style="display:flex;align-items:center;gap:5px;cursor:pointer">
            <input type="checkbox" checked onchange="GraphModule.toggleType('institution', this.checked)">
            <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#1a365d"></span> Institutions
          </label>
          <label style="display:flex;align-items:center;gap:5px;cursor:pointer">
            <input type="checkbox" checked onchange="GraphModule.toggleType('application', this.checked)">
            <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#2563eb"></span> Applications
          </label>
          <label style="display:flex;align-items:center;gap:5px;cursor:pointer">
            <input type="checkbox" checked onchange="GraphModule.toggleType('document', this.checked)">
            <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#0d9488"></span> Documents
          </label>
          <label style="display:flex;align-items:center;gap:5px;cursor:pointer">
            <input type="checkbox" checked onchange="GraphModule.toggleType('compliance', this.checked)">
            <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#d97706"></span> Compliance
          </label>
          <label style="display:flex;align-items:center;gap:5px;cursor:pointer">
            <input type="checkbox" checked onchange="GraphModule.toggleType('complaint', this.checked)">
            <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#dc2626"></span> Complaints
          </label>
          <label style="display:flex;align-items:center;gap:5px;cursor:pointer">
            <input type="checkbox" checked onchange="GraphModule.toggleType('task', this.checked)">
            <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#4f46e5"></span> Action Tasks
          </label>
        </div>
      </div>

      <!-- Graph Canvas Container -->
      <div class="graph-canvas-container">
        <canvas id="graph-canvas"></canvas>

        <!-- Inspector Drawer -->
        <div class="graph-inspector-panel" id="graph-inspector">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <span class="pill blue" id="inspector-type">Node</span>
            <button class="btn sm" onclick="GraphModule.closeInspector()" style="padding:2px 6px">✕</button>
          </div>
          <strong id="inspector-title" style="display:block;font-size:13px;color:#ffffff;margin-bottom:4px"></strong>
          <div id="inspector-id" style="font-size:11px;color:#94a3b8;margin-bottom:8px"></div>
          <div id="inspector-details" style="font-size:11px;color:#cbd5e1;line-height:1.5;margin-bottom:12px"></div>
          <div id="inspector-status" style="margin-bottom:12px"></div>
          <button class="btn sm primary" style="width:100%" id="inspector-jump-btn">Open Record Profile →</button>
        </div>

        <!-- Controls -->
        <div class="graph-controls">
          <button class="btn sm" onclick="GraphModule.zoom(1.2)">＋ Zoom In</button>
          <button class="btn sm" onclick="GraphModule.zoom(0.8)">－ Zoom Out</button>
          <button class="btn sm" onclick="GraphModule.resetView()">⟲ Center</button>
        </div>
      </div>
    `;
  },

  async initCanvas() {
    this.canvas = document.getElementById("graph-canvas");
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext("2d");
    this.resizeCanvas();
    window.addEventListener("resize", () => this.resizeCanvas());

    this.setupEvents();
    await this.loadData();
    this.startSimulation();
  },

  resizeCanvas() {
    if (!this.canvas) return;
    const rect = this.canvas.parentElement.getBoundingClientRect();
    this.canvas.width = rect.width;
    this.canvas.height = rect.height;
  },

  async loadData() {
    const raw = await API.getGraphData();
    const w = this.canvas ? this.canvas.width : 900;
    const h = this.canvas ? this.canvas.height : 500;

    // Initialize node positions in a radial cluster
    this.nodes = raw.nodes.map((n, idx) => {
      const angle = (idx / raw.nodes.length) * 2 * Math.PI;
      const radius = 120 + Math.random() * 150;
      return {
        ...n,
        x: w / 2 + Math.cos(angle) * radius,
        y: h / 2 + Math.sin(angle) * radius,
        vx: 0,
        vy: 0,
        radius: n.type === 'institution' ? 18 : 13
      };
    });

    this.edges = raw.edges;
    this.resetView();
  },

  startSimulation() {
    const tick = () => {
      this.updatePhysics();
      this.draw();
      this.animationId = requestAnimationFrame(tick);
    };
    if (this.animationId) cancelAnimationFrame(this.animationId);
    this.animationId = requestAnimationFrame(tick);
  },

  updatePhysics() {
    if (!this.nodes.length) return;

    // Repulsion between nodes
    for (let i = 0; i < this.nodes.length; i++) {
      for (let j = i + 1; j < this.nodes.length; j++) {
        const a = this.nodes[i];
        const b = this.nodes[j];
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        if (dist < 180) {
          const force = (180 - dist) / dist * 0.04;
          if (a !== this.draggedNode) {
            a.vx -= dx * force;
            a.vy -= dy * force;
          }
          if (b !== this.draggedNode) {
            b.vx += dx * force;
            b.vy += dy * force;
          }
        }
      }
    }

    // Spring attraction along edges
    this.edges.forEach(e => {
      const a = this.nodes.find(n => n.id === e.source);
      const b = this.nodes.find(n => n.id === e.target);
      if (a && b) {
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = (dist - 100) * 0.003;
        if (a !== this.draggedNode) {
          a.vx += dx * force;
          a.vy += dy * force;
        }
        if (b !== this.draggedNode) {
          b.vx -= dx * force;
          b.vy -= dy * force;
        }
      }
    });

    // Center gravity & damping
    const cx = this.canvas.width / 2;
    const cy = this.canvas.height / 2;
    this.nodes.forEach(n => {
      if (n !== this.draggedNode) {
        n.vx += (cx - n.x) * 0.0005;
        n.vy += (cy - n.y) * 0.0005;
        n.vx *= 0.85;
        n.vy *= 0.85;
        n.x += n.vx;
        n.y += n.vy;
      }
    });
  },

  draw() {
    if (!this.ctx || !this.canvas) return;
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    ctx.save();
    ctx.translate(this.transform.x, this.transform.y);
    ctx.scale(this.transform.scale, this.transform.scale);

    // Draw Edges
    this.edges.forEach(e => {
      const src = this.nodes.find(n => n.id === e.source);
      const tgt = this.nodes.find(n => n.id === e.target);
      if (src && tgt && this.filterTypes[src.type] && this.filterTypes[tgt.type]) {
        ctx.beginPath();
        ctx.moveTo(src.x, src.y);
        ctx.lineTo(tgt.x, tgt.y);
        ctx.strokeStyle = "rgba(148, 163, 184, 0.25)";
        ctx.lineWidth = 1.2;
        ctx.stroke();

        // Edge label in subtle text
        const midX = (src.x + tgt.x) / 2;
        const midY = (src.y + tgt.y) / 2;
        ctx.fillStyle = "rgba(148, 163, 184, 0.6)";
        ctx.font = "8.5px Inter, sans-serif";
        ctx.fillText(e.label, midX - 15, midY - 3);
      }
    });

    // Draw Nodes
    this.nodes.forEach(n => {
      if (!this.filterTypes[n.type]) return;

      const isSelected = this.selectedNode && this.selectedNode.id === n.id;

      // Glow / Selection ring
      if (isSelected) {
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius + 6, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(59, 130, 246, 0.4)";
        ctx.fill();
      }

      // Main Node Circle
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
      ctx.fillStyle = n.color || "#2563eb";
      ctx.fill();
      ctx.strokeStyle = isSelected ? "#ffffff" : "rgba(255, 255, 255, 0.7)";
      ctx.lineWidth = isSelected ? 2.5 : 1.5;
      ctx.stroke();

      // Node label
      ctx.fillStyle = "#f8fafc";
      ctx.font = n.type === 'institution' ? "bold 10.5px Inter" : "9.5px Inter";
      ctx.textAlign = "center";
      const shortLabel = n.label.length > 20 ? n.label.slice(0, 18) + "…" : n.label;
      ctx.fillText(shortLabel, n.x, n.y + n.radius + 12);
    });

    ctx.restore();
  },

  setupEvents() {
    this.canvas.addEventListener("mousedown", (e) => this.handleMouseDown(e));
    window.addEventListener("mousemove", (e) => this.handleMouseMove(e));
    window.addEventListener("mouseup", () => this.handleMouseUp());
    this.canvas.addEventListener("wheel", (e) => this.handleWheel(e));
  },

  screenToWorld(sx, sy) {
    const rect = this.canvas.getBoundingClientRect();
    const x = (sx - rect.left - this.transform.x) / this.transform.scale;
    const y = (sy - rect.top - this.transform.y) / this.transform.scale;
    return { x, y };
  },

  handleMouseDown(e) {
    const { x, y } = this.screenToWorld(e.clientX, e.clientY);
    const clicked = this.nodes.find(n => {
      if (!this.filterTypes[n.type]) return false;
      const dx = n.x - x;
      const dy = n.y - y;
      return Math.sqrt(dx * dx + dy * dy) <= n.radius + 4;
    });

    if (clicked) {
      this.draggedNode = clicked;
      this.selectNode(clicked);
    } else {
      this.isDragging = true;
      this.lastMouse = { x: e.clientX, y: e.clientY };
    }
  },

  handleMouseMove(e) {
    if (this.draggedNode) {
      const { x, y } = this.screenToWorld(e.clientX, e.clientY);
      this.draggedNode.x = x;
      this.draggedNode.y = y;
      this.draggedNode.vx = 0;
      this.draggedNode.vy = 0;
    } else if (this.isDragging) {
      const dx = e.clientX - this.lastMouse.x;
      const dy = e.clientY - this.lastMouse.y;
      this.transform.x += dx;
      this.transform.y += dy;
      this.lastMouse = { x: e.clientX, y: e.clientY };
    }
  },

  handleMouseUp() {
    this.draggedNode = null;
    this.isDragging = false;
  },

  handleWheel(e) {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    this.zoom(zoomFactor);
  },

  zoom(factor) {
    this.transform.scale = Math.max(0.4, Math.min(2.5, this.transform.scale * factor));
  },

  resetView() {
    this.transform = { x: 0, y: 0, scale: 1 };
  },

  selectNode(node) {
    this.selectedNode = node;
    const p = document.getElementById("graph-inspector");
    if (!p) return;
    p.style.display = "block";
    document.getElementById("inspector-type").textContent = node.type.toUpperCase();
    document.getElementById("inspector-title").textContent = node.label;
    document.getElementById("inspector-id").textContent = `Entity ID: ${node.id}`;
    document.getElementById("inspector-details").textContent = node.details || "No further details available.";
    document.getElementById("inspector-status").innerHTML = renderPill(node.status);

    const jumpBtn = document.getElementById("inspector-jump-btn");
    jumpBtn.onclick = () => {
      if (node.type === 'institution') App.navigate('digital-twin', { id: node.id });
      else if (node.type === 'application') App.navigate('applications', { id: node.id });
      else if (node.type === 'document') App.navigate('verification', { id: node.id });
      else if (node.type === 'compliance') App.navigate('compliance', { id: node.id });
      else if (node.type === 'complaint') App.navigate('complaints', { id: node.id });
      else if (node.type === 'task') App.navigate('tasks', { id: node.id });
    };
  },

  closeInspector() {
    const p = document.getElementById("graph-inspector");
    if (p) p.style.display = "none";
    this.selectedNode = null;
  },

  toggleType(type, isChecked) {
    this.filterTypes[type] = isChecked;
  }
};

window.GraphModule = GraphModule;
