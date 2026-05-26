// ─────────────────────────────────────────────
// Qentis — Admin Pending Items Page
// ─────────────────────────────────────────────

let pendingItems = [];
let selectedItem = null;

async function loadPendingItems() {
    try {
        const items = await apiRequest(`${API_BASE.ITEMS}/pending/`, {
            method: 'GET',
            headers: headers.auth(),
        });

        pendingItems = items || [];
        renderItems(pendingItems);
    } catch (e) {
        document.getElementById('pending-loading').style.display = 'none';
        document.getElementById('pending-empty').style.display   = 'block';
    }
}

function renderItems(items) {
    document.getElementById('pending-loading').style.display = 'none';

    if (!items || items.length === 0) {
        document.getElementById('pending-empty').style.display = 'block';
        document.getElementById('pending-table').style.display = 'none';
        return;
    }

    document.getElementById('pending-empty').style.display = 'none';
    document.getElementById('pending-table').style.display = 'table';

    document.getElementById('pending-body').innerHTML = items.map(item => {
        const detail = getItemSummary(item);
        return `
            <tr>
                <td><span class="q-badge q-badge-category">${item.category}</span></td>
                <td class="td-mono" style="font-size:11px;">${item.issuer_id.slice(0,8)}...</td>
                <td>${detail}</td>
                <td>${formatDate(item.registered_at)}</td>
                <td>
                    <button class="btn-link" onclick="viewItem('${item.id}')">Review</button>
                </td>
            </tr>
        `;
    }).join('');
}

function getItemSummary(item) {
    if (item.certificate_detail)    return item.certificate_detail.student_name + ' — ' + item.certificate_detail.degree;
    if (item.pharmaceutical_detail) return item.pharmaceutical_detail.drug_name + ' — ' + item.pharmaceutical_detail.batch_number;
    if (item.document_detail)       return item.document_detail.owner_name + ' — ' + item.document_detail.document_type;
    if (item.banknote_detail)       return item.banknote_detail.currency + ' ' + item.banknote_detail.denomination;
    return '—';
}

function viewItem(itemId) {
    selectedItem = pendingItems.find(i => i.id === itemId);
    if (!selectedItem) return;

    // Reset sections
    document.getElementById('modal-cert').style.display   = 'none';
    document.getElementById('modal-pharma').style.display = 'none';
    document.getElementById('modal-doc').style.display    = 'none';
    document.getElementById('modal-bank').style.display   = 'none';
    document.getElementById('reject-section').style.display   = 'none';
    document.getElementById('confirm-reject-btn').style.display = 'none';
    document.getElementById('show-reject-btn').style.display    = 'inline-block';
    document.getElementById('approve-btn').style.display        = 'inline-block';
    hideAlert('reject-alert');

    document.getElementById('modal-title').textContent       = `Review — ${selectedItem.category}`;
    document.getElementById('modal-id').textContent          = selectedItem.id;
    document.getElementById('modal-category').textContent    = selectedItem.category;
    document.getElementById('modal-issuer').textContent      = selectedItem.issuer_id;
    document.getElementById('modal-institution').textContent = selectedItem.institution_id;
    document.getElementById('modal-date').textContent        = formatDate(selectedItem.registered_at);

    if (selectedItem.certificate_detail) {
        const d = selectedItem.certificate_detail;
        document.getElementById('modal-cert-student').textContent     = d.student_name;
        document.getElementById('modal-cert-matricule').textContent   = d.matricule;
        document.getElementById('modal-cert-degree').textContent      = d.degree;
        document.getElementById('modal-cert-grade').textContent       = d.grade;
        document.getElementById('modal-cert-date').textContent        = formatDate(d.graduation_date);
        document.getElementById('modal-cert-institution').textContent = d.institution_name;
        document.getElementById('modal-cert').style.display           = 'block';

    } else if (selectedItem.pharmaceutical_detail) {
        const d = selectedItem.pharmaceutical_detail;
        document.getElementById('modal-pharma-drug').textContent  = d.drug_name;
        document.getElementById('modal-pharma-batch').textContent = d.batch_number;
        document.getElementById('modal-pharma-mfr').textContent   = d.manufacturer;
        document.getElementById('modal-pharma-loc').textContent   = d.factory_location;
        document.getElementById('modal-pharma-prod').textContent  = formatDate(d.production_date);
        document.getElementById('modal-pharma-exp').textContent   = formatDate(d.expiry_date);
        document.getElementById('modal-pharma').style.display     = 'block';

    } else if (selectedItem.document_detail) {
        const d = selectedItem.document_detail;
        document.getElementById('modal-doc-type').textContent      = d.document_type;
        document.getElementById('modal-doc-owner').textContent     = d.owner_name;
        document.getElementById('modal-doc-authority').textContent = d.issuing_authority;
        document.getElementById('modal-doc-ref').textContent       = d.reference_number;
        document.getElementById('modal-doc-loc').textContent       = d.location;
        document.getElementById('modal-doc-date').textContent      = formatDate(d.issue_date);
        document.getElementById('modal-doc').style.display         = 'block';

    } else if (selectedItem.banknote_detail) {
        const d = selectedItem.banknote_detail;
        document.getElementById('modal-bank-currency').textContent = d.currency;
        document.getElementById('modal-bank-denom').textContent    = d.denomination;
        document.getElementById('modal-bank-serial').textContent   = d.serial_number;
        document.getElementById('modal-bank-series').textContent   = d.series;
        document.getElementById('modal-bank-date').textContent     = formatDate(d.issue_date);
        document.getElementById('modal-bank-issuer').textContent   = d.issuing_bank;
        document.getElementById('modal-bank').style.display        = 'block';
    }

    document.getElementById('item-modal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('item-modal').style.display = 'none';
    selectedItem = null;
    document.getElementById('reject-reason').value = '';
}

function showRejectSection() {
    document.getElementById('reject-section').style.display     = 'block';
    document.getElementById('show-reject-btn').style.display    = 'none';
    document.getElementById('confirm-reject-btn').style.display = 'inline-block';
    document.getElementById('approve-btn').style.display        = 'none';
}

async function confirmApprove() {
    if (!selectedItem) return;
    setLoading('approve-btn', true, 'Approving...');

    try {
        await apiRequest(`${API_BASE.ITEMS}/${selectedItem.id}/approve/`, {
            method: 'PUT',
            headers: headers.auth(),
            body: JSON.stringify({}),
        });

        closeModal();
        pendingItems = pendingItems.filter(i => i.id !== selectedItem?.id);
        renderItems(pendingItems);
        showAlert('alert', 'Item approved and registered on blockchain!', 'success');

    } catch (e) {
        const msg = e.data?.error || 'Failed to approve item.';
        showAlert('alert', msg, 'error');
    } finally {
        setLoading('approve-btn', false, '✓ Approve');
    }
}

async function confirmReject() {
    const reason = document.getElementById('reject-reason').value.trim();
    if (!reason) {
        showAlert('reject-alert', 'Please provide a rejection reason.', 'error');
        return;
    }

    setLoading('confirm-reject-btn', true, 'Rejecting...');

    try {
        await apiRequest(`${API_BASE.ITEMS}/${selectedItem.id}/reject/`, {
            method: 'PUT',
            headers: headers.auth(),
            body: JSON.stringify({ reason }),
        });

        closeModal();
        pendingItems = pendingItems.filter(i => i.id !== selectedItem?.id);
        renderItems(pendingItems);
        showAlert('alert', 'Item rejected.', 'success');

    } catch (e) {
        showAlert('reject-alert', 'Failed to reject item.', 'error');
    } finally {
        setLoading('confirm-reject-btn', false, 'Confirm Reject');
    }
}

// Init
loadPendingItems();