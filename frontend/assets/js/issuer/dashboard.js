// ─────────────────────────────────────────────
// Qentis — Issuer Dashboard
// ─────────────────────────────────────────────

Auth.guard('ISSUER');

async function loadDashboard() {
    try {
        // Load issuer's items
        const items = await ItemsAPI.myItems();

        // Total items
        document.getElementById('stat-total').textContent = items ? items.length : 0;

        // Count blockchain records (items with a blockchain_hash)
        const onChain = items ? items.filter(i => i.blockchain_hash).length : 0;
        document.getElementById('stat-blockchain').textContent = onChain;

        // Verified this month (placeholder — no direct endpoint yet)
        document.getElementById('stat-verified').textContent = '—';

        // Fraud alerts (placeholder)
        document.getElementById('stat-alerts').textContent = '0';

        // Recent items table
        document.getElementById('recent-items-loading').style.display = 'none';

        if (!items || items.length === 0) {
            document.getElementById('recent-items-empty').style.display = 'block';
            return;
        }

        document.getElementById('recent-items-table').style.display = 'table';
        document.getElementById('recent-items-body').innerHTML = items.slice(0, 5).map(item => `
            <tr>
                <td>
                    <div class="item-name">${item.category}</div>
                    <div class="item-hash">${formatHash(item.blockchain_hash)}</div>
                </td>
                <td><span class="q-badge q-badge-active">${item.category}</span></td>
                <td class="td-date">${formatDate(item.registered_at)}</td>
                <td><span class="q-badge q-badge-${item.status === 'REGISTERED' ? 'approved' : 'revoked'}">${item.status}</span></td>
                <td><a href="my-items.html" class="link-sm">View</a></td>
            </tr>
        `).join('');

    } catch (e) {
        document.getElementById('recent-items-loading').style.display = 'none';
        document.getElementById('recent-items-empty').style.display = 'block';
    }
}

loadDashboard();