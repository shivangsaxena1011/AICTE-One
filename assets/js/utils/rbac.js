/**
 * AICTE ONE - Centralized Role-Based Access Control (RBAC) System
 * Sovereign Government-Tech Permission Matrix aligned with AICTE Approval Process Handbook (APH 2024-27).
 * Single Source of Truth for frontend navigation, route guards, and component gating.
 */
const RBAC = {
  // 8 Statutory Role Identifiers (+ Demo Judge Evaluation Sandbox)
  ROLES: {
    SUPER_ADMIN: 'SUPER_ADMIN',
    SECURITY_OFFICER: 'SECURITY_OFFICER',
    POLICY_COMPLIANCE_OFFICER: 'POLICY_COMPLIANCE_OFFICER',
    COMPLAINT_OFFICER: 'COMPLAINT_OFFICER',
    ANTI_RAGGING_OFFICER: 'ANTI_RAGGING_OFFICER',
    INSTITUTE_HEAD: 'INSTITUTE_HEAD',
    STUDENT_COMPLAINANT: 'STUDENT_COMPLAINANT',
    PUBLIC_VISITOR: 'PUBLIC_VISITOR',
    DEMO_JUDGE: 'DEMO_JUDGE'
  },

  // Role Default Landing Routes
  DEFAULT_ROUTES: {
    SUPER_ADMIN: 'overview',
    DEMO_JUDGE: 'overview',
    SECURITY_OFFICER: 'verification',
    POLICY_COMPLIANCE_OFFICER: 'compliance',
    COMPLAINT_OFFICER: 'complaints',
    ANTI_RAGGING_OFFICER: 'complaints',
    INSTITUTE_HEAD: 'digitalTwin',
    STUDENT_COMPLAINANT: 'complaints',
    PUBLIC_VISITOR: 'institutions'
  },

  // Statutory Role-to-Route Access Matrix
  ROLE_ROUTES: {
    SUPER_ADMIN: [
      'overview', 'institutions', 'digitalTwin', 'applications', 'scrutiny',
      'evc', 'verification', 'compliance', 'complaints', 'coordination',
      'tasks', 'graph', 'copilot', 'reports', 'notifications', 'audit', 'settings'
    ],
    DEMO_JUDGE: [
      'overview', 'institutions', 'digitalTwin', 'applications', 'scrutiny',
      'evc', 'verification', 'compliance', 'complaints', 'coordination',
      'tasks', 'graph', 'copilot', 'reports', 'notifications', 'audit', 'settings'
    ],
    SECURITY_OFFICER: [
      'verification', 'audit', 'tasks', 'reports', 'notifications', 'institutions'
    ],
    POLICY_COMPLIANCE_OFFICER: [
      'compliance', 'scrutiny', 'applications', 'institutions', 'tasks', 'reports', 'notifications'
    ],
    COMPLAINT_OFFICER: [
      'complaints', 'coordination', 'institutions', 'tasks', 'reports', 'notifications'
    ],
    ANTI_RAGGING_OFFICER: [
      'complaints', 'institutions', 'tasks', 'reports', 'notifications'
    ],
    INSTITUTE_HEAD: [
      'digitalTwin', 'applications', 'compliance', 'complaints', 'notifications', 'institutions'
    ],
    STUDENT_COMPLAINANT: [
      'complaints', 'institutions', 'notifications'
    ],
    PUBLIC_VISITOR: [
      'institutions', 'digitalTwin'
    ]
  },

  // Human-Readable Role Descriptions & Badges
  ROLE_META: {
    SUPER_ADMIN: {
      name: 'Super Administrator',
      hindi: 'मुख्य प्रशासक',
      badge: 'Statutory Apex',
      description: 'Apex statutory authority across central bureaus, approval workflows, and immutable audit trails.'
    },
    SECURITY_OFFICER: {
      name: 'Security Officer',
      hindi: 'सुरक्षा अधिकारी',
      badge: 'Cyber & Vigilance',
      description: 'Security incident surveillance, document forensic anomaly review, threat monitoring, and audit logs.'
    },
    POLICY_COMPLIANCE_OFFICER: {
      name: 'Policy & Compliance Officer',
      hindi: 'नीति एवं अनुपालन अधिकारी',
      badge: 'Academic Bureau',
      description: 'Regulatory compliance audits, land lease deed tracking, FDR monitoring, and deficiency cure management.'
    },
    COMPLAINT_OFFICER: {
      name: 'Complaint & Vigilance Officer',
      hindi: 'शिकायत एवं सतर्कता अधिकारी',
      badge: 'Grievance Cell',
      description: 'Grievance intake, cross-bureau clash detection, vigilance case investigation, and matter disposal.'
    },
    ANTI_RAGGING_OFFICER: {
      name: 'Anti-Ragging Committee Head',
      hindi: 'एंटी-रैगिंग समिति प्रमुख',
      badge: 'Student Safety',
      description: 'Student safety enforcement, rapid campus squad alerts, urgent hearing notices, and case tracking.'
    },
    INSTITUTE_HEAD: {
      name: 'Institute Principal / Head',
      hindi: 'संस्थान प्राचार्य / निदेशक',
      badge: 'Tenant Isolated',
      description: 'Tenant-isolated institutional portal for digital twin inspection, EoA applications, and compliance filings.'
    },
    STUDENT_COMPLAINANT: {
      name: 'Student / Scholar / Complainant',
      hindi: 'छात्र / शिकायतकर्ता',
      badge: 'Citizen Access',
      description: 'Citizen grievance lodging, ragging reporting, digital evidence submission, and milestone tracking.'
    },
    PUBLIC_VISITOR: {
      name: 'Public Visitor',
      hindi: 'सार्वजनिक नागरिक',
      badge: 'Open Registry',
      description: 'Open public directory search across 8,800+ approved institutions, approval verification, and official records.'
    },
    DEMO_JUDGE: {
      name: 'Honorable Evaluation Committee / Judge',
      hindi: 'मूल्यांकन समिति / निर्णायक',
      badge: 'Evaluation Sandbox',
      description: 'Full prototype evaluation and inspection mode with pre-populated datasets across all regulatory bureaus.'
    }
  },

  // Master Navigation Menu Registry
  MENU_ITEMS: [
    // Group 1: Core Operations
    {
      group: 'Core Operations',
      groupColor: '#fd651e',
      id: 'overview',
      label: 'Executive Overview',
      icon: 'dashboard',
      roles: ['SUPER_ADMIN', 'DEMO_JUDGE']
    },
    {
      group: 'Core Operations',
      groupColor: '#fd651e',
      id: 'institutions',
      label: 'Institution Directory',
      icon: 'account_balance',
      roles: ['SUPER_ADMIN', 'DEMO_JUDGE', 'SECURITY_OFFICER', 'POLICY_COMPLIANCE_OFFICER', 'COMPLAINT_OFFICER', 'ANTI_RAGGING_OFFICER', 'INSTITUTE_HEAD', 'STUDENT_COMPLAINANT', 'PUBLIC_VISITOR']
    },
    {
      group: 'Core Operations',
      groupColor: '#fd651e',
      id: 'digitalTwin',
      label: 'Digital Twin (360°)',
      icon: 'view_in_ar',
      roles: ['SUPER_ADMIN', 'DEMO_JUDGE', 'INSTITUTE_HEAD', 'PUBLIC_VISITOR']
    },
    {
      group: 'Core Operations',
      groupColor: '#fd651e',
      id: 'applications',
      label: 'Approval Applications',
      icon: 'assignment',
      roles: ['SUPER_ADMIN', 'DEMO_JUDGE', 'POLICY_COMPLIANCE_OFFICER', 'INSTITUTE_HEAD']
    },
    {
      group: 'Core Operations',
      groupColor: '#fd651e',
      id: 'scrutiny',
      label: 'Scrutiny & Workflow',
      icon: 'fact_check',
      roles: ['SUPER_ADMIN', 'DEMO_JUDGE', 'POLICY_COMPLIANCE_OFFICER']
    },
    {
      group: 'Core Operations',
      groupColor: '#fd651e',
      id: 'evc',
      label: 'EVC Scheduling',
      icon: 'event_available',
      roles: ['SUPER_ADMIN', 'DEMO_JUDGE']
    },

    // Group 2: Evidence & Oversight
    {
      group: 'Evidence & Oversight',
      groupColor: '#23a274',
      id: 'verification',
      label: 'Document Verification',
      icon: 'verified_user',
      roles: ['SUPER_ADMIN', 'DEMO_JUDGE', 'SECURITY_OFFICER'],
      externalLink: 'https://documentverify-two.vercel.app/'
    },
    {
      group: 'Evidence & Oversight',
      groupColor: '#23a274',
      id: 'compliance',
      label: 'Regulatory Compliance',
      icon: 'rule',
      roles: ['SUPER_ADMIN', 'DEMO_JUDGE', 'POLICY_COMPLIANCE_OFFICER', 'INSTITUTE_HEAD']
    },
    {
      group: 'Evidence & Oversight',
      groupColor: '#23a274',
      id: 'complaints',
      label: 'Complaints & Grievances',
      icon: 'crisis_alert',
      roles: ['SUPER_ADMIN', 'DEMO_JUDGE', 'COMPLAINT_OFFICER', 'ANTI_RAGGING_OFFICER', 'INSTITUTE_HEAD', 'STUDENT_COMPLAINANT']
    },
    {
      group: 'Evidence & Oversight',
      groupColor: '#23a274',
      id: 'coordination',
      label: 'Cross-Bureau Clashes',
      icon: 'alt_route',
      roles: ['SUPER_ADMIN', 'DEMO_JUDGE', 'COMPLAINT_OFFICER']
    },
    {
      group: 'Evidence & Oversight',
      groupColor: '#23a274',
      id: 'tasks',
      label: 'Tasks & Escalations',
      icon: 'task_alt',
      roles: ['SUPER_ADMIN', 'DEMO_JUDGE', 'SECURITY_OFFICER', 'POLICY_COMPLIANCE_OFFICER', 'COMPLAINT_OFFICER', 'ANTI_RAGGING_OFFICER']
    },

    // Group 3: Graph & AI Intelligence
    {
      group: 'Graph & AI Intelligence',
      groupColor: '#85f8c4',
      id: 'graph',
      label: 'Regulatory Graph',
      icon: 'hub',
      roles: ['SUPER_ADMIN', 'DEMO_JUDGE']
    },
    {
      group: 'Graph & AI Intelligence',
      groupColor: '#85f8c4',
      id: 'copilot',
      label: 'AI Governance Copilot',
      icon: 'smart_toy',
      roles: ['SUPER_ADMIN', 'DEMO_JUDGE']
    },

    // Group 4: Assurance & Admin
    {
      group: 'Assurance & Admin',
      groupColor: '#94a3b8',
      id: 'reports',
      label: 'Reports & Analytics',
      icon: 'analytics',
      roles: ['SUPER_ADMIN', 'DEMO_JUDGE', 'SECURITY_OFFICER', 'POLICY_COMPLIANCE_OFFICER', 'COMPLAINT_OFFICER', 'ANTI_RAGGING_OFFICER']
    },
    {
      group: 'Assurance & Admin',
      groupColor: '#94a3b8',
      id: 'notifications',
      label: 'Notification Center',
      icon: 'notifications_active',
      roles: ['SUPER_ADMIN', 'DEMO_JUDGE', 'SECURITY_OFFICER', 'POLICY_COMPLIANCE_OFFICER', 'COMPLAINT_OFFICER', 'ANTI_RAGGING_OFFICER', 'INSTITUTE_HEAD', 'STUDENT_COMPLAINANT']
    },
    {
      group: 'Assurance & Admin',
      groupColor: '#94a3b8',
      id: 'audit',
      label: 'Audit Trail',
      icon: 'history_edu',
      roles: ['SUPER_ADMIN', 'DEMO_JUDGE', 'SECURITY_OFFICER']
    },
    {
      group: 'Assurance & Admin',
      groupColor: '#94a3b8',
      id: 'settings',
      label: 'Settings & RBAC',
      icon: 'admin_panel_settings',
      roles: ['SUPER_ADMIN', 'DEMO_JUDGE']
    }
  ],

  /**
   * Evaluates if a given role is authorized to access a route.
   */
  canAccessRoute(role, route) {
    if (!route) return false;
    const cleanRoute = route.split('/')[0];
    if (!role) role = 'PUBLIC_VISITOR';
    const r = role.toUpperCase();
    if (r === 'SUPER_ADMIN' || r === 'DEMO_JUDGE') return true;
    const allowed = this.ROLE_ROUTES[r] || [];
    return allowed.includes(cleanRoute);
  },

  /**
   * Returns the authorized landing route for a given persona.
   */
  getDefaultRoute(role) {
    if (!role) return 'institutions';
    return this.DEFAULT_ROUTES[role.toUpperCase()] || 'institutions';
  },

  /**
   * Returns organized, grouped navigation items filtered to the authorized role.
   */
  getGroupedMenuItems(role) {
    if (!role) role = 'PUBLIC_VISITOR';
    const r = role.toUpperCase();
    const isSuper = r === 'SUPER_ADMIN' || r === 'DEMO_JUDGE';
    const filteredItems = this.MENU_ITEMS.filter(item => isSuper || item.roles.includes(r));

    const groups = [];
    const groupMap = new Map();
    filteredItems.forEach(item => {
      if (!groupMap.has(item.group)) {
        const g = { name: item.group, color: item.groupColor, items: [] };
        groupMap.set(item.group, g);
        groups.push(g);
      }
      groupMap.get(item.group).items.push(item);
    });
    return groups;
  }
};

if (typeof window !== 'undefined') {
  window.RBAC = RBAC;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = RBAC;
}
