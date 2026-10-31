/**
 * ANALYTIX CLUB - CORE API CLIENT
 * Handles REST requests, JWT bearer authorization, and toast notifications.
 */

const API = {
  // If served via FastAPI, origin is empty or matches host; otherwise default to localhost:8000
  BASE_URL: window.location.origin.includes('5500') || window.location.protocol === 'file:'
    ? 'http://localhost:8000'
    : window.location.origin,

  TOKEN_KEY: 'analytix_token',
  USER_KEY: 'analytix_user',

  getToken() {
    return localStorage.getItem(this.TOKEN_KEY);
  },

  setToken(token) {
    if (token) {
      localStorage.setItem(this.TOKEN_KEY, token);
    } else {
      localStorage.removeItem(this.TOKEN_KEY);
    }
  },

  getUser() {
    const raw = localStorage.getItem(this.USER_KEY);
    try {
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  },

  setUser(user) {
    if (user) {
      localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    } else {
      localStorage.removeItem(this.USER_KEY);
    }
  },

  clearAuth() {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  },

  async request(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${this.BASE_URL}${endpoint}`;
    const headers = options.headers || {};

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const config = {
      ...options,
      headers
    };

    try {
      const response = await fetch(url, config);

      // Handle 401 Unauthorized
      if (response.status === 401) {
        // If on an internal dashboard page, redirect to login
        const path = window.location.pathname;
        if (path.includes('dashboard') || path.includes('profile')) {
          this.clearAuth();
          window.location.href = 'login.html';
          return;
        }
      }

      const isJson = (response.headers.get('content-type') || '').includes('application/json');
      const data = isJson ? await response.json() : await response.text();

      if (!response.ok) {
        let errorDetail = 'An unexpected error occurred';
        if (data && typeof data === 'object') {
          if (Array.isArray(data.detail)) {
            errorDetail = data.detail.map(d => d.msg || JSON.stringify(d)).join(', ');
          } else if (data.detail) {
            errorDetail = data.detail;
          } else if (data.message) {
            errorDetail = data.message;
          }
        } else if (typeof data === 'string' && data.trim()) {
          errorDetail = data;
        }
        throw new Error(errorDetail);
      }

      return data;
    } catch (error) {
      console.error(`API Error [${options.method || 'GET'} ${endpoint}]:`, error);
      throw error;
    }
  },

  escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  },

  get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  },

  post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },

  patch(endpoint, data) {
    return this.request(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  },

  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  },

  upload(endpoint, formData) {
    return this.request(endpoint, {
      method: 'POST',
      body: formData
    });
  },

  toast(message, type = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const cleanMsg = this.escapeHtml(message);
    toast.innerHTML = `
      <span class="toast-message">${cleanMsg}</span>
    `;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  },

  formatDate(dateStr) {
    if (!dateStr) return 'TBA';
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return String(dateStr);
      return d.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    } catch (e) {
      return dateStr || 'TBA';
    }
  },

  formatDateTime(dateStr) {
    if (!dateStr) return 'TBA';
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return String(dateStr);
      return d.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (e) {
      return dateStr || 'TBA';
    }
  }
};

window.API = API;

