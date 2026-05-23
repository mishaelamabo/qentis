// ─────────────────────────────────────────────
// Qentis — My Items Page
// ─────────────────────────────────────────────

let allItems     = [];
let selectedItem = null;

async function loadItems() {
    try {
        const items = await ItemsAPI.myItems();
        allItems = items || [];
        renderItems(allItems);
    } catch (e) {
        document.getElementById('items-loading').style.display = 'none';
        document.getElementById('items-empty').style.display   = 'block';
    }
}

function renderItems(items) {
    document.getElementById('items-loading').style.display = 'none';

    if (!items || items.length === 0) {
        document.getElementById('items-empty').style.display = 'block';
        document.getElementById('items-table').style.display = 'none';
        return;
    }

    document.getElementById('items-empty').style.display = 'none';
    document.getElementById('items-table').style.display = 'table';

    document.getElementById('items-body').innerHTML = items.map(item => `
        <tr>
            <td><span class="q-badge q-badge-category">${item.category}</span></td>
            <td class="td-mono">${item.serial_number || '—'}</td>
            <td class="td-mono">${formatHash(item.blockchain_hash)}</td>
            <td>${formatDate(item.registered_at)}</td>
            <td>
                <span class="q-badge q-badge-${item.status === 'REGISTERED' ? 'approved' : 'revoked'}">
                    ${item.status}
                </span>
            </td>
            <td>
                <button class="btn-link" onclick="viewItem('${item.id}')">View</button>
                ${item.status === 'REGISTERED'
                    ? `<button class="btn-link btn-link--danger" onclick="openRevokeFor('${item.id}')">Revoke</button>`
                    : ''}
            </td>
        </tr>
    `).join('');
}

function applyFilters() {
    const category = document.getElementById('filter-category').value;
    const status   = document.getElementById('filter-status').value;

    let filtered = allItems;
    if (category) filtered = filtered.filter(i => i.category === category);
    if (status)   filtered = filtered.filter(i => i.status   === status);

    renderItems(filtered);
}

function viewItem(itemId) {
    selectedItem = allItems.find(i => i.id === itemId);
    if (!selectedItem) return;

    // Reset all category sections
    document.getElementById('modal-cert').style.display   = 'none';
    document.getElementById('modal-pharma').style.display = 'none';
    document.getElementById('modal-doc').style.display    = 'none';
    document.getElementById('modal-bank').style.display   = 'none';
    document.getElementById('modal-divider').style.display = 'none';

    // Set title
    document.getElementById('modal-title').textContent = `${selectedItem.category} — ${selectedItem.serial_number || 'No serial'}`;

    // Set QR code
    if (selectedItem.qr_code_url) {
        document.getElementById('qr-image').src         = selectedItem.qr_code_url;
        document.getElementById('qr-download').href     = selectedItem.qr_code_url;
        document.getElementById('qr-download').download = `QNT-${selectedItem.serial_number}.png`;
        document.getElementById('qr-section').style.display = 'block';
    } else {
        document.getElementById('qr-section').style.display = 'none';
    }

    // Set common fields
    document.getElementById('modal-id').textContent       = selectedItem.id;
    document.getElementById('modal-category').textContent = selectedItem.category;
    document.getElementById('modal-status').textContent   = selectedItem.status;
    document.getElementById('modal-serial').textContent   = selectedItem.serial_number   || '—';
    document.getElementById('modal-hash').textContent     = selectedItem.blockchain_hash || '—';
    document.getElementById('modal-tx').textContent       = selectedItem.transaction_hash || '—';
    document.getElementById('modal-date').textContent     = formatDate(selectedItem.registered_at);

    // Set category-specific fields
    if (selectedItem.certificate_detail) {
        const d = selectedItem.certificate_detail;
        document.getElementById('modal-cert-student').textContent   = d.student_name;
        document.getElementById('modal-cert-matricule').textContent = d.matricule;
        document.getElementById('modal-cert-degree').textContent    = d.degree;
        document.getElementById('modal-cert-grade').textContent     = d.grade;
        document.getElementById('modal-cert-date').textContent      = formatDate(d.graduation_date);
        document.getElementById('modal-cert').style.display         = 'block';
        document.getElementById('modal-divider').style.display      = 'block';

    } else if (selectedItem.pharmaceutical_detail) {
        const d = selectedItem.pharmaceutical_detail;
        document.getElementById('modal-pharma-drug').textContent  = d.drug_name;
        document.getElementById('modal-pharma-batch').textContent = d.batch_number;
        document.getElementById('modal-pharma-mfr').textContent   = d.manufacturer;
        document.getElementById('modal-pharma-loc').textContent   = d.factory_location;
        document.getElementById('modal-pharma-prod').textContent  = formatDate(d.production_date);
        document.getElementById('modal-pharma-exp').textContent   = formatDate(d.expiry_date);
        document.getElementById('modal-pharma').style.display     = 'block';
        document.getElementById('modal-divider').style.display    = 'block';

    } else if (selectedItem.document_detail) {
        const d = selectedItem.document_detail;
        document.getElementById('modal-doc-type').textContent      = d.document_type;
        document.getElementById('modal-doc-owner').textContent     = d.owner_name;
        document.getElementById('modal-doc-authority').textContent = d.issuing_authority;
        document.getElementById('modal-doc-ref').textContent       = d.reference_number;
        document.getElementById('modal-doc-loc').textContent       = d.location;
        document.getElementById('modal-doc-date').textContent      = formatDate(d.issue_date);
        document.getElementById('modal-doc').style.display         = 'block';
        document.getElementById('modal-divider').style.display     = 'block';

    } else if (selectedItem.banknote_detail) {
        const d = selectedItem.banknote_detail;
        document.getElementById('modal-bank-currency').textContent = d.currency;
        document.getElementById('modal-bank-denom').textContent    = d.denomination;
        document.getElementById('modal-bank-serial').textContent   = d.serial_number;
        document.getElementById('modal-bank-series').textContent   = d.series;
        document.getElementById('modal-bank-date').textContent     = formatDate(d.issue_date);
        document.getElementById('modal-bank-issuer').textContent   = d.issuing_bank;
        document.getElementById('modal-bank').style.display        = 'block';
        document.getElementById('modal-divider').style.display     = 'block';
    }

    // Hide revoke button if already revoked
    document.getElementById('revoke-btn').style.display =
        selectedItem.status === 'REVOKED' ? 'none' : 'inline-block';

    document.getElementById('item-modal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('item-modal').style.display = 'none';
    selectedItem = null;
}

function openRevokeFor(itemId) {
    selectedItem = allItems.find(i => i.id === itemId);
    document.getElementById('revoke-modal').style.display = 'flex';
}

function showRevokeConfirm() {
    closeModal();
    document.getElementById('revoke-modal').style.display = 'flex';
}

function closeRevokeModal() {
    document.getElementById('revoke-modal').style.display = 'none';
    document.getElementById('revoke-reason').value = '';
    hideAlert('revoke-alert');
}

async function confirmRevoke() {
    const reason = document.getElementById('revoke-reason').value.trim();
    if (!reason) {
        showAlert('revoke-alert', 'Please provide a reason for revocation.', 'error');
        return;
    }

    setLoading('confirm-revoke-btn', true, 'Revoking...');

    try {
        await ItemsAPI.revokeItem(selectedItem.id, reason);
        const idx = allItems.findIndex(i => i.id === selectedItem.id);
        if (idx !== -1) allItems[idx].status = 'REVOKED';
        closeRevokeModal();
        renderItems(allItems);
    } catch (e) {
        showAlert('revoke-alert', 'Failed to revoke item. Please try again.', 'error');
    } finally {
        setLoading('confirm-revoke-btn', false, 'Confirm revoke');
    }
}

// Init
loadItems();