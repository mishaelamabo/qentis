// ─────────────────────────────────────────────
// Qentis — API Configuration
// ─────────────────────────────────────────────
const hostname = window.location.hostname;
const IS_LOCAL = hostname === 'localhost' || hostname === '127.0.0.1';
const IS_LAN   = hostname === '192.168.1.154';
const HOST     = IS_LOCAL ? 'localhost'
               : IS_LAN   ? '192.168.1.154'
               : hostname;

const API_BASE = {
    AUTH:         `http://${HOST}:8001/api/auth`,
    INSTITUTION:  `http://${HOST}:8002/api/institution`,
    ITEMS:        `http://${HOST}:8003/api/items`,
    BLOCKCHAIN:   `http://${HOST}:8004/api/blockchain`,
    OUTPUT:       `http://${HOST}:8005/api/output`,
    VERIFICATION: `http://${HOST}:8006/api/verify`,
    ADMIN:        `http://${HOST}:8007/api/admin`,
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
        localStorage.setItem('qentis_token_time', Date.now().toString());
    },

    setTokens: (access, refresh) => {
        localStorage.setItem('qentis_token', access);
        localStorage.setItem('qentis_refresh', refresh);
        localStorage.setItem('qentis_token_time', Date.now().toString());
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
        localStorage.removeItem('qentis_token_time');
    },

    isLoggedIn: () => !!localStorage.getItem('qentis_token'),

    isTokenExpired: () => {
        const tokenTime = localStorage.getItem('qentis_token_time');
        if (!tokenTime) return true;
        const elapsed = Date.now() - parseInt(tokenTime);
        const sixtyMinutes = 60 * 60 * 1000;
        return elapsed > sixtyMinutes;
    },

    guard: (requiredRole = null) => {
        if (!Auth.isLoggedIn() || Auth.isTokenExpired()) {
            Auth.clear();
            window.location.href = '/login.html';
            return;
        }
        if (requiredRole && Auth.getRole() !== requiredRole) {
            Auth.clear();
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

// ── Re-check token when user comes back to the tab ──
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
        const hasSidebar = document.body.dataset.sidebar;
        if (hasSidebar && (!Auth.isLoggedIn() || Auth.isTokenExpired())) {
            Auth.clear();
            window.location.href = '/login.html';
        }
    }
});

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