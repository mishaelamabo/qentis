// ─────────────────────────────────────────────
// Qentis — Admin Activity Log
// ─────────────────────────────────────────────

async function loadActivity() {
    const container = document.getElementById('activity-list');

    try {
        const res = await fetch(`${API_BASE.VERIFICATION}/flags/`, {
            headers: headers.auth()
        });
        const flags = await res.json();
        const data = Array.isArray(flags) ? flags : [];

        if (data.length === 0) {
            container.innerHTML = '<p class="q-empty">No activity found.</p>';
            return;
        }

        container.innerHTML = `
            <table class="q-table">
                <thead>
                    <tr>
                        <th>Item ID</th>
                        <th>Verifications</th>
                        <th>Flagged At</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.map(item => `
                        <tr>
                            <td style="font-family:monospace;font-size:12px">
                                ${item.item_id}
                            </td>
                            <td>${item.verification_count}</td>
                            <td>${formatDateTime(item.flagged_at)}</td>
                            <td>
                                <span class="q-badge q-badge--${item.status === 'OPEN' ? 'warning' : 'success'}">
                                    ${item.status}
                                </span>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

    } catch (error) {
        container.innerHTML = '<p class="q-error">Failed to load activity.</p>';
    }
}

document.addEventListener('DOMContentLoaded', loadActivity);