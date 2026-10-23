/**
 * AICTE ONE - Module 15: Notifications Center
 * Multi-channel priority alerts, compliance warnings, workflow updates, and deep-linking to records
 */
const NotificationsModule = {
  currentFilter: 'all', // 'all' | 'unread' | 'CRITICAL' | 'WARNING' | 'INFO'
  items: [],

  async render(containerId, params = {}) {
    // If called via App.navigate('notifications'), containerId might be 'main-content' or absent
    const res = await API.getNotifications();
    this.items = (res && res.items) ? res.items : (Array.isArray(res) ? res : (localStore.db.notifications || []));

    const total = this.items.length;
    const unread = this.items.filter(n => !n.is_read).length;
    const critical = this.items.filter(n => /crit/i.test(n.urgency || n.type || n.category || '')).length;
    const warnings = this.items.filter(n => /warn|alert/i.test(n.urgency || n.type || n.category || '')).length;
    const info = this.items.filter(n => /info|notice/i.test(n.urgency || n.type || n.category || '')).length;

    let filtered = [...this.items];
    if (this.currentFilter === 'unread') {
      filtered = filtered.filter(n => !n.is_read);
    } else if (this.currentFilter === 'CRITICAL') {
      filtered = filtered.filter(n => /crit/i.test(n.urgency || n.type || n.category || ''));
    } else if (this.currentFilter === 'WARNING') {
      filtered = filtered.filter(n => /warn|alert/i.test(n.urgency || n.type || n.category || ''));
    } else if (this.currentFilter === 'INFO') {
      filtered = filtered.filter(n => /info|notice/i.test(n.urgency || n.type || n.category || ''));
    }

    const html = `
      <div class="page-header flex justify-between items-center mb-6 flex-wrap gap-4">
        <div>
          <div class="page-eyebrow text-xs font-bold text-blue-600 uppercase tracking-wider mb-1">Operational Alerts</div>
          <h1 class="page-title text-2xl font-bold text-[#001332]">Notifications & Regulatory Alerts</h1>
          <p class="text-sm text-slate-500">Live statutory alerts, EVC scheduling notices, deadline reminders, and escalation triggers</p>
        </div>
        <div class="flex gap-2">
          <button class="btn btn-secondary text-xs flex items-center gap-1.5" onclick="NotificationsModule.markAllAsRead()">
            <span class="material-symbols-outlined text-[16px]">done_all</span>
            <span>Mark All as Read</span>
          </button>
        </div>
      </div>

      <!-- Filters & Stats Chips -->
      <div class="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div class="flex flex-wrap gap-2">
          <button class="filter-chip px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${this.currentFilter === 'all' ? 'bg-[#001332] text-white shadow-xs' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'}" onclick="NotificationsModule.setFilter('all')">
            All Alerts <span class="ml-1 opacity-75 font-mono">(${total})</span>
          </button>
          <button class="filter-chip px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${this.currentFilter === 'unread' ? 'bg-[#001332] text-white shadow-xs' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'}" onclick="NotificationsModule.setFilter('unread')">
            Unread <span class="ml-1 opacity-75 font-mono">(${unread})</span>
          </button>
          <button class="filter-chip px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${this.currentFilter === 'CRITICAL' ? 'bg-red-600 text-white shadow-xs' : 'bg-red-50 text-red-700 hover:bg-red-100'}" onclick="NotificationsModule.setFilter('CRITICAL')">
            Critical <span class="ml-1 opacity-75 font-mono">(${critical})</span>
          </button>
          <button class="filter-chip px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${this.currentFilter === 'WARNING' ? 'bg-amber-600 text-white shadow-xs' : 'bg-amber-50 text-amber-700 hover:bg-amber-100'}" onclick="NotificationsModule.setFilter('WARNING')">
            Warnings <span class="ml-1 opacity-75 font-mono">(${warnings})</span>
          </button>
          <button class="filter-chip px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${this.currentFilter === 'INFO' ? 'bg-blue-600 text-white shadow-xs' : 'bg-blue-50 text-blue-700 hover:bg-blue-100'}" onclick="NotificationsModule.setFilter('INFO')">
            Informational <span class="ml-1 opacity-75 font-mono">(${info})</span>
          </button>
        </div>
        <div class="text-xs text-slate-500 font-medium">
          Showing ${filtered.length} of ${total} alerts
        </div>
      </div>

      <!-- Notifications List -->
      <div id="notifications-list" class="space-y-3">
        ${filtered.length === 0 ? `
          <div class="card p-12 text-center text-slate-400 bg-white border border-slate-200 rounded-lg">
            <span class="material-symbols-outlined text-4xl text-slate-300 mb-2 block">notifications_paused</span>
            <div class="font-medium text-slate-600">No alerts match the selected criteria</div>
            <div class="text-xs text-slate-400 mt-1">All regulatory obligations and workflow tasks are up to date</div>
          </div>
        ` : filtered.map(n => {
          const rawUrg = (n.urgency || n.type || '').toUpperCase();
          const isCrit = /CRIT/.test(rawUrg);
          const isWarn = /WARN|ALERT/.test(rawUrg);
          
          let borderClass = 'border-l-4 border-blue-500 bg-blue-50/20';
          let badgeColor = 'pill blue';
          let iconName = 'info';
          let labelText = 'Informational';

          if (isCrit) {
            borderClass = 'border-l-4 border-red-500 bg-red-50/30';
            badgeColor = 'pill red';
            iconName = 'error';
            labelText = 'Critical';
          } else if (isWarn) {
            borderClass = 'border-l-4 border-amber-500 bg-amber-50/30';
            badgeColor = 'pill amber';
            iconName = 'warning';
            labelText = 'Warning';
          }

          const timeFormatted = n.created_at ? new Date(n.created_at).toLocaleString('en-IN', {
            day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
          }) : 'Recent';

          const targetRoute = n.link_type || (/compli/i.test(n.title + n.message) ? 'compliance' : (/complaint|grievance/i.test(n.title + n.message) ? 'complaints' : (/evc|visit/i.test(n.title + n.message) ? 'evc' : 'tasks')));
          const targetId = n.link_id || null;

          return `
            <div class="card p-4 flex items-start gap-3.5 transition-all hover:shadow-md ${borderClass} ${n.is_read ? 'opacity-80 bg-white' : 'bg-white font-medium'} rounded-lg border border-slate-200">
              <div class="mt-0.5 text-slate-500 shrink-0">
                <span class="material-symbols-outlined text-[20px] ${isCrit ? 'text-red-500' : (isWarn ? 'text-amber-500' : 'text-blue-500')}">${iconName}</span>
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between flex-wrap gap-2">
                  <div class="flex items-center gap-2">
                    <span class="${badgeColor} text-[10px] font-bold uppercase">${labelText}</span>
                    <h4 class="text-xs sm:text-sm font-bold text-[#001332] truncate">${escapeHtml(n.title)}</h4>
                    ${!n.is_read ? '<span class="w-2 h-2 rounded-full bg-blue-600 inline-block" title="Unread"></span>' : ''}
                  </div>
                  <span class="text-[11px] text-slate-400 font-mono">${timeFormatted}</span>
                </div>
                <p class="text-xs text-slate-600 mt-1 leading-relaxed">${escapeHtml(n.message)}</p>
                <div class="flex items-center gap-3 mt-3">
                  <button class="btn sm primary text-xs py-1" onclick="NotificationsModule.handleAction('${n.id}', '${targetRoute}', '${targetId || ''}')">
                    Open Linked Record →
                  </button>
                  ${!n.is_read ? `
                    <button class="btn sm text-xs py-1 text-slate-500 hover:text-slate-800" onclick="NotificationsModule.markRead('${n.id}')">
                      Mark as Read
                    </button>
                  ` : ''}
                </div>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;

    const container = document.getElementById(containerId);
    if (container) {
      container.innerHTML = html;
    }
    return html;
  },

  setFilter(filter) {
    this.currentFilter = filter;
    this.render('main-content');
  },

  async markRead(id) {
    await API.markNotificationRead(id);
    const item = this.items.find(n => n.id === id);
    if (item) item.is_read = true;
    if (typeof App !== 'undefined' && App.updateNotificationBadge) {
      App.updateNotificationBadge();
    }
    this.render('main-content');
  },

  async markAllAsRead() {
    await API.markAllNotificationsRead();
    this.items.forEach(n => { n.is_read = true; });
    if (typeof App !== 'undefined') {
      if (App.updateNotificationBadge) App.updateNotificationBadge();
      App.toast("All notifications marked as read.");
    }
    this.render('main-content');
  },

  handleAction(notifId, route, recordId) {
    this.markRead(notifId);
    if (recordId) {
      App.navigate(route, { id: recordId });
    } else {
      App.navigate(route);
    }
  }
};

window.NotificationsModule = NotificationsModule;
