// ─────────────────────────────────────────────
// Qentis — Admin Analytics
// ─────────────────────────────────────────────

async function loadAnalytics() {
    try {
        // Load all institutions
        const instRes = await fetch(`${API_BASE.INSTITUTION}/all/`, {
            headers: headers.auth()
        });
        const institutions = await instRes.json();
        const approved = Array.isArray(institutions)
            ? institutions.filter(i => i.status === 'APPROVED').length
            : 0;

        // Load verification flags
        const flagsRes = await fetch(`${API_BASE.VERIFICATION}/flags/`, {
            headers: headers.auth()
        });
        const flags = await flagsRes.json();
        const totalFlags = Array.isArray(flags) ? flags.length : 0;
        const openFlags = Array.isArray(flags)
            ? flags.filter(f => f.status === 'OPEN').length
            : 0;

        // Update stats
        document.getElementById('stat-total').textContent = approved;
        document.getElementById('stat-certificates').textContent = '—';
        document.getElementById('stat-pharma').textContent = '—';
        document.getElementById('stat-documents').textContent = '—';
        document.getElementById('stat-banknotes').textContent = '—';

        // Verification stats
        document.getElementById('verification-stats').innerHTML = `
            <table class="q-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Approved Institutions</td>
                        <td>${approved}</td>
                    </tr>
                    <tr>
                        <td>Total Fraud Flags</td>
                        <td>${totalFlags}</td>
                    </tr>
                    <tr>
                        <td>Open Fraud Flags</td>
                        <td>${openFlags}</td>
                    </tr>
                </tbody>
            </table>
        `;

    } catch (error) {
        console.error('Analytics load error:', error);
    }
}

document.addEventListener('DOMContentLoaded', loadAnalytics);