// ─────────────────────────────────────────────
// Qentis — Admin Pending Issuers
// ─────────────────────────────────────────────

async function loadPendingIssuers() {
    try {
        const res = await fetch(`${API_BASE.INSTITUTION}/pending/`, {
            headers: headers.auth()
        });
        const data = await res.json();
        const pending = Array.isArray(data) ? data : [];
        const container = document.getElementById('pending-list');

        if (pending.length === 0) {
            container.innerHTML = '<p class="q-empty">No pending applications.</p>';
            return;
        }

        container.innerHTML = `
            <table class="q-table">
                <thead>
                    <tr>
                        <th>Institution</th>
                        <th>Type</th>
                        <th>Country</th>
                        <th>City</th>
                        <th>Email</th>
                        <th>Applied</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${pending.map(inst => `
                        <tr id="row-${inst.id}">
                            <td>${inst.name}</td>
                            <td>${inst.institution_type}</td>
                            <td>${inst.country}</td>
                            <td>${inst.city}</td>
                            <td>${inst.contact_email}</td>
                            <td>${formatDate(inst.created_at)}</td>
                            <td style="display:flex;gap:8px">
                                <button
                                    class="btn-q-primary"
                                    style="padding:4px 12px;font-size:12px"
                                    onclick="approveIssuer('${inst.id}')">
                                    Approve
                                </button>
                                <button
                                    class="btn-q-danger"
                                    style="padding:4px 12px;font-size:12px"
                                    onclick="rejectIssuer('${inst.id}')">
                                    Reject
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

    } catch (error) {
        document.getElementById('pending-list').innerHTML =
            '<p class="q-error">Failed to load pending issuers.</p>';
    }
}

async function approveIssuer(institutionId) {
    if (!confirm('Are you sure you want to approve this institution?')) return;

    try {
        const res = await fetch(`${API_BASE.INSTITUTION}/${institutionId}/approve/`, {
            method: 'PUT',
            headers: headers.auth()
        });

        if (res.ok) {
            showSuccess('alert', 'Institution approved successfully.');
            document.getElementById(`row-${institutionId}`).remove();
        } else {
            const data = await res.json();
            showAlert('alert', data.error || 'Failed to approve institution.', 'error');
        }
    } catch (error) {
        showAlert('alert', 'Connection error.', 'error');
    }
}

async function rejectIssuer(institutionId) {
    const reason = prompt('Enter rejection reason:');
    if (!reason) return;

    try {
        const res = await fetch(`${API_BASE.INSTITUTION}/${institutionId}/reject/`, {
            method: 'PUT',
            headers: headers.auth(),
            body: JSON.stringify({ reason })
        });

        if (res.ok) {
            showSuccess('alert', 'Institution rejected.');
            document.getElementById(`row-${institutionId}`).remove();
        } else {
            const data = await res.json();
            showAlert('alert', data.error || 'Failed to reject institution.', 'error');
        }
    } catch (error) {
        showAlert('alert', 'Connection error.', 'error');
    }
}

document.addEventListener('DOMContentLoaded', loadPendingIssuers);