// ─────────────────────────────────────────────
// Qentis — Admin All Issuers
// ─────────────────────────────────────────────

async function loadAllIssuers() {
    try {
        const res = await fetch(`${API_BASE.INSTITUTION}/all/`, {
            headers: headers.auth()
        });
        const data = await res.json();
        const issuers = Array.isArray(data) ? data : [];
        const container = document.getElementById('issuers-list');

        if (issuers.length === 0) {
            container.innerHTML = '<p class="q-empty">No institutions found.</p>';
            return;
        }

        container.innerHTML = `
            <table class="q-table">
                <thead>
                    <tr>
                        <th>Institution</th>
                        <th>Type</th>
                        <th>Country</th>
                        <th>Email</th>
                        <th>Status</th>
                        <th>Registered</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${issuers.map(inst => `
                        <tr id="row-${inst.id}">
                            <td>${inst.name}</td>
                            <td>${inst.institution_type}</td>
                            <td>${inst.country}</td>
                            <td>${inst.contact_email}</td>
                            <td>
                                <span class="q-badge q-badge--${getBadgeClass(inst.status)}">
                                    ${inst.status}
                                </span>
                            </td>
                            <td>${formatDate(inst.created_at)}</td>
                            <td>
                                ${inst.status === 'APPROVED' ? `
                                    <button
                                        class="btn-q-danger"
                                        style="padding:4px 12px;font-size:12px"
                                        onclick="revokeIssuer('${inst.id}')">
                                        Revoke
                                    </button>
                                ` : '—'}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

    } catch (error) {
        document.getElementById('issuers-list').innerHTML =
            '<p class="q-error">Failed to load issuers.</p>';
    }
}

function getBadgeClass(status) {
    const map = {
        APPROVED: 'success',
        PENDING:  'warning',
        REJECTED: 'danger',
        REVOKED:  'danger',
    };
    return map[status] || 'default';
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
            showSuccess('alert', 'Institution revoked successfully.');
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