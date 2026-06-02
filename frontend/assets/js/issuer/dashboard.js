// ─────────────────────────────────────────────
// Qentis — Issuer Dashboard
// ─────────────────────────────────────────────

Auth.guard('ISSUER');

async function loadDashboard() {
    try {
        const items = await ItemsAPI.myItems();

        const total   = items ? items.length : 0;
        const onChain = items ? items.filter(i => i.blockchain_hash).length : 0;

        document.getElementById('stat-total').textContent      = total;
        document.getElementById('stat-blockchain').textContent = onChain;
        document.getElementById('stat-verified').textContent   = '—';
        document.getElementById('stat-alerts').textContent     = '0';

        document.getElementById('recent-items-loading').style.display = 'none';

        if (!items || items.length === 0) {
            document.getElementById('recent-items-empty').style.display = 'block';
            return;
        }

        const tbody = document.getElementById('recent-items-body');
        tbody.innerHTML = '';

        items.slice(0, 5).forEach(item => {
            const tr = document.createElement('tr');

            const tdItem = document.createElement('td');
            const name   = document.createElement('div');
            const hash   = document.createElement('div');
            name.className = 'item-name';
            hash.className = 'item-hash';
            name.textContent = item.serial_number || item.category;
            hash.textContent = formatHash(item.blockchain_hash);
            tdItem.appendChild(name);
            tdItem.appendChild(hash);

            const tdCat = document.createElement('td');
            const badge = document.createElement('span');
            badge.className   = 'q-badge q-badge-active';
            badge.textContent = item.category;
            tdCat.appendChild(badge);

            const tdDate = document.createElement('td');
            tdDate.className   = 'td-date';
            tdDate.textContent = formatDate(item.registered_at);

            const tdStatus = document.createElement('td');
            const sBadge   = document.createElement('span');
            const isReg    = item.status === 'REGISTERED';
            const isPend   = item.status === 'PENDING';
            sBadge.className   = `q-badge q-badge-${isReg ? 'approved' : isPend ? 'pending' : 'revoked'}`;
            sBadge.textContent = item.status;
            tdStatus.appendChild(sBadge);

            const tdAction = document.createElement('td');
            const link     = document.createElement('a');
            link.href      = 'my-items.html';
            link.className = 'link-sm';
            link.textContent = 'View';
            tdAction.appendChild(link);

            tr.appendChild(tdItem);
            tr.appendChild(tdCat);
            tr.appendChild(tdDate);
            tr.appendChild(tdStatus);
            tr.appendChild(tdAction);
            tbody.appendChild(tr);
        });

        document.getElementById('recent-items-table').style.display = 'table';

    } catch (e) {
        document.getElementById('recent-items-loading').style.display = 'none';
        document.getElementById('recent-items-empty').style.display   = 'block';
    }
}

loadDashboard();