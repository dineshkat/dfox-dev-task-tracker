// API Client for DFOX Dev Task Tracker with Authentication Support

const API = {
  getToken() {
    return localStorage.getItem('dfox_auth_token');
  },

  setToken(token) {
    if (token) {
      localStorage.setItem('dfox_auth_token', token);
    } else {
      localStorage.removeItem('dfox_auth_token');
    }
  },

  getAuthHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  },

  // ----------------- Auth API -----------------
  async signup(data) {
    const res = await fetch('/api/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return await res.json();
  },

  async verifyOTP(email, otp) {
    const res = await fetch('/api/auth/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, otp })
    });
    return await res.json();
  },

  async resendVerification(email) {
    const res = await fetch('/api/auth/resend-verification', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    return await res.json();
  },

  async login(email, password) {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (data.token) {
      this.setToken(data.token);
    }
    return data;
  },

  async getMe() {
    const res = await fetch('/api/auth/me', {
      headers: this.getAuthHeaders()
    });
    return await res.json();
  },

  async logout() {
    await fetch('/api/auth/logout', {
      method: 'POST',
      headers: this.getAuthHeaders()
    });
    this.setToken(null);
  },

  // ----------------- Tasks API -----------------
  async getTasks(params = {}) {
    const query = new URLSearchParams(params).toString();
    const res = await fetch(`/api/tasks?${query}`, {
      headers: this.getAuthHeaders()
    });
    return await res.json();
  },

  async getTask(id) {
    const res = await fetch(`/api/tasks/${id}`, {
      headers: this.getAuthHeaders()
    });
    return await res.json();
  },

  async createTask(taskData) {
    const res = await fetch('/api/tasks', {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(taskData)
    });
    return await res.json();
  },

  async updateTaskStatusAndTime(id, updateData) {
    const res = await fetch(`/api/tasks/${id}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(updateData)
    });
    return await res.json();
  },

  async deleteTask(id) {
    const res = await fetch(`/api/tasks/${id}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders()
    });
    return await res.json();
  },

  // ----------------- Members & Analytics -----------------
  async getMembers() {
    const res = await fetch('/api/members', {
      headers: this.getAuthHeaders()
    });
    return await res.json();
  },

  async deleteMember(id) {
    const res = await fetch(`/api/members/${id}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders()
    });
    return await res.json();
  },

  async getAnalytics() {
    const res = await fetch('/api/analytics', {
      headers: this.getAuthHeaders()
    });
    return await res.json();
  },

  async getEmailLogs() {
    const res = await fetch('/api/email/logs', {
      headers: this.getAuthHeaders()
    });
    return await res.json();
  },

  async resendEmail(taskId) {
    const res = await fetch('/api/email/resend', {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ task_id: taskId })
    });
    return await res.json();
  },

  async getSettings() {
    const res = await fetch('/api/settings', {
      headers: this.getAuthHeaders()
    });
    return await res.json();
  },

  async saveSettings(settingsData) {
    const res = await fetch('/api/settings', {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(settingsData)
    });
    return await res.json();
  },

  async testSMTP(smtpData) {
    const res = await fetch('/api/settings/test-smtp', {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(smtpData)
    });
    return await res.json();
  }
};
