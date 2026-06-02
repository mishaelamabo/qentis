// ─────────────────────────────────────────────
// Qentis — Admin Fraud Alerts
// ─────────────────────────────────────────────

async function loadFraudFlags() {
    try {
        const res = await fetch(`${API_BASE.VERIFICATION}/flags/`, {
            headers: headers.auth()
        });
        const data = await res.json();
        const flags = Array.isArray(data) ? data : [];
        const container = document.getElementById('flags-list');

        if (flags.length === 0) {
            container.innerHTML = '<p class="q-empty">No fraud flags found.</p>';
            return;
        }

        container.innerHTML = `
            <table class="q-table">
                <thead>
                    <tr>
                        <th>Item ID</th>
                        <th>Verifications</th>
                        <th>Window Start</th>
                        <th>Window End</th>
                        <th>Flagged At</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    ${flags.map(flag => `
                        <tr>
                            <td style="font-family:monospace;font-size:12px">
                                ${flag.item_id}
                            </td>
                            <td>${flag.verification_count}</td>
                            <td>${formatDateTime(flag.window_start)}</td>
                            <td>${formatDateTime(flag.window_end)}</td>
                            <td>${formatDateTime(flag.flagged_at)}</td>
                            <td>
                                <span class="q-badge q-badge--${flag.status === 'OPEN' ? 'warning' : 'success'}">
                                    ${flag.status}
                                </span>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

    } catch (error) {
        document.getElementById('flags-list').innerHTML =
            '<p class="q-error">Failed to load fraud flags.</p>';
    }
}

document.addEventListener('DOMContentLoaded', loadFraudFlags);