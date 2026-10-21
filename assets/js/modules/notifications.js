/**
 * AICTE ONE - Module 15: Notifications Center
 * Multi-channel priority alerts, compliance warnings, workflow updates, and deep-linking to records
 */
const NotificationsModule = {
  currentFilter: 'all',

  async render(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = `
      <div class="page-header flex justify-between items-center mb-6">
        <div>
          <h1 class="page-title text-2xl font-bold text-navy-900">Notifications & Regulatory Alerts</h1>
          <p class="text-sm text-slate-500">Live operational alerts, EVC scheduling notices, deadline reminders, and escalation triggers</p>
        </div>
        <div class="flex gap-2">
          <button class="btn btn-secondary text-sm" onclick="NotificationsModule.markAllAsRead()">
            <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
            Mark All as Read
          </button>
        </div>
      </div>

      <!-- Filters & Stats -->
      <div class="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div class="flex space-x-2">
          <button class="filter-chip px-3 py-1.5 rounded-full text-xs font-semibold ${this.currentFilter === 'all' ? 'bg-navy-900 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'}" onclick="NotificationsModule.setFilter('all')">
            All Alerts
          </button>
          <button class="filter-chip px-3 py-1.5 rounded-full text-xs font-semibold ${this.currentFilter === 'unread' ? 'bg-navy-900 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'}" onclick="NotificationsModule.setFilter('unread')">
            Unread
          </button>
          <button class="filter-chip px-3 py-1.5 rounded-full text-xs font-semibold ${this.currentFilter === 'CRITICAL' ? 'bg-red-600 text-white' : 'bg-red-50 text-red-700 hover:bg-red-100'}" onclick="NotificationsModule.setFilter('CRITICAL')">
            Critical
          </button>
          <button class="filter-chip px-3 py-1.5 rounded-full text-xs font-semibold ${this.currentFilter === 'ALERT' ? 'bg-amber-600 text-white' : 'bg-amber-50 text-amber-700 hover:bg-amber-100'}" onclick="NotificationsModule.setFilter('ALERT')">
            Warnings
          </button>
          <button class="filter-chip px-3 py-1.5 rounded-full text-xs font-semibold ${this.currentFilter === 'INFO' ? 'bg-blue-600 text-white' : 'bg-blue-50 text-blue-700 hover:bg-blue-100'}" onclick="NotificationsModule.setFilter('INFO')">
            Informational
          </button>
        </div>
        <div id="notif-count-summary" class="text-xs text-slate-500 font-medium"></div>
      </div>

      <div id="notifications-list" class="space-y-3">
        <div class="flex justify-center items-center py-12"><div class="spinner"></div></div>
      </div>
    `;

    await this.loadNotifications();
  },

  setFilter(filter) {
    this.currentFilter = filter;
    this.render('main-content');
  },

  async loadNotifications() {
    const listContainer = document.getElementById('notifications-list');
    const summaryContainer = document.getElementById('notif-count-summary');
    if (!listContainer) return;

    let res = await ApiService.getNotifications();
    let notifications = res.items || [];

    const unreadCount = notifications.filter(n => !n.is_read).length;
    if (summaryContainer) {
      summaryContainer.textContent = `${unreadCount} unread out of ${notifications.length} total`;
    }

    if (this.currentFilter === 'unread') {
      notifications = notifications.filter(n => !n.is_read);
    } else if (this.currentFilter !== 'all') {
      notifications = notifications.filter(n => n.type === this.currentFilter);
    }

    if (notifications.length === 0) {
      listContainer.innerHTML = `
        <div class="card p-12 text-center text-slate-400">
          <svg class="w-12 h-12 mx-auto mb-3 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path></svg>
          <div class="font-medium text-slate-600">No alerts match the selected criteria</div>
          <div class="text-xs text-slate-400 mt-1">All regulatory obligations and tasks are up to date</div>
        </div>
      `;
      return;
    }

    listContainer.innerHTML = notifications.map(n => {
      const typeStyles = {
        CRITICAL: { border: 'border-l-4 border-red-500 bg-red-50/30', badge: 'badge-danger', icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z' },
        ALERT: { border: 'border-l-4 border-amber-500 bg-amber-50/30', badge: 'badge-warning', icon: 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z' },
        INFO: { border: 'border-l-4 border-blue-500 bg-blue-50/30', badge: 'badge-neutral', icon: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z' }
      }[n.type] || { border: 'border-l-4 border-slate-300', badge: 'badge-neutral', icon: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z' };

      const timeFormatted = n.created_at ? new Date(n.created_at).toLocaleString('en-IN', {
        day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
      }) : 'Recent';

      return `
        <div class="card p-4 flex items-start gap-4 transition-all hover:shadow-md ${typeStyles.border} ${n.is_read ? 'opacity-80' : 'bg-white font-medium'}">
          <div class="mt-1 text-slate-500">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${typeStyles.icon}"></path></svg>
          </div>
          <div class="flex-1">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="badge ${typeStyles.badge} text-[10px] font-bold">${n.type}</span>
                <h4 class="text-sm font-bold text-navy-900">${n.title}</h4>
                ${!n.is_read ? '<span class="w-2 h-2 rounded-full bg-blue-600 inline-block"></span>' : ''}
              </div>
              <span class="text-xs text-slate-400 font-mono">${timeFormatted}</span>
            </div>
            <p class="text-xs text-slate-600 mt-1">${n.message}</p>
            <div class="flex items-center gap-3 mt-3">
              ${n.link ? `
                <button class="btn btn-secondary text-xs py-1" onclick="NotificationsModule.handleAction('${n.id}', '${n.link}')">
                  View Linked Record &rarr;
                </button>
              ` : ''}
              ${!n.is_read ? `
                <button class="text-xs text-slate-500 hover:text-navy-900 underline" onclick="NotificationsModule.markAsRead('${n.id}')">
                  Mark as Read
                </button>
              ` : `
                <span class="text-[11px] text-slate-400">Read</span>
              `}
            </div>
          </div>
        </div>
      `;
    }).join('');
  },

  async markAsRead(id) {
    await ApiService.markNotificationRead(id);
    this.loadNotifications();
    App.updateNotificationBadge();
  },

  async markAllAsRead() {
    const res = await ApiService.getNotifications();
    const notifications = res.items || [];
    for (const n of notifications) {
      if (!n.is_read) {
        await ApiService.markNotificationRead(n.id);
      }
    }
    App.toast('All notifications marked as read', 'success');
    this.loadNotifications();
    App.updateNotificationBadge();
  },

  async handleAction(id, link) {
    await ApiService.markNotificationRead(id);
    App.updateNotificationBadge();
    if (link) {
      // Parse link format like "applications?id=APP-2024-001" or "compliance"
      const [module, query] = link.split('?');
      let param = null;
      if (query && query.includes('=')) {
        param = query.split('=')[1];
      }
      App.navigate(module, param);
    }
  }
};

window.NotificationsModule = NotificationsModule;
