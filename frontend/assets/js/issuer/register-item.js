// ─────────────────────────────────────────────
// Qentis — Register Item Page
// ─────────────────────────────────────────────

Auth.guard('ISSUER');

let selectedCategory = null;
let institutionId    = null;
let institutionName  = null;

// Load institution ID on page load
async function loadInstitution() {
    try {
        const data = await InstitutionAPI.getStatus();
        if (data && data.institution) {
            institutionId   = data.institution.id;
            institutionName = data.institution.name;
        }
    } catch (e) {
        showAlert('alert', 'Could not load institution info. Please contact support.', 'error');
    }
}

function selectCategory(category) {
    selectedCategory = category;
    document.querySelectorAll('.category-fields').forEach(f => f.style.display = 'none');
    document.getElementById(`fields-${category}`).style.display = 'block';
    document.getElementById('form-title').textContent = `Step 2 — ${category.charAt(0) + category.slice(1).toLowerCase()} details`;
    document.getElementById('step-category').style.display = 'none';
    document.getElementById('step-form').style.display = 'block';
    hideAlert('alert');
}

function goBackToCategory() {
    selectedCategory = null;
    document.getElementById('step-form').style.display    = 'none';
    document.getElementById('step-category').style.display = 'block';
    hideAlert('alert');
}

async function handleRegisterItem() {
    if (!selectedCategory) return;

    if (!institutionId) {
        showAlert('alert', 'Institution not found. Please ensure your institution is approved.', 'error');
        return;
    }

    let itemData = {
        category:         selectedCategory,
        institution_id:   institutionId,
        institution_name: institutionName,
    };

    if (selectedCategory === 'CERTIFICATE') {
        const student_name    = document.getElementById('student_name').value.trim();
        const matricule       = document.getElementById('matricule').value.trim();
        const degree          = document.getElementById('degree').value.trim();
        const grade           = document.getElementById('grade').value.trim();
        const graduation_date = document.getElementById('graduation_date').value;
        if (!student_name || !matricule || !degree || !grade || !graduation_date) {
            showAlert('alert', 'Please fill in all required fields.', 'error'); return;
        }
        itemData = { ...itemData, student_name, matricule, degree, grade,
            graduation_date, institution_name: institutionName };

    } else if (selectedCategory === 'PHARMACEUTICAL') {
        const drug_name        = document.getElementById('drug_name').value.trim();
        const batch_number     = document.getElementById('batch_number').value.trim();
        const manufacturer     = document.getElementById('manufacturer').value.trim();
        const factory_location = document.getElementById('factory_location').value.trim();
        const production_date  = document.getElementById('production_date').value;
        const expiry_date      = document.getElementById('expiry_date').value;
        if (!drug_name || !batch_number || !manufacturer || !factory_location || !production_date || !expiry_date) {
            showAlert('alert', 'Please fill in all required fields.', 'error'); return;
        }
        itemData = { ...itemData, drug_name, batch_number, manufacturer,
            factory_location, production_date, expiry_date };

    } else if (selectedCategory === 'DOCUMENT') {
        const document_type     = document.getElementById('document_type').value;
        const owner_name        = document.getElementById('owner_name').value.trim();
        const issuing_authority = document.getElementById('issuing_authority').value.trim();
        const reference_number  = document.getElementById('reference_number').value.trim();
        const location          = document.getElementById('location').value.trim();
        const issue_date        = document.getElementById('doc_issue_date').value;
        if (!document_type || !owner_name || !issuing_authority || !reference_number || !location || !issue_date) {
            showAlert('alert', 'Please fill in all required fields.', 'error'); return;
        }
        itemData = { ...itemData, document_type, owner_name, issuing_authority,
            reference_number, location, issue_date };

    } else if (selectedCategory === 'BANKNOTE') {
        const currency      = document.getElementById('currency').value.trim();
        const denomination  = document.getElementById('denomination').value.trim();
        const serial_number = document.getElementById('banknote_serial').value.trim();
        const series        = document.getElementById('series').value.trim();
        const issue_date    = document.getElementById('banknote_issue_date').value;
        const issuing_bank  = document.getElementById('issuing_bank').value.trim();
        if (!currency || !denomination || !serial_number || !series || !issue_date || !issuing_bank) {
            showAlert('alert', 'Please fill in all required fields.', 'error'); return;
        }
        itemData = { ...itemData, currency, denomination, serial_number,
            series, issue_date, issuing_bank };
    }

    setLoading('submit-btn', true, 'Registering on blockchain...');
    hideAlert('alert');

    try {
        const data = await ItemsAPI.register(itemData);

        if (data && data.item) {
            document.getElementById('step-form').style.display    = 'none';
            document.getElementById('step-success').style.display = 'block';
            document.getElementById('success-details').innerHTML  = `
                <div class="detail-row">
                    <span class="detail-label">Serial number</span>
                    <span class="detail-value">${data.item.serial_number}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Blockchain hash</span>
                    <span class="detail-value hash-value">${formatHash(data.item.blockchain_hash)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Transaction</span>
                    <span class="detail-value hash-value">${formatHash(data.item.transaction_hash)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Category</span>
                    <span class="detail-value">${data.item.category}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Status</span>
                    <span class="detail-value">${data.item.status}</span>
                </div>
            `;
        }

    } catch (error) {
        const msg = error.data?.error   ||
                    error.data?.detail  ||
                    JSON.stringify(error.data) ||
                    'Registration failed. Please try again.';
        showAlert('alert', msg, 'error');
    } finally {
        setLoading('submit-btn', false, 'Register on blockchain');
    }
}

function registerAnother() {
    selectedCategory = null;
    document.getElementById('step-success').style.display  = 'none';
    document.getElementById('step-category').style.display = 'block';
}

// Init
loadInstitution();