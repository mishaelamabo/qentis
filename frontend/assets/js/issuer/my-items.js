// ─────────────────────────────────────────────
// Qentis — My Items Page
// ─────────────────────────────────────────────

Auth.guard('ISSUER');

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

    document.getElementById('modal-title').textContent = `${selectedItem.category} — ${selectedItem.serial_number || 'No serial'}`;

    // Build detail rows based on category
    let detailHtml = `
        <div class="detail-row"><span class="detail-label">ID</span><span class="detail-value td-mono">${selectedItem.id}</span></div>
        <div class="detail-row"><span class="detail-label">Category</span><span class="detail-value">${selectedItem.category}</span></div>
        <div class="detail-row"><span class="detail-label">Status</span><span class="detail-value">${selectedItem.status}</span></div>
        <div class="detail-row"><span class="detail-label">Serial number</span><span class="detail-value td-mono">${selectedItem.serial_number || '—'}</span></div>
        <div class="detail-row"><span class="detail-label">Blockchain hash</span><span class="detail-value td-mono">${selectedItem.blockchain_hash || '—'}</span></div>
        <div class="detail-row"><span class="detail-label">Transaction</span><span class="detail-value td-mono">${selectedItem.transaction_hash || '—'}</span></div>
        <div class="detail-row"><span class="detail-label">Registered</span><span class="detail-value">${formatDate(selectedItem.registered_at)}</span></div>
    `;

    // Category-specific details
    if (selectedItem.certificate_detail) {
        const d = selectedItem.certificate_detail;
        detailHtml += `
            <hr/>
            <div class="detail-row"><span class="detail-label">Student name</span><span class="detail-value">${d.student_name}</span></div>
            <div class="detail-row"><span class="detail-label">Matricule</span><span class="detail-value">${d.matricule}</span></div>
            <div class="detail-row"><span class="detail-label">Degree</span><span class="detail-value">${d.degree}</span></div>
            <div class="detail-row"><span class="detail-label">Grade</span><span class="detail-value">${d.grade}</span></div>
            <div class="detail-row"><span class="detail-label">Graduation date</span><span class="detail-value">${formatDate(d.graduation_date)}</span></div>
        `;
    } else if (selectedItem.pharmaceutical_detail) {
        const d = selectedItem.pharmaceutical_detail;
        detailHtml += `
            <hr/>
            <div class="detail-row"><span class="detail-label">Drug name</span><span class="detail-value">${d.drug_name}</span></div>
            <div class="detail-row"><span class="detail-label">Batch number</span><span class="detail-value">${d.batch_number}</span></div>
            <div class="detail-row"><span class="detail-label">Manufacturer</span><span class="detail-value">${d.manufacturer}</span></div>
            <div class="detail-row"><span class="detail-label">Factory location</span><span class="detail-value">${d.factory_location}</span></div>
            <div class="detail-row"><span class="detail-label">Production date</span><span class="detail-value">${formatDate(d.production_date)}</span></div>
            <div class="detail-row"><span class="detail-label">Expiry date</span><span class="detail-value">${formatDate(d.expiry_date)}</span></div>
        `;
    } else if (selectedItem.document_detail) {
        const d = selectedItem.document_detail;
        detailHtml += `
            <hr/>
            <div class="detail-row"><span class="detail-label">Document type</span><span class="detail-value">${d.document_type}</span></div>
            <div class="detail-row"><span class="detail-label">Owner name</span><span class="detail-value">${d.owner_name}</span></div>
            <div class="detail-row"><span class="detail-label">Issuing authority</span><span class="detail-value">${d.issuing_authority}</span></div>
            <div class="detail-row"><span class="detail-label">Reference number</span><span class="detail-value">${d.reference_number}</span></div>
            <div class="detail-row"><span class="detail-label">Location</span><span class="detail-value">${d.location}</span></div>
            <div class="detail-row"><span class="detail-label">Issue date</span><span class="detail-value">${formatDate(d.issue_date)}</span></div>
        `;
    } else if (selectedItem.banknote_detail) {
        const d = selectedItem.banknote_detail;
        detailHtml += `
            <hr/>
            <div class="detail-row"><span class="detail-label">Currency</span><span class="detail-value">${d.currency}</span></div>
            <div class="detail-row"><span class="detail-label">Denomination</span><span class="detail-value">${d.denomination}</span></div>
            <div class="detail-row"><span class="detail-label">Serial number</span><span class="detail-value">${d.serial_number}</span></div>
            <div class="detail-row"><span class="detail-label">Series</span><span class="detail-value">${d.series}</span></div>
            <div class="detail-row"><span class="detail-label">Issue date</span><span class="detail-value">${formatDate(d.issue_date)}</span></div>
            <div class="detail-row"><span class="detail-label">Issuing bank</span><span class="detail-value">${d.issuing_bank}</span></div>
        `;
    }

    document.getElementById('modal-body').innerHTML = detailHtml;

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

        // Update local state
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