// ─────────────────────────────────────────────
// Qentis — API Configuration
// ─────────────────────────────────────────────

const API_BASE = {
    AUTH:         'http://localhost:8001/api/auth',
    INSTITUTION:  'http://localhost:8002/api/institution',
    ITEMS:        'http://localhost:8003/api/items',
    BLOCKCHAIN:   'http://localhost:8004/api/blockchain',
    OUTPUT:       'http://localhost:8005/api/output',
    VERIFICATION: 'http://localhost:8006/api/verify',
    ADMIN:        'http://localhost:8007/api/admin',
};

// ─────────────────────────────────────────────
// Token & User Management
// ─────────────────────────────────────────────

const Auth = {
    getToken: () => localStorage.getItem('qentis_token'),
    getRefreshToken: () => localStorage.getItem('qentis_refresh'),
    getUser: () => JSON.parse(localStorage.getItem('qentis_user') || 'null'),
    getRole: () => localStorage.getItem('qentis_role'),

    setToken: (access) => {
        localStorage.setItem('qentis_token', access);
    },

    setTokens: (access, refresh) => {
        localStorage.setItem('qentis_token', access);
        localStorage.setItem('qentis_refresh', refresh);
    },

    setUser: (user) => {
        localStorage.setItem('qentis_user', JSON.stringify(user));
        localStorage.setItem('qentis_role', user.role);
    },

    clear: () => {
        localStorage.removeItem('qentis_token');
        localStorage.removeItem('qentis_refresh');
        localStorage.removeItem('qentis_user');
        localStorage.removeItem('qentis_role');
    },

    isLoggedIn: () => !!localStorage.getItem('qentis_token'),

    guard: (requiredRole = null) => {
        if (!Auth.isLoggedIn()) {
            window.location.href = '/login.html';
            return;
        }
        if (requiredRole && Auth.getRole() !== requiredRole) {
            window.location.href = '/login.html';
        }
    },

    logout: async () => {
        const refresh_token = Auth.getRefreshToken();
        try {
            await fetch(`${API_BASE.AUTH}/logout/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${Auth.getToken()}`
                },
                body: JSON.stringify({ refresh_token }),
            });
        } catch (e) {
            // Clear even if server call fails
        } finally {
            Auth.clear();
            window.location.href = '/login.html';
        }
    },
};

// ─────────────────────────────────────────────
// HTTP Headers
// ─────────────────────────────────────────────

const headers = {
    json: () => ({
        'Content-Type': 'application/json',
    }),

    auth: () => ({
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${Auth.getToken()}`,
    }),

    authOnly: () => ({
        'Authorization': `Bearer ${Auth.getToken()}`,
    }),
};

// ─────────────────────────────────────────────
// Base API Request Handler
// ─────────────────────────────────────────────

async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, options);

        if (response.status === 401) {
            Auth.clear();
            window.location.href = '/login.html';
            return;
        }

        const data = await response.json();

        if (!response.ok) {
            throw { status: response.status, data };
        }

        return data;

    } catch (error) {
        if (error.status) throw error;
        throw { status: 0, data: { error: 'Network error. Please check your connection.' } };
    }
}

// ─────────────────────────────────────────────
// Role-based redirect
// ─────────────────────────────────────────────

function redirectByRole(role) {
    const map = {
        ISSUER:   '/pages/issuer/dashboard.html',
        ADMIN:    '/pages/admin/dashboard.html',
        VERIFIER: '/pages/verifier/verify.html',
    };
    window.location.href = map[role] || '/login.html';
}

// ─────────────────────────────────────────────
// UI Helpers
// ─────────────────────────────────────────────

function showAlert(elementId, message, type = 'error') {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.textContent = message;
    el.className = `q-alert q-alert--${type}`;
    el.style.display = 'block';
}

function hideAlert(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.style.display = 'none';
    el.textContent = '';
}

function showSuccess(elementId, message) {
    showAlert(elementId, message, 'success');
}

function setLoading(buttonId, loading, loadingText = 'Loading...') {
    const btn = document.getElementById(buttonId);
    if (!btn) return;
    btn.disabled = loading;
    if (loading) {
        btn.dataset.originalText = btn.textContent;
        btn.textContent = loadingText;
    } else {
        btn.textContent = btn.dataset.originalText || loadingText;
    }
}

function formatDate(dateString) {
    if (!dateString) return '—';
    return new Date(dateString).toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    });
}

function formatDateTime(dateString) {
    if (!dateString) return '—';
    return new Date(dateString).toLocaleString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatHash(hash) {
    if (!hash) return '—';
    return hash.slice(0, 10) + '...' + hash.slice(-6);
}