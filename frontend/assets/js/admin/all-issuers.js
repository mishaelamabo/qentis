// ─────────────────────────────────────────────
// Qentis — Admin All Issuers
// ─────────────────────────────────────────────

async function loadAllIssuers() {
    try {
        const res = await fetch(`${API_BASE.INSTITUTION}/all/`, {
            headers: headers.auth()
        });
        const data    = await res.json();
        const issuers = Array.isArray(data) ? data : [];

        document.getElementById('issuers-loading').style.display = 'none';

        if (issuers.length === 0) {
            document.getElementById('issuers-empty').style.display = 'block';
            return;
        }

        document.getElementById('issuers-table-wrap').style.display = 'block';
        const tbody = document.getElementById('issuers-body');
        tbody.innerHTML = '';

        issuers.forEach(inst => {
            const tr = document.createElement('tr');
            tr.id = `row-${inst.id}`;

            const tdName = document.createElement('td');
            tdName.textContent = inst.name;

            const tdType = document.createElement('td');
            tdType.textContent = inst.institution_type;

            const tdCountry = document.createElement('td');
            tdCountry.textContent = inst.country;

            const tdEmail = document.createElement('td');
            tdEmail.textContent = inst.contact_email;

            const tdStatus = document.createElement('td');
            const badge = document.createElement('span');
            badge.className   = `q-badge q-badge-${inst.status.toLowerCase()}`;
            badge.textContent = inst.status;
            tdStatus.appendChild(badge);

            const tdDate = document.createElement('td');
            tdDate.textContent = formatDate(inst.created_at);

            const tdAction = document.createElement('td');
            if (inst.status === 'APPROVED') {
                const btn = document.createElement('button');
                btn.className   = 'btn-q-danger';
                btn.style.cssText = 'padding:4px 12px;font-size:12px';
                btn.textContent = 'Revoke';
                btn.onclick     = () => revokeIssuer(inst.id);
                tdAction.appendChild(btn);
            } else {
                tdAction.textContent = '—';
            }

            tr.appendChild(tdName);
            tr.appendChild(tdType);
            tr.appendChild(tdCountry);
            tr.appendChild(tdEmail);
            tr.appendChild(tdStatus);
            tr.appendChild(tdDate);
            tr.appendChild(tdAction);
            tbody.appendChild(tr);
        });

    } catch (error) {
        document.getElementById('issuers-loading').style.display = 'none';
        showAlert('alert', 'Failed to load issuers.', 'error');
    }
}

async function revokeIssuer(institutionId) {
    const reason = prompt('Enter revocation reason:');
    if (!reason) return;

    try {
        const res = await fetch(`${API_BASE.INSTITUTION}/${institutionId}/revoke/`, {
            method: 'PUT',
            headers: headers.auth(),
            body: JSON.stringify({ reason })
        });

        if (res.ok) {
            showAlert('alert', 'Institution revoked successfully.', 'success');
            loadAllIssuers();
        } else {
            const data = await res.json();
            showAlert('alert', data.error || 'Failed to revoke institution.', 'error');
        }
    } catch (error) {
        showAlert('alert', 'Connection error.', 'error');
    }
}

document.addEventListener('DOMContentLoaded', loadAllIssuers);