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
      <div class="space-y-5">
        <!-- Page Header -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
          <div>
            <div class="text-[11px] font-mono uppercase tracking-wider text-[#a73a00] font-bold flex items-center gap-1.5">
              <span>Apex Visual Knowledge Architecture</span>
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              <span class="text-slate-400">Live Physics Network</span>
            </div>
            <h1 class="font-headline text-xl sm:text-2xl font-extrabold text-[#001332] tracking-tight">Regulatory Intelligence Graph</h1>
            <p class="text-xs text-slate-500 mt-0.5">
              Multi-dimensional ontology connecting institutions, approval scrutinies, evidence documents, vigilance complaints & official actions.
            </p>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <button class="btn btn-secondary text-xs flex items-center gap-1.5" onclick="GraphModule.resetView()" title="Center & Reset Zoom">
              <span class="material-symbols-outlined text-[16px]">filter_center_focus</span>
              <span>Reset View</span>
            </button>
            <button class="btn btn-primary text-xs flex items-center gap-1.5" onclick="GraphModule.loadData()" title="Re-simulate Force Physics">
              <span class="material-symbols-outlined text-[16px]">refresh</span>
              <span>Re-layout Graph</span>
            </button>
          </div>
        </div>

        <!-- Topology Summary Metric KPI Cards -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div class="card p-3.5 bg-white border border-slate-200 shadow-xs flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center shrink-0">
              <span class="material-symbols-outlined text-blue-600 text-xl">hub</span>
            </div>
            <div>
              <div class="text-[10px] font-mono uppercase text-slate-500 font-semibold">Active Entities</div>
              <div class="text-lg font-extrabold font-mono text-[#001332]" id="graph-stat-nodes">57</div>
            </div>
          </div>
          <div class="card p-3.5 bg-white border border-slate-200 shadow-xs flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-indigo-50 border border-indigo-200 flex items-center justify-center shrink-0">
              <span class="material-symbols-outlined text-indigo-600 text-xl">linear_scale</span>
            </div>
            <div>
              <div class="text-[10px] font-mono uppercase text-slate-500 font-semibold">Statutory Links</div>
              <div class="text-lg font-extrabold font-mono text-[#001332]" id="graph-stat-edges">50</div>
            </div>
          </div>
          <div class="card p-3.5 bg-white border border-slate-200 shadow-xs flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-rose-50 border border-rose-200 flex items-center justify-center shrink-0">
              <span class="material-symbols-outlined text-rose-600 text-xl">warning</span>
            </div>
            <div>
              <div class="text-[10px] font-mono uppercase text-slate-500 font-semibold">Clash Clusters</div>
              <div class="text-lg font-extrabold font-mono text-rose-700" id="graph-stat-clashes">8</div>
            </div>
          </div>
          <div class="card p-3.5 bg-white border border-slate-200 shadow-xs flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center shrink-0">
              <span class="material-symbols-outlined text-emerald-600 text-xl">schema</span>
            </div>
            <div>
              <div class="text-[10px] font-mono uppercase text-slate-500 font-semibold">Network Modularity</div>
              <div class="text-lg font-extrabold font-mono text-emerald-800" id="graph-stat-modularity">0.42</div>
            </div>
          </div>
        </div>

        <!-- NEW: Graph Intelligence Analytics Grid (Donut Chart + Degree Centrality Histogram) -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          
          <!-- Chart 1: Entity Distribution Donut Breakdown -->
          <div class="card p-4 sm:p-5 bg-white border border-slate-200 shadow-xs">
            <div class="flex items-center justify-between mb-3">
              <div>
                <h3 class="text-sm font-bold text-[#001332] flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-blue-600 text-[18px]">donut_large</span>
                  <span>Entity Distribution Breakdown</span>
                </h3>
                <p class="text-[11px] text-slate-500">Proportional classification across regulatory entity types</p>
              </div>
              <span class="badge badge-info text-[10px]">6 Categories</span>
            </div>

            <div class="flex flex-col sm:flex-row items-center justify-around gap-4 pt-1">
              <!-- Donut Canvas -->
              <div class="relative shrink-0 flex items-center justify-center">
                <canvas id="graph-donut-canvas" width="180" height="180" class="w-[150px] h-[150px]"></canvas>
              </div>

              <!-- Legend & Breakdown Table -->
              <div class="grid grid-cols-2 gap-x-4 gap-y-2 text-xs w-full sm:w-auto flex-1 max-w-xs">
                <div class="flex items-center justify-between gap-2 p-1.5 rounded bg-slate-50 border border-slate-100">
                  <span class="flex items-center gap-1.5 text-slate-700">
                    <span class="w-2.5 h-2.5 rounded-full bg-[#1a365d]"></span>
                    <span>Institutions</span>
                  </span>
                  <span class="font-mono font-bold text-[#001332]" id="legend-cnt-inst">10</span>
                </div>
                <div class="flex items-center justify-between gap-2 p-1.5 rounded bg-slate-50 border border-slate-100">
                  <span class="flex items-center gap-1.5 text-slate-700">
                    <span class="w-2.5 h-2.5 rounded-full bg-[#2563eb]"></span>
                    <span>Applications</span>
                  </span>
                  <span class="font-mono font-bold text-[#001332]" id="legend-cnt-app">8</span>
                </div>
                <div class="flex items-center justify-between gap-2 p-1.5 rounded bg-slate-50 border border-slate-100">
                  <span class="flex items-center gap-1.5 text-slate-700">
                    <span class="w-2.5 h-2.5 rounded-full bg-[#0d9488]"></span>
                    <span>Documents</span>
                  </span>
                  <span class="font-mono font-bold text-[#001332]" id="legend-cnt-doc">12</span>
                </div>
                <div class="flex items-center justify-between gap-2 p-1.5 rounded bg-slate-50 border border-slate-100">
                  <span class="flex items-center gap-1.5 text-slate-700">
                    <span class="w-2.5 h-2.5 rounded-full bg-[#d97706]"></span>
                    <span>Compliance</span>
                  </span>
                  <span class="font-mono font-bold text-[#001332]" id="legend-cnt-comp">10</span>
                </div>
                <div class="flex items-center justify-between gap-2 p-1.5 rounded bg-slate-50 border border-slate-100">
                  <span class="flex items-center gap-1.5 text-slate-700">
                    <span class="w-2.5 h-2.5 rounded-full bg-[#dc2626]"></span>
                    <span>Complaints</span>
                  </span>
                  <span class="font-mono font-bold text-[#001332]" id="legend-cnt-cmpl">9</span>
                </div>
                <div class="flex items-center justify-between gap-2 p-1.5 rounded bg-slate-50 border border-slate-100">
                  <span class="flex items-center gap-1.5 text-slate-700">
                    <span class="w-2.5 h-2.5 rounded-full bg-[#4f46e5]"></span>
                    <span>Action Tasks</span>
                  </span>
                  <span class="font-mono font-bold text-[#001332]" id="legend-cnt-task">8</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Chart 2: Inter-Bureau Connectivity Histogram -->
          <div class="card p-4 sm:p-5 bg-white border border-slate-200 shadow-xs">
            <div class="flex items-center justify-between mb-3">
              <div>
                <h3 class="text-sm font-bold text-[#001332] flex items-center gap-1.5">
                  <span class="material-symbols-outlined text-indigo-600 text-[18px]">bar_chart</span>
                  <span>Cross-Bureau Connectivity Histogram</span>
                </h3>
                <p class="text-[11px] text-slate-500">Degree centrality distribution (nodes by number of active inter-links)</p>
              </div>
              <span class="badge badge-neutral text-[10px]">Degree Spread</span>
            </div>

            <!-- Histogram Canvas -->
            <div class="w-full flex items-center justify-center pt-1">
              <canvas id="graph-histogram-canvas" width="340" height="150" class="w-full max-w-[340px] h-[150px]"></canvas>
            </div>
          </div>

        </div>

        <!-- Graph Filter & Search Toolbar -->
        <div class="card p-3 sm:p-4 bg-white border border-slate-200 shadow-xs flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          <!-- Live Node Search -->
          <div class="relative flex-1 max-w-md">
            <span class="material-symbols-outlined absolute left-3 top-2 text-slate-400 text-[18px]">search</span>
            <input 
              type="text" 
              id="graph-search-input" 
              placeholder="Search entity by ID or Name (e.g., INST-10482, CMP, APP)..." 
              oninput="GraphModule.handleSearch(this.value)"
              class="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <!-- Filter Badges -->
          <div class="flex items-center gap-3 flex-wrap text-xs font-medium text-slate-600">
            <span class="text-slate-400 font-semibold text-[11px]">Filters:</span>
            <label class="flex items-center gap-1.5 cursor-pointer hover:text-navy-900 transition-colors">
              <input type="checkbox" checked onchange="GraphModule.toggleType('institution', this.checked)">
              <span class="w-2.5 h-2.5 rounded-full bg-[#1a365d]"></span>
              <span>Institutions</span>
            </label>
            <label class="flex items-center gap-1.5 cursor-pointer hover:text-navy-900 transition-colors">
              <input type="checkbox" checked onchange="GraphModule.toggleType('application', this.checked)">
              <span class="w-2.5 h-2.5 rounded-full bg-[#2563eb]"></span>
              <span>Applications</span>
            </label>
            <label class="flex items-center gap-1.5 cursor-pointer hover:text-navy-900 transition-colors">
              <input type="checkbox" checked onchange="GraphModule.toggleType('document', this.checked)">
              <span class="w-2.5 h-2.5 rounded-full bg-[#0d9488]"></span>
              <span>Documents</span>
            </label>
            <label class="flex items-center gap-1.5 cursor-pointer hover:text-navy-900 transition-colors">
              <input type="checkbox" checked onchange="GraphModule.toggleType('compliance', this.checked)">
              <span class="w-2.5 h-2.5 rounded-full bg-[#d97706]"></span>
              <span>Compliance</span>
            </label>
            <label class="flex items-center gap-1.5 cursor-pointer hover:text-navy-900 transition-colors">
              <input type="checkbox" checked onchange="GraphModule.toggleType('complaint', this.checked)">
              <span class="w-2.5 h-2.5 rounded-full bg-[#dc2626]"></span>
              <span>Complaints</span>
            </label>
            <label class="flex items-center gap-1.5 cursor-pointer hover:text-navy-900 transition-colors">
              <input type="checkbox" checked onchange="GraphModule.toggleType('task', this.checked)">
              <span class="w-2.5 h-2.5 rounded-full bg-[#4f46e5]"></span>
              <span>Tasks</span>
            </label>
          </div>
        </div>

        <!-- Graph Canvas Container -->
        <div class="graph-canvas-container relative rounded-xl overflow-hidden border border-slate-700 bg-[#001332] shadow-xl">
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

          <!-- Zoom / Pan Controls -->
          <div class="graph-controls">
            <button id="btn-zoom-in" class="btn sm" onclick="GraphModule.zoom(1.2)">＋ Zoom In</button>
            <button id="btn-zoom-out" class="btn sm" onclick="GraphModule.zoom(0.8)">－ Zoom Out</button>
            <button id="btn-reset-zoom" class="btn sm" onclick="GraphModule.resetView()">⟲ Center</button>
          </div>
        </div>
      </div>
    `;
  },

  async initCanvas() {
    this.canvas = document.getElementById("graph-canvas");
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext("2d");
    this.resizeCanvas();
    window.removeEventListener("resize", this._onResize);
    this._onResize = () => this.resizeCanvas();
    window.addEventListener("resize", this._onResize);

    this.setupEvents();
    await this.loadData();
    this.startSimulation();
  },

  postRender() {
    // Canvas requires DOM to be painted before sizing
    setTimeout(async () => {
      await this.initCanvas();
      this.renderAnalyticsCharts();
    }, 50);
  },

  handleSearch(query) {
    const q = (query || '').trim().toLowerCase();
    if (!q) {
      this.searchMatchId = null;
      return;
    }
    const match = this.nodes.find(n => 
      n.id.toLowerCase().includes(q) || 
      n.label.toLowerCase().includes(q)
    );
    if (match) {
      this.searchMatchId = match.id;
      this.selectNode(match);
      // Pan camera smoothly to center node
      const cx = this.canvas.width / 2;
      const cy = this.canvas.height / 2;
      this.transform.x = cx - match.x * this.transform.scale;
      this.transform.y = cy - match.y * this.transform.scale;
    } else {
      this.searchMatchId = null;
    }
  },

  renderAnalyticsCharts() {
    if (!this.nodes || !this.nodes.length) return;

    // 1. Calculate Entity Counts
    const typeCounts = {
      institution: 0,
      application: 0,
      document: 0,
      compliance: 0,
      complaint: 0,
      task: 0
    };
    this.nodes.forEach(n => {
      if (typeCounts[n.type] !== undefined) typeCounts[n.type]++;
    });

    // Update legend numbers
    const elInst = document.getElementById('legend-cnt-inst');
    if (elInst) elInst.textContent = typeCounts.institution;
    const elApp = document.getElementById('legend-cnt-app');
    if (elApp) elApp.textContent = typeCounts.application;
    const elDoc = document.getElementById('legend-cnt-doc');
    if (elDoc) elDoc.textContent = typeCounts.document;
    const elComp = document.getElementById('legend-cnt-comp');
    if (elComp) elComp.textContent = typeCounts.compliance;
    const elCmpl = document.getElementById('legend-cnt-cmpl');
    if (elCmpl) elCmpl.textContent = typeCounts.complaint;
    const elTask = document.getElementById('legend-cnt-task');
    if (elTask) elTask.textContent = typeCounts.task;

    // Update Top KPI Cards
    const statNodes = document.getElementById('graph-stat-nodes');
    if (statNodes) statNodes.textContent = this.nodes.length;
    const statEdges = document.getElementById('graph-stat-edges');
    if (statEdges) statEdges.textContent = this.edges.length;

    // 2. Draw Donut Chart
    this.drawDonutChart(typeCounts);

    // 3. Degree Centrality Distribution
    const degreeMap = {};
    this.nodes.forEach(n => { degreeMap[n.id] = 0; });
    this.edges.forEach(e => {
      if (degreeMap[e.source] !== undefined) degreeMap[e.source]++;
      if (degreeMap[e.target] !== undefined) degreeMap[e.target]++;
    });

    const degreeBins = { '1 Link': 0, '2 Links': 0, '3 Links': 0, '4+ Links': 0 };
    Object.values(degreeMap).forEach(d => {
      if (d <= 1) degreeBins['1 Link']++;
      else if (d === 2) degreeBins['2 Links']++;
      else if (d === 3) degreeBins['3 Links']++;
      else degreeBins['4+ Links']++;
    });

    this.drawHistogramChart(degreeBins);
  },

  drawDonutChart(counts) {
    const canvas = document.getElementById('graph-donut-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const colors = {
      institution: '#1a365d',
      application: '#2563eb',
      document: '#0d9488',
      compliance: '#d97706',
      complaint: '#dc2626',
      task: '#4f46e5'
    };

    const total = Object.values(counts).reduce((a, b) => a + b, 0) || 1;
    let currentAngle = -Math.PI / 2;
    const cx = w / 2;
    const cy = h / 2;
    const radius = 65;
    const lineWidth = 24;

    Object.entries(counts).forEach(([type, count]) => {
      const sliceAngle = (count / total) * 2 * Math.PI;
      if (sliceAngle <= 0) return;

      ctx.beginPath();
      ctx.arc(cx, cy, radius, currentAngle, currentAngle + sliceAngle);
      ctx.strokeStyle = colors[type] || '#64748b';
      ctx.lineWidth = lineWidth;
      ctx.stroke();

      currentAngle += sliceAngle;
    });

    // Central text
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.font = 'bold 22px Inter, sans-serif';
    ctx.fillStyle = '#001332';
    ctx.fillText(total, cx, cy - 6);

    ctx.font = '10px Inter, sans-serif';
    ctx.fillStyle = '#64748b';
    ctx.fillText('ENTITIES', cx, cy + 14);
  },

  drawHistogramChart(bins) {
    const canvas = document.getElementById('graph-histogram-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const keys = Object.keys(bins);
    const values = Object.values(bins);
    const maxVal = Math.max(...values, 1);

    const padLeft = 24;
    const padRight = 16;
    const padBottom = 28;
    const padTop = 20;

    const chartW = w - padLeft - padRight;
    const chartH = h - padBottom - padTop;
    const barWidth = 38;
    const gap = (chartW - (barWidth * keys.length)) / (keys.length + 1);

    const barColors = [
      ['#64748b', '#94a3b8'],
      ['#2563eb', '#60a5fa'],
      ['#d97706', '#fbbf24'],
      ['#dc2626', '#f87171']
    ];

    keys.forEach((key, idx) => {
      const val = values[idx];
      const barH = (val / maxVal) * (chartH - 10);
      const x = padLeft + gap + idx * (barWidth + gap);
      const y = h - padBottom - barH;

      // Gradient bar
      const grad = ctx.createLinearGradient(0, y, 0, y + barH);
      grad.addColorStop(0, barColors[idx % barColors.length][0]);
      grad.addColorStop(1, barColors[idx % barColors.length][1]);

      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.roundRect(x, y, barWidth, barH, [4, 4, 0, 0]);
      ctx.fill();

      // Bar count label on top
      ctx.fillStyle = '#001332';
      ctx.font = 'bold 11px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(val, x + barWidth / 2, y - 6);

      // X-axis label
      ctx.fillStyle = '#64748b';
      ctx.font = '10px Inter, sans-serif';
      ctx.fillText(key, x + barWidth / 2, h - 8);
    });

    // Horizontal baseline
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padLeft, h - padBottom);
    ctx.lineTo(w - padRight, h - padBottom);
    ctx.stroke();
  },

  destroy() {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }
    if (this._onResize) {
      window.removeEventListener("resize", this._onResize);
    }
  },

  resizeCanvas() {
    if (!this.canvas) return;
    const rect = this.canvas.parentElement ? this.canvas.parentElement.getBoundingClientRect() : { width: 900, height: 520 };
    this.canvas.width = rect.width > 0 ? rect.width : 900;
    this.canvas.height = rect.height > 0 ? rect.height : 520;
  },

  async loadData() {
    const raw = await API.getGraphData();
    if (!raw || !raw.nodes) {
      console.warn("No graph data returned from API, using fallback");
      this.nodes = [];
      this.edges = [];
      return;
    }
    const w = this.canvas ? this.canvas.width : 900;
    const h = this.canvas ? this.canvas.height : 520;

    // Initialize node positions in a radial cluster
    this.nodes = (raw.nodes || []).map((n, idx) => {
      const angle = (idx / Math.max(raw.nodes.length, 1)) * 2 * Math.PI;
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

    this.edges = raw.edges || [];
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
      const isSearchMatch = this.searchMatchId && this.searchMatchId === n.id;

      // Glow / Selection / Search Match ring
      if (isSelected || isSearchMatch) {
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius + (isSearchMatch ? 8 : 6), 0, Math.PI * 2);
        ctx.fillStyle = isSearchMatch ? "rgba(251, 191, 36, 0.45)" : "rgba(59, 130, 246, 0.4)";
        ctx.fill();
        ctx.strokeStyle = isSearchMatch ? "#fbbf24" : "#ffffff";
        ctx.lineWidth = 2;
        ctx.stroke();
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

  focusEntity(id) {
    const target = this.nodes.find(n => n.id === id);
    if (!target) return;
    this.selectNode(target);
    const cx = this.canvas.width / 2;
    const cy = this.canvas.height / 2;
    this.transform.x = cx - target.x * this.transform.scale;
    this.transform.y = cy - target.y * this.transform.scale;
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

    // Render connected entity relationships
    const relatedLinks = this.edges
      .filter(e => e.source === node.id || e.target === node.id)
      .map(e => {
        const otherId = e.source === node.id ? e.target : e.source;
        const otherNode = this.nodes.find(n => n.id === otherId);
        return {
          id: otherId,
          label: otherNode ? otherNode.label : otherId,
          type: otherNode ? otherNode.type : 'entity',
          relation: e.label
        };
      });

    let linksContainer = document.getElementById("inspector-related-links");
    if (!linksContainer) {
      linksContainer = document.createElement("div");
      linksContainer.id = "inspector-related-links";
      linksContainer.className = "mt-3 pt-2 border-t border-slate-700/80";
      const statusEl = document.getElementById("inspector-status");
      if (statusEl && statusEl.parentNode) {
        statusEl.parentNode.insertBefore(linksContainer, document.getElementById("inspector-jump-btn"));
      }
    }

    if (linksContainer) {
      if (relatedLinks.length > 0) {
        linksContainer.innerHTML = `
          <div class="text-[10px] font-mono uppercase text-slate-400 font-bold mb-1.5 flex items-center justify-between">
            <span>Connected Links (${relatedLinks.length})</span>
            <span class="text-blue-400">Click to Inspect</span>
          </div>
          <div class="space-y-1 max-h-32 overflow-y-auto pr-1">
            ${relatedLinks.map(l => `
              <div 
                onclick="GraphModule.focusEntity('${l.id}')"
                class="flex items-center justify-between gap-1.5 p-1 rounded bg-slate-800/80 hover:bg-slate-700 cursor-pointer text-[10px] transition-colors"
                title="${l.label}"
              >
                <div class="truncate text-slate-200">${l.label}</div>
                <span class="text-[9px] font-mono text-amber-300 shrink-0 uppercase">${l.relation}</span>
              </div>
            `).join('')}
          </div>
        `;
      } else {
        linksContainer.innerHTML = `<div class="text-[10px] text-slate-500 italic">No connected links in current view.</div>`;
      }
    }

    const jumpBtn = document.getElementById("inspector-jump-btn");
    jumpBtn.onclick = () => {
      if (node.type === 'institution') App.navigate('digitalTwin', { id: node.id });
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
