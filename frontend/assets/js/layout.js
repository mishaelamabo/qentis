/* ============================================================
   QENTIS — Shared layout components
   ============================================================ */

function injectNavbar() {
    const nav = document.createElement('nav');
    nav.className = 'q-navbar';

    // Check if we're on a page with a sidebar (dashboard pages)
    const hasSidebar = document.body.dataset.sidebar;

    const logoHref = hasSidebar ? 'javascript:history.back()' : '/frontend/index.html';
    const logoTitle = hasSidebar ? 'Go back' : 'Go to home';

    nav.innerHTML = `
        <button class="q-hamburger" id="hamburger-btn" onclick="toggleSidebar()" aria-label="Menu">
            <span></span>
            <span></span>
            <span></span>
        </button>
        <a href="${logoHref}" title="${logoTitle}" class="q-logo">Qen<span>tis</span></a>
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
        { href: '/frontend/pages/admin/pending-items.html',   icon: '📦', label: 'Pending Items',   id: 'pending-items' },
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
    sidebar.id = 'q-sidebar';
    sidebar.innerHTML = `
        <div class="q-sidebar-section">${role.toUpperCase()}</div>
        ${links.map(l => `
            <a href="${l.href}" class="q-sidebar-link ${l.id === activePage ? 'active' : ''}" onclick="closeSidebar()">
                <span style="font-size:14px;width:18px;text-align:center">${l.icon}</span>
                ${l.label}
            </a>
        `).join('')}
    `;
    const nav = document.querySelector('.q-navbar');
    if (nav) nav.after(sidebar);
    else document.body.prepend(sidebar);

    // Create overlay for mobile
    const overlay = document.createElement('div');
    overlay.id = 'sidebar-overlay';
    overlay.onclick = closeSidebar;
    document.body.appendChild(overlay);
}

function toggleSidebar() {
    const sidebar = document.getElementById('q-sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const btn     = document.getElementById('hamburger-btn');
    if (!sidebar) return;
    sidebar.classList.toggle('open');
    overlay.classList.toggle('show');
    btn.classList.toggle('active');
}

function closeSidebar() {
    const sidebar = document.getElementById('q-sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const btn     = document.getElementById('hamburger-btn');
    if (!sidebar) return;
    sidebar.classList.remove('open');
    overlay.classList.remove('show');
    if (btn) btn.classList.remove('active');
}