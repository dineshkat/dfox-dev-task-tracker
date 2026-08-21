// Main Application Logic for DFOX Dev Task Tracker with Authentication First Portal

const App = {
  state: {
    currentUser: null,
    pendingVerifyEmail: '',
    tasks: [],
    members: [],
    analytics: null,
    emailLogs: [],
    settings: {},
    activeTab: 'tasks', // tasks, analytics, members, emails
    viewMode: 'kanban', // kanban, table
    roleMode: 'lead', // lead, dev
    selectedDevId: null,
    searchQuery: '',
    selectedPriority: 'ALL',
    selectedAssignee: 'ALL'
  },

  async init() {
    TaskTimer.init();
    this.setupEventListeners();
    this.checkUrlParams();
    await this.checkAuthStatus();

    if (this.state.currentUser) {
      this.showDashboardView();
      await this.loadInitialData();
      this.render();
    } else {
      this.showAuthPortal();
    }
  },

  checkUrlParams() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('verified') === '1') {
      const msg = urlParams.get('msg') || 'Account verified successfully! You can now log in.';
      this.showToast(`✅ ${msg}`, 'success');
      this.showPortalScreen('login');
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  },

  showAuthPortal() {
    const portalEl = document.getElementById('auth-portal-view');
    const dashEl = document.getElementById('app-dashboard-view');
    if (portalEl) portalEl.style.display = 'flex';
    if (dashEl) dashEl.style.display = 'none';
  },

  showDashboardView() {
    const portalEl = document.getElementById('auth-portal-view');
    const dashEl = document.getElementById('app-dashboard-view');
    if (portalEl) portalEl.style.display = 'none';
    if (dashEl) dashEl.style.display = 'block';
  },

  showPortalScreen(screen) {
    const screens = ['login', 'signup', 'verify'];
    screens.forEach(s => {
      const el = document.getElementById(`portal-screen-${s}`);
      if (el) el.style.display = (s === screen) ? 'block' : 'none';
    });

    const tabNav = document.getElementById('auth-toggle-nav');
    if (tabNav) {
      tabNav.style.display = (screen === 'verify') ? 'none' : 'flex';
    }

    const tabLogin = document.getElementById('tab-btn-login');
    const tabSignup = document.getElementById('tab-btn-signup');
    if (tabLogin && tabSignup) {
      tabLogin.classList.toggle('active', screen === 'login');
      tabSignup.classList.toggle('active', screen === 'signup');
    }
  },

  async checkAuthStatus() {
    try {
      const res = await API.getMe();
      if (res.user) {
        this.state.currentUser = res.user;
        if (res.user.role === 'Developer') {
          this.state.roleMode = 'dev';
          this.state.selectedDevId = res.user.id;
          this.state.selectedAssignee = res.user.id.toString();
        } else {
          this.state.roleMode = 'lead';
          this.state.selectedAssignee = 'ALL';
        }
      } else {
        this.state.currentUser = null;
      }
    } catch (e) {
      this.state.currentUser = null;
    }
  },

  async loadInitialData() {
    try {
      const [membersData, settingsData] = await Promise.all([
        API.getMembers(),
        API.getSettings()
      ]);
      this.state.members = membersData.members || [];
      this.state.settings = settingsData.settings || {};
      
      if (this.state.members.length > 0 && !this.state.selectedDevId) {
        this.state.selectedDevId = this.state.members[0].id;
      }
      
      await this.refreshTasksAndAnalytics();
    } catch (err) {
      console.error("Error loading initial data:", err);
    }
  },

  async refreshTasksAndAnalytics() {
    try {
      const [tasksData, analyticsData, logsData] = await Promise.all([
        API.getTasks(),
        API.getAnalytics(),
        API.getEmailLogs()
      ]);
      this.state.tasks = tasksData.tasks || [];
      this.state.analytics = analyticsData || null;
      this.state.emailLogs = logsData.logs || [];
      this.render();
    } catch (err) {
      console.error("Error refreshing tasks:", err);
    }
  },

  setupEventListeners() {
    // Role switcher
    document.querySelectorAll('.role-pill').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const role = e.currentTarget.dataset.role;
        this.setRoleMode(role);
      });
    });

    // Developer dropdown in header
    const devSelect = document.getElementById('header-dev-select');
    if (devSelect) {
      devSelect.addEventListener('change', (e) => {
        this.state.selectedDevId = parseInt(e.target.value);
        if (this.state.roleMode === 'dev') {
          this.state.selectedAssignee = e.target.value;
        }
        this.render();
      });
    }

    // Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const tab = e.currentTarget.dataset.tab;
        this.setActiveTab(tab);
      });
    });

    // View toggle (Kanban vs Table)
    document.querySelectorAll('.view-toggle-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const view = e.currentTarget.dataset.view;
        this.setViewMode(view);
      });
    });

    // Search and filters
    const searchInput = document.getElementById('filter-search');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.state.searchQuery = e.target.value.toLowerCase();
        this.renderTaskViews();
      });
    }

    const prioFilter = document.getElementById('filter-priority');
    if (prioFilter) {
      prioFilter.addEventListener('change', (e) => {
        this.state.selectedPriority = e.target.value;
        this.renderTaskViews();
      });
    }

    const assigneeFilter = document.getElementById('filter-assignee');
    if (assigneeFilter) {
      assigneeFilter.addEventListener('change', (e) => {
        this.state.selectedAssignee = e.target.value;
        this.renderTaskViews();
      });
    }

    // Modals
    document.getElementById('btn-new-task')?.addEventListener('click', () => this.openCreateTaskModal());
    document.getElementById('btn-open-settings')?.addEventListener('click', () => this.openSettingsModal());
    
    // Live efficiency calculation in completion modal
    document.getElementById('complete-actual-hours')?.addEventListener('input', () => this.calculateCompletionEfficiencyPreview());
    document.getElementById('complete-actual-mins')?.addEventListener('input', () => this.calculateCompletionEfficiencyPreview());

    // Live Stopwatch listeners
    document.getElementById('btn-timer-start')?.addEventListener('click', () => TaskTimer.start());
    document.getElementById('btn-timer-pause')?.addEventListener('click', () => TaskTimer.pause());
    document.getElementById('btn-timer-reset')?.addEventListener('click', () => TaskTimer.reset());
  },

  // ----------------- Auth Workflows -----------------
  async handleSignupSubmit(e) {
    e.preventDefault();
    const name = document.getElementById('signup-name').value.trim();
    const email = document.getElementById('signup-email').value.trim();
    const designation = document.getElementById('signup-designation').value.trim();
    const password = document.getElementById('signup-password').value;

    if (!name || !email || !password) {
      this.showToast('Please fill in all required fields', 'danger');
      return;
    }

    try {
      const res = await API.signup({ name, email, password, designation });
      if (res.error) {
        this.showToast(res.error, 'danger');
        return;
      }

      this.state.pendingVerifyEmail = email;
      document.getElementById('verify-display-email').textContent = email;
      document.getElementById('verify-otp-input').value = '';
      
      this.showPortalScreen('verify');
      this.showToast('📧 6-digit verification code sent to your email address!', 'success');

      if (res.email_result && res.email_result.mode === 'SIMULATED') {
        this.showToast(`📝 Simulated OTP: ${res.email_result.otp}`, 'info');
      }
    } catch (err) {
      this.showToast('Failed to create account', 'danger');
    }
  },

  async handleVerifySubmit(e) {
    e.preventDefault();
    const email = this.state.pendingVerifyEmail;
    const otp = document.getElementById('verify-otp-input').value.trim();

    if (!otp) {
      this.showToast('Please enter the 6-digit verification code', 'danger');
      return;
    }

    try {
      const res = await API.verifyOTP(email, otp);
      if (res.success) {
        this.showToast('🎉 Account successfully verified! Please sign in.', 'success');
        document.getElementById('login-email').value = email;
        this.showPortalScreen('login');
      } else {
        this.showToast(res.error || 'Verification failed', 'danger');
      }
    } catch (err) {
      this.showToast('Verification failed', 'danger');
    }
  },

  async handleResendVerification() {
    const email = this.state.pendingVerifyEmail;
    if (!email) return;

    try {
      const res = await API.resendVerification(email);
      if (res.error) {
        this.showToast(res.error, 'danger');
      } else {
        this.showToast('Fresh verification code dispatched to your email!', 'success');
      }
    } catch (err) {
      this.showToast('Failed to resend code', 'danger');
    }
  },

  async handleLoginSubmit(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;

    try {
      const res = await API.login(email, password);
      if (res.unverified) {
        this.state.pendingVerifyEmail = email;
        document.getElementById('verify-display-email').textContent = email;
        this.showPortalScreen('verify');
        this.showToast('⚠️ Please verify your account first. A code has been sent to your email.', 'warning');
        return;
      }

      if (res.error) {
        this.showToast(res.error, 'danger');
        return;
      }

      this.state.currentUser = res.user;
      this.showToast(`Welcome back, ${res.user.name}!`, 'success');

      // Transition from Auth portal to Dashboard
      this.showDashboardView();

      if (res.user.role === 'Developer') {
        this.setRoleMode('dev');
      } else {
        this.setRoleMode('lead');
      }

      await this.loadInitialData();
      this.render();
    } catch (err) {
      this.showToast('Login failed', 'danger');
    }
  },

  async handleLogout() {
    await API.logout();
    this.state.currentUser = null;
    this.showToast('Logged out successfully', 'info');
    this.showPortalScreen('login');
    this.showAuthPortal();
  },

  openCreateMemberModal() {
    this.showToast('Direct new team members to register on the sign-up page.', 'info');
  },

  // ----------------- Role & Navigation -----------------
  setRoleMode(role) {
    this.state.roleMode = role;
    document.querySelectorAll('.role-pill').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.role === role);
    });

    const devSelectContainer = document.getElementById('dev-select-wrapper');
    if (devSelectContainer) {
      devSelectContainer.classList.toggle('visible', role === 'dev');
    }

    if (role === 'dev') {
      if (this.state.currentUser && this.state.currentUser.role === 'Developer') {
        this.state.selectedDevId = this.state.currentUser.id;
        this.state.selectedAssignee = this.state.currentUser.id.toString();
      } else if (this.state.selectedDevId) {
        this.state.selectedAssignee = this.state.selectedDevId.toString();
      }
    } else {
      this.state.selectedAssignee = 'ALL';
    }

    this.setActiveTab('tasks');
    this.render();
  },

  setActiveTab(tab) {
    this.state.activeTab = tab;
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.tab === tab);
    });

    const views = ['tasks', 'analytics', 'members', 'emails'];
    views.forEach(v => {
      const el = document.getElementById(`view-${v}`);
      if (el) el.style.display = (v === tab) ? 'block' : 'none';
    });

    this.render();
  },

  setViewMode(view) {
    this.state.viewMode = view;
    document.querySelectorAll('.view-toggle-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.view === view);
    });

    const kanbanEl = document.getElementById('kanban-container');
    const tableEl = document.getElementById('table-container');
    if (kanbanEl && tableEl) {
      kanbanEl.style.display = (view === 'kanban') ? 'grid' : 'none';
      tableEl.style.display = (view === 'table') ? 'block' : 'none';
    }
  },

  getFilteredTasks() {
    let tasks = [...this.state.tasks];

    if (this.state.roleMode === 'dev' && this.state.selectedDevId) {
      tasks = tasks.filter(t => t.assignee_id === this.state.selectedDevId);
    } else if (this.state.selectedAssignee !== 'ALL') {
      tasks = tasks.filter(t => t.assignee_id === parseInt(this.state.selectedAssignee));
    }

    if (this.state.selectedPriority !== 'ALL') {
      tasks = tasks.filter(t => t.priority === this.state.selectedPriority);
    }

    if (this.state.searchQuery) {
      tasks = tasks.filter(t => 
        (t.title && t.title.toLowerCase().includes(this.state.searchQuery)) ||
        (t.description && t.description.toLowerCase().includes(this.state.searchQuery)) ||
        (t.assignee_name && t.assignee_name.toLowerCase().includes(this.state.searchQuery))
      );
    }

    return tasks;
  },

  render() {
    this.renderAuthHeader();
    this.renderHeaderSelect();
    this.renderStats();
    this.renderTaskViews();
    this.renderAnalytics();
    this.renderMembers();
    this.renderEmailLogs();
  },

  renderAuthHeader() {
    const authSection = document.getElementById('auth-user-section');
    if (!authSection) return;

    const user = this.state.currentUser;
    if (user) {
      let roleBadgeColor = 'rgba(216, 27, 96, 0.12); color: var(--dfox-magenta);';
      if (user.role === 'HOD') roleBadgeColor = 'background: #ffe4e6; color: #e11d48;';
      else if (user.role === 'Team Lead') roleBadgeColor = 'background: #f3e8ff; color: #7e22ce;';
      else roleBadgeColor = 'background: #e0f2fe; color: #0284c7;';

      authSection.innerHTML = `
        <div style="display:flex; align-items:center; gap: 8px; background:#ffffff; border:1px solid var(--dfox-border-subtle); padding:4px 10px 4px 6px; border-radius:var(--radius-full); box-shadow:var(--shadow-sm);">
          <div class="avatar-circle" style="background:${user.avatar_color}; width:26px; height:26px; font-size:0.75rem;">
            ${user.name.charAt(0)}
          </div>
          <div style="display:flex; flex-direction:column; text-align:left;">
            <div style="font-size:0.78rem; font-weight:800; color:var(--text-main); line-height:1.1;">${user.name}</div>
            <div style="font-size:0.65rem; color:var(--text-muted); font-weight:700;">${user.designation}</div>
          </div>
          <span style="font-size:0.68rem; font-weight:800; padding:2px 7px; border-radius:4px; ${roleBadgeColor}">
            ${user.role}
          </span>
          <button class="btn btn-secondary" style="padding:2px 8px; font-size:0.7rem; border-radius:var(--radius-full); margin-left:4px;" onclick="App.handleLogout()" title="Sign Out">
            Logout
          </button>
        </div>
      `;
    } else {
      authSection.innerHTML = ``;
    }
  },

  renderHeaderSelect() {
    const devSelect = document.getElementById('header-dev-select');
    const assigneeFilter = document.getElementById('filter-assignee');
    
    if (devSelect) {
      devSelect.innerHTML = this.state.members.map(m => 
        `<option value="${m.id}" ${m.id === this.state.selectedDevId ? 'selected' : ''}>👤 ${m.name} (${m.designation || m.role})</option>`
      ).join('');
    }

    if (assigneeFilter) {
      const currentVal = this.state.selectedAssignee;
      assigneeFilter.innerHTML = `<option value="ALL">All Assignees</option>` + 
        this.state.members.map(m => 
          `<option value="${m.id}" ${m.id.toString() === currentVal ? 'selected' : ''}>${m.name}</option>`
        ).join('');
    }
  },

  renderStats() {
    const analytics = this.state.analytics;
    if (!analytics) return;

    document.getElementById('stat-total-tasks').textContent = analytics.total_tasks;
    document.getElementById('stat-in-progress').textContent = analytics.in_progress_tasks;
    document.getElementById('stat-completed').textContent = analytics.completed_tasks;
    document.getElementById('stat-avg-efficiency').textContent = `${analytics.avg_efficiency}%`;
    document.getElementById('stat-total-hours').textContent = `${analytics.total_actual_hours}h / ${analytics.total_allocated_hours}h`;
  },

  renderTaskViews() {
    const tasks = this.getFilteredTasks();

    const columns = {
      'Assigned': tasks.filter(t => t.status === 'Assigned'),
      'In Progress': tasks.filter(t => t.status === 'In Progress'),
      'In Review': tasks.filter(t => t.status === 'In Review'),
      'Completed': tasks.filter(t => t.status === 'Completed')
    };

    Object.keys(columns).forEach(status => {
      const colId = `col-${status.toLowerCase().replace(' ', '-')}`;
      const container = document.getElementById(colId);
      const countEl = document.getElementById(`count-${status.toLowerCase().replace(' ', '-')}`);
      
      if (countEl) countEl.textContent = columns[status].length;
      if (container) {
        if (columns[status].length === 0) {
          container.innerHTML = `<div style="text-align:center; padding: 2rem 1rem; color: var(--text-dim); font-size: 0.8rem;">No tasks</div>`;
        } else {
          container.innerHTML = columns[status].map(t => this.renderTaskCardHTML(t)).join('');
        }
      }
    });

    const tableBody = document.getElementById('tasks-table-body');
    if (tableBody) {
      if (tasks.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 2rem; color: var(--text-dim);">No tasks found matching criteria</td></tr>`;
      } else {
        tableBody.innerHTML = tasks.map(t => this.renderTableRowHTML(t)).join('');
      }
    }
  },

  renderTaskCardHTML(t) {
    const eff = t.efficiency;
    let effBadge = '';
    if (eff !== null && eff !== undefined) {
      let effClass = 'eff-acceptable';
      let effIcon = '⚡';
      if (eff >= 120) { effClass = 'eff-super'; effIcon = '🚀'; }
      else if (eff >= 100) { effClass = 'eff-optimal'; effIcon = '🎯'; }
      else if (eff < 80) { effClass = 'eff-overrun'; effIcon = '⚠️'; }
      effBadge = `<span class="efficiency-badge ${effClass}">${effIcon} ${eff}% Efficiency</span>`;
    }

    const allocStr = `${t.allocated_hours}h ${t.allocated_minutes}m`;
    const actualStr = t.actual_total_hours > 0 ? `${t.actual_hours}h ${t.actual_minutes}m` : 'Not logged';

    return `
      <div class="task-card" onclick="App.openTaskActionModal(${t.id})">
        <div class="task-top-bar">
          <span class="priority-badge priority-${t.priority}">${t.priority}</span>
        </div>
        <div class="task-title">${t.title}</div>
        <div class="task-desc-preview">${t.description || 'No detailed instructions.'}</div>
        
        <div class="task-timing-box">
          <div class="time-item">
            <span class="time-label">Allocated</span>
            <span class="time-val">⏱️ ${allocStr}</span>
          </div>
          <div class="time-item" style="text-align:right;">
            <span class="time-label">Actual Spent</span>
            <span class="time-val">${actualStr}</span>
          </div>
        </div>

        ${effBadge ? `<div style="margin-bottom: 0.75rem;">${effBadge}</div>` : ''}

        <div class="task-footer">
          <div class="assignee-chip">
            <div class="avatar-circle" style="background: ${t.assignee_avatar_color || '#7928CA'};">
              ${(t.assignee_name || 'U').charAt(0)}
            </div>
            <span class="assignee-name">${t.assignee_name || 'Unassigned'}</span>
          </div>
          <div class="due-chip">
            📅 ${t.due_date || 'No date'}
          </div>
        </div>
      </div>
    `;
  },

  renderTableRowHTML(t) {
    const allocStr = `${t.allocated_hours}h ${t.allocated_minutes}m (${t.allocated_total_hours}h)`;
    const actualStr = t.actual_total_hours > 0 ? `${t.actual_hours}h ${t.actual_minutes}m` : '-';
    
    let effBadge = '<span style="color:var(--text-dim);">-</span>';
    if (t.efficiency !== null && t.efficiency !== undefined) {
      let effClass = 'eff-acceptable';
      if (t.efficiency >= 120) effClass = 'eff-super';
      else if (t.efficiency >= 100) effClass = 'eff-optimal';
      else if (t.efficiency < 80) effClass = 'eff-overrun';
      effBadge = `<span class="efficiency-badge ${effClass}">${t.efficiency}%</span>`;
    }

    const statusClass = t.status.replace(' ', '-');

    return `
      <tr onclick="App.openTaskActionModal(${t.id})" style="cursor:pointer;">
        <td>
          <div style="font-weight:800; color:var(--text-main);">${t.title}</div>
          <div style="font-size:0.75rem; color:var(--text-dim);">${t.priority} Priority</div>
        </td>
        <td>
          <div class="assignee-chip">
            <div class="avatar-circle" style="background: ${t.assignee_avatar_color || '#7928CA'};">
              ${(t.assignee_name || 'U').charAt(0)}
            </div>
            <span>${t.assignee_name || 'Unassigned'}</span>
          </div>
        </td>
        <td><span class="status-pill ${statusClass}">${t.status}</span></td>
        <td><strong>${allocStr}</strong></td>
        <td>${actualStr}</td>
        <td>${effBadge}</td>
        <td>${t.due_date || '-'}</td>
      </tr>
    `;
  },

  renderAnalytics() {
    const analytics = this.state.analytics;
    if (!analytics) return;

    const leaderboardEl = document.getElementById('leaderboard-container');
    if (leaderboardEl) {
      if (analytics.leaderboard.length === 0) {
        leaderboardEl.innerHTML = `<p style="color:var(--text-dim);">No performance data available yet.</p>`;
      } else {
        leaderboardEl.innerHTML = analytics.leaderboard.map((m, idx) => {
          return `
            <div class="member-eff-card">
              <span class="rank-corner">#${idx + 1}</span>
              <div class="member-header">
                <div class="member-avatar-lg" style="background: ${m.avatar_color};">
                  ${m.name.charAt(0)}
                </div>
                <div class="member-meta">
                  <h4>${m.name}</h4>
                  <p>${m.designation || m.role}</p>
                  <span style="font-size:0.72rem; color:var(--dfox-magenta); font-weight:800;">${m.performance_badge}</span>
                </div>
              </div>

              <div class="eff-score-box">
                <div>
                  <div style="font-size:0.7rem; color:var(--text-muted); text-transform:uppercase; font-weight:800;">Avg Efficiency</div>
                  <div class="eff-score-val">${m.avg_efficiency}%</div>
                </div>
                <div style="text-align:right;">
                  <div style="font-size:0.7rem; color:var(--text-muted); text-transform:uppercase; font-weight:800;">Tasks Completed</div>
                  <div style="font-size:1.3rem; font-weight:900; color:var(--text-main);">${m.completed_tasks} <span style="font-size:0.8rem; color:var(--text-dim);">/ ${m.total_tasks}</span></div>
                </div>
              </div>

              <div class="eff-stats-row">
                <div>
                  <div style="font-size:0.68rem; color:var(--text-dim); font-weight:700;">ALLOCATED</div>
                  <div class="eff-stat-num">${m.sum_allocated_hours}h</div>
                </div>
                <div>
                  <div style="font-size:0.68rem; color:var(--text-dim); font-weight:700;">ACTUAL SPENT</div>
                  <div class="eff-stat-num">${m.sum_actual_hours}h</div>
                </div>
                <div>
                  <div style="font-size:0.68rem; color:var(--text-dim); font-weight:700;">TIME SAVED</div>
                  <div class="eff-stat-num" style="color:${m.sum_allocated_hours >= m.sum_actual_hours ? '#059669' : '#e11d48'};">
                    ${(m.sum_allocated_hours - m.sum_actual_hours).toFixed(1)}h
                  </div>
                </div>
              </div>
            </div>
          `;
        }).join('');
      }
    }
  },

  renderMembers() {
    const listEl = document.getElementById('members-table-body');
    if (!listEl) return;

    if (this.state.members.length === 0) {
      listEl.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:2rem; color:var(--text-dim);">No registered team members found</td></tr>`;
    } else {
      listEl.innerHTML = this.state.members.map(m => {
        let roleBadgeColor = 'background:#f1f5f9; color:#475569;';
        if (m.role === 'HOD') roleBadgeColor = 'background:#ffe4e6; color:#e11d48;';
        else if (m.role === 'Team Lead') roleBadgeColor = 'background:#f3e8ff; color:#7e22ce;';
        else roleBadgeColor = 'background:#e0f2fe; color:#0284c7;';

        return `
          <tr>
            <td>
              <div style="display:flex; align-items:center; gap: 0.75rem;">
                <div class="avatar-circle" style="background: ${m.avatar_color}; width:32px; height:32px;">
                  ${m.name.charAt(0)}
                </div>
                <div>
                  <strong style="color:var(--text-main); font-weight:800;">${m.name}</strong>
                </div>
              </div>
            </td>
            <td><code style="color:#6441a5; font-weight:700;">${m.email}</code></td>
            <td><span style="padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:800; ${roleBadgeColor}">${m.role}</span></td>
            <td>${m.designation || '-'}</td>
            <td>
              <span class="status-pill Completed" style="font-size:0.7rem;">Verified</span>
            </td>
          </tr>
        `;
      }).join('');
    }
  },

  renderEmailLogs() {
    const listEl = document.getElementById('email-logs-list');
    if (!listEl) return;

    if (this.state.emailLogs.length === 0) {
      listEl.innerHTML = `<div style="padding:2rem; text-align:center; color:var(--text-dim);">No email notifications recorded yet.</div>`;
    } else {
      listEl.innerHTML = this.state.emailLogs.map(log => {
        let statusBadge = `<span class="badge" style="background:#dcfce7; color:#15803d; border:1px solid #bbf7d0;">SENT</span>`;
        if (log.status === 'SIMULATED') {
          statusBadge = `<span class="badge" style="background:#f3e8ff; color:#6441a5; border:1px solid #e9d5ff;">SIMULATED / PREVIEW</span>`;
        } else if (log.status === 'FAILED') {
          statusBadge = `<span class="badge" style="background:#fee2e2; color:#b91c1c; border:1px solid #fecaca;">FAILED</span>`;
        }

        return `
          <div class="email-log-item">
            <div>
              <div style="font-weight:800; color:var(--text-main); margin-bottom:2px;">${log.subject}</div>
              <div style="font-size:0.8rem; color:var(--text-muted);">
                Recipient: <strong>${log.recipient_name}</strong> (${log.recipient_email}) &bull; ${log.sent_at}
              </div>
              ${log.error_message ? `<div style="font-size:0.75rem; color:#e11d48; margin-top:2px;">ℹ️ ${log.error_message}</div>` : ''}
            </div>
            <div style="display:flex; align-items:center; gap: 0.75rem;">
              ${statusBadge}
              <button class="btn btn-secondary" style="padding:4px 10px; font-size:0.75rem;" onclick="App.previewEmailBody(${log.id})">View Email</button>
            </div>
          </div>
        `;
      }).join('');
    }
  },

  /* Modals and Actions */
  openCreateTaskModal() {
    const memberSelect = document.getElementById('create-assignee-select');
    if (memberSelect) {
      memberSelect.innerHTML = this.state.members.map(m => 
        `<option value="${m.id}">👤 ${m.name} (${m.designation || m.role})</option>`
      ).join('');
    }
    this.openModal('modal-create-task');
  },

  async handleCreateTaskSubmit(e) {
    e.preventDefault();
    const title = document.getElementById('create-task-title').value.trim();
    const description = document.getElementById('create-task-desc').value.trim();
    const priority = document.getElementById('create-task-priority').value;
    const assignee_id = parseInt(document.getElementById('create-assignee-select').value);
    const allocated_hours = parseFloat(document.getElementById('create-alloc-hours').value) || 0;
    const allocated_minutes = parseInt(document.getElementById('create-alloc-mins').value) || 0;
    const due_date = document.getElementById('create-due-date').value;
    const send_email = document.getElementById('create-send-email').checked;

    if (!title) {
      this.showToast('Please enter a task title', 'danger');
      return;
    }

    try {
      const res = await API.createTask({
        title,
        description,
        priority,
        assignee_id,
        allocated_hours,
        allocated_minutes,
        due_date,
        send_email
      });

      this.closeModal('modal-create-task');
      this.showToast('Task created and assigned successfully!', 'success');
      
      if (res.email_result) {
        if (res.email_result.mode === 'SMTP_DELIVERED') {
          this.showToast('📧 Email notification sent to developer!', 'success');
        } else if (res.email_result.mode === 'SIMULATED') {
          this.showToast('📝 Email notification logged in Email Center.', 'info');
        }
      }

      await this.refreshTasksAndAnalytics();
    } catch (err) {
      this.showToast('Failed to create task', 'danger');
    }
  },

  openTaskActionModal(taskId) {
    const task = this.state.tasks.find(t => t.id === taskId);
    if (!task) return;

    this.currentActiveTask = task;

    document.getElementById('action-task-title').textContent = task.title;
    document.getElementById('action-task-desc').textContent = task.description || 'No detailed instructions provided.';
    document.getElementById('action-task-priority').textContent = task.priority;
    document.getElementById('action-task-assignee').textContent = `${task.assignee_name || 'Unassigned'} (${task.assignee_email || ''})`;
    document.getElementById('action-task-allocated').textContent = `${task.allocated_hours}h ${task.allocated_minutes}m (${task.allocated_total_hours} hrs)`;
    document.getElementById('action-task-due').textContent = task.due_date || 'None';

    const statusSelect = document.getElementById('action-task-status');
    statusSelect.value = task.status;

    document.getElementById('complete-actual-hours').value = task.actual_hours || 0;
    document.getElementById('complete-actual-mins').value = task.actual_minutes || 0;
    document.getElementById('complete-notes').value = task.completion_notes || '';
    document.getElementById('complete-pr-link').value = task.pr_link || '';

    this.calculateCompletionEfficiencyPreview();
    this.openModal('modal-task-action');
  },

  calculateCompletionEfficiencyPreview() {
    if (!this.currentActiveTask) return;
    const allocTotal = this.currentActiveTask.allocated_total_hours || 0;
    const actH = parseFloat(document.getElementById('complete-actual-hours').value) || 0;
    const actM = parseInt(document.getElementById('complete-actual-mins').value) || 0;
    const actTotal = actH + (actM / 60.0);

    const effDisplay = document.getElementById('preview-efficiency-val');
    const badgeDisplay = document.getElementById('preview-efficiency-badge');

    if (actTotal > 0 && allocTotal > 0) {
      const eff = ((allocTotal / actTotal) * 100).toFixed(1);
      effDisplay.textContent = `${eff}%`;

      if (eff >= 120) {
        badgeDisplay.className = 'efficiency-badge eff-super';
        badgeDisplay.textContent = '🚀 Super Fast';
      } else if (eff >= 100) {
        badgeDisplay.className = 'efficiency-badge eff-optimal';
        badgeDisplay.textContent = '🎯 Optimal';
      } else if (eff >= 80) {
        badgeDisplay.className = 'efficiency-badge eff-acceptable';
        badgeDisplay.textContent = '⚡ Acceptable';
      } else {
        badgeDisplay.className = 'efficiency-badge eff-overrun';
        badgeDisplay.textContent = '⚠️ Overrun';
      }
    } else {
      effDisplay.textContent = '0%';
      badgeDisplay.textContent = 'Enter actual time';
      badgeDisplay.className = 'efficiency-badge';
    }
  },

  syncTimerToModal() {
    const { hours, minutes } = TaskTimer.getHoursAndMinutes();
    document.getElementById('complete-actual-hours').value = hours;
    document.getElementById('complete-actual-mins').value = minutes;
    this.calculateCompletionEfficiencyPreview();
    this.showToast(`⏱️ Synced ${hours}h ${minutes}m from stopwatch!`, 'info');
  },

  async handleTaskActionSave() {
    if (!this.currentActiveTask) return;
    const taskId = this.currentActiveTask.id;
    const status = document.getElementById('action-task-status').value;
    const actual_hours = parseFloat(document.getElementById('complete-actual-hours').value) || 0;
    const actual_minutes = parseInt(document.getElementById('complete-actual-mins').value) || 0;
    const completion_notes = document.getElementById('complete-notes').value.trim();
    const pr_link = document.getElementById('complete-pr-link').value.trim();

    try {
      await API.updateTaskStatusAndTime(taskId, {
        status,
        actual_hours,
        actual_minutes,
        completion_notes,
        pr_link
      });

      this.closeModal('modal-task-action');
      this.showToast('Task updated successfully!', 'success');
      await this.refreshTasksAndAnalytics();
    } catch (err) {
      this.showToast('Failed to update task', 'danger');
    }
  },

  async handleResendTaskEmail() {
    if (!this.currentActiveTask) return;
    try {
      await API.resendEmail(this.currentActiveTask.id);
      this.showToast('📧 Email notification re-dispatched!', 'success');
      await this.refreshTasksAndAnalytics();
    } catch (err) {
      this.showToast('Failed to send email notification', 'danger');
    }
  },

  async handleDeleteTask() {
    if (!this.currentActiveTask) return;
    if (confirm(`Are you sure you want to delete task "${this.currentActiveTask.title}"?`)) {
      try {
        await API.deleteTask(this.currentActiveTask.id);
        this.closeModal('modal-task-action');
        this.showToast('Task deleted', 'info');
        await this.refreshTasksAndAnalytics();
      } catch (err) {
        this.showToast('Failed to delete task', 'danger');
      }
    }
  },

  // Settings & SMTP
  openSettingsModal() {
    const s = this.state.settings;
    document.getElementById('smtp-enabled').checked = s.smtp_enabled === 'true';
    document.getElementById('smtp-host').value = s.smtp_host || '';
    document.getElementById('smtp-port').value = s.smtp_port || '587';
    document.getElementById('smtp-user').value = s.smtp_user || '';
    document.getElementById('smtp-pass').value = s.smtp_pass || '';
    document.getElementById('smtp-from-name').value = s.smtp_from_name || 'DFOX Media Tracker';
    document.getElementById('smtp-from-email').value = s.smtp_from_email || '';
    document.getElementById('smtp-tls').checked = s.smtp_tls !== 'false';

    this.openModal('modal-settings');
  },

  async handleSaveSettings(e) {
    e.preventDefault();
    const settings = {
      smtp_enabled: document.getElementById('smtp-enabled').checked ? 'true' : 'false',
      smtp_host: document.getElementById('smtp-host').value.trim(),
      smtp_port: document.getElementById('smtp-port').value.trim(),
      smtp_user: document.getElementById('smtp-user').value.trim(),
      smtp_pass: document.getElementById('smtp-pass').value.trim(),
      smtp_from_name: document.getElementById('smtp-from-name').value.trim(),
      smtp_from_email: document.getElementById('smtp-from-email').value.trim(),
      smtp_tls: document.getElementById('smtp-tls').checked ? 'true' : 'false'
    };

    try {
      await API.saveSettings(settings);
      this.state.settings = { ...this.state.settings, ...settings };
      this.closeModal('modal-settings');
      this.showToast('Settings saved successfully!', 'success');
    } catch (err) {
      this.showToast('Failed to save settings', 'danger');
    }
  },

  async handleTestSMTP() {
    const btn = document.getElementById('btn-test-smtp');
    btn.disabled = true;
    btn.textContent = 'Testing...';

    const smtpData = {
      smtp_host: document.getElementById('smtp-host').value.trim(),
      smtp_port: document.getElementById('smtp-port').value.trim(),
      smtp_user: document.getElementById('smtp-user').value.trim(),
      smtp_pass: document.getElementById('smtp-pass').value.trim(),
      smtp_tls: document.getElementById('smtp-tls').checked,
      test_recipient: document.getElementById('smtp-test-recipient').value.trim()
    };

    try {
      const res = await API.testSMTP(smtpData);
      if (res.success) {
        this.showToast(res.message || 'SMTP Connection Successful!', 'success');
      } else {
        this.showToast(`SMTP Error: ${res.error}`, 'danger');
      }
    } catch (err) {
      this.showToast('Failed to test SMTP connection', 'danger');
    } finally {
      btn.disabled = false;
      btn.textContent = 'Test Connection';
    }
  },

  previewEmailBody(logId) {
    const log = this.state.emailLogs.find(l => l.id === logId);
    if (!log) return;

    const previewFrame = document.getElementById('email-preview-frame');
    previewFrame.srcdoc = log.body_html;
    this.openModal('modal-email-preview');
  },

  exportCSV() {
    window.location.href = '/api/export';
  },

  openModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('active');
  },

  closeModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('active');
  },

  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast';
    if (type === 'danger') toast.style.borderLeftColor = '#e11d48';
    if (type === 'success') toast.style.borderLeftColor = '#059669';
    if (type === 'warning') toast.style.borderLeftColor = '#d97706';

    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }
};

document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
