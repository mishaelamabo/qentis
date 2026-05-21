/* ============================================================
   QENTIS — Shared layout components
   ============================================================ */

function injectNavbar() {
    const nav = document.createElement('nav');
    nav.className = 'q-navbar';
    nav.innerHTML = `
        <a href="/frontend/index.html" class="q-logo">Qen<span>tis</span></a>
        <div style="margin-left:auto;display:flex;align-items:center;gap:16px">
            <span style="font-size:13px;color:var(--q-text-muted)" id="navbar-user"></span>
            <button onclick="Auth.logout()" class="btn-q-outline" style="padding:6px 14px;font-size:13px">
                Sign out
            </button>
        </div>
    `;
    document.body.prepend(nav);
}

const SIDEBAR_LINKS = {
    issuer: [
        { href: '/frontend/pages/issuer/dashboard.html',     icon: '▦',  label: 'Dashboard',       id: 'dashboard' },
        { href: '/frontend/pages/issuer/register-item.html', icon: '+',  label: 'Register Item',   id: 'register-item' },
        { href: '/frontend/pages/issuer/my-items.html',      icon: '≡',  label: 'My Items',        id: 'my-items' },
        { href: '/frontend/pages/issuer/account.html',       icon: '◎',  label: 'Account',         id: 'account' },
    ],
    owner: [
        { href: '/frontend/pages/owner/dashboard.html',      icon: '▦',  label: 'Dashboard',       id: 'dashboard' },
        { href: '/frontend/pages/owner/claim-item.html',     icon: '⊕',  label: 'Claim Item',      id: 'claim-item' },
        { href: '/frontend/pages/owner/my-items.html',       icon: '≡',  label: 'My Items',        id: 'my-items' },
        { href: '/frontend/pages/owner/account.html',        icon: '◎',  label: 'Account',         id: 'account' },
    ],
    admin: [
        { href: '/frontend/pages/admin/dashboard.html',       icon: '▦',  label: 'Dashboard',       id: 'dashboard' },
        { href: '/frontend/pages/admin/pending-issuers.html', icon: '⏳', label: 'Pending Issuers', id: 'pending-issuers' },
        { href: '/frontend/pages/admin/all-issuers.html',     icon: '🏢', label: 'All Issuers',     id: 'all-issuers' },
        { href: '/frontend/pages/admin/activity.html',        icon: '≡',  label: 'All Activity',    id: 'activity' },
        { href: '/frontend/pages/admin/fraud-alerts.html',    icon: '⚠',  label: 'Fraud Alerts',    id: 'fraud-alerts' },
        { href: '/frontend/pages/admin/analytics.html',       icon: '◈',  label: 'Analytics',       id: 'analytics' },
    ],
};

function injectSidebar(role, activePage) {
    const links = SIDEBAR_LINKS[role] || [];
    const sidebar = document.createElement('aside');
    sidebar.className = 'q-sidebar';
    sidebar.innerHTML = `
        <div class="q-sidebar-section">${role.toUpperCase()}</div>
        ${links.map(l => `
            <a href="${l.href}" class="q-sidebar-link ${l.id === activePage ? 'active' : ''}">
                <span style="font-size:14px;width:18px;text-align:center">${l.icon}</span>
                ${l.label}
            </a>
        `).join('')}
    `;
    const nav = document.querySelector('.q-navbar');
    if (nav) nav.after(sidebar);
    else document.body.prepend(sidebar);
}