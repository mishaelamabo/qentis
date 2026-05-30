// ─────────────────────────────────────────────
// Qentis — Register Item Page
// ─────────────────────────────────────────────

let selectedCategory    = null;
let institutionId       = null;
let institutionName     = null;
let fingerprintCaptured = false;

const INSTITUTION_CATEGORY_MAP = {
    'UNIVERSITY':   'CERTIFICATE',
    'HOSPITAL':     'PHARMACEUTICAL',
    'MANUFACTURER': 'PHARMACEUTICAL',
    'BANK':         'BANKNOTE',
    'NOTARY':       'DOCUMENT',
};

async function loadInstitution() {
    try {
        const data = await InstitutionAPI.getStatus();
        if (data && data.id) {
            institutionId   = data.id;
            institutionName = data.name;

            const allowedCategory = INSTITUTION_CATEGORY_MAP[data.institution_type];
            if (allowedCategory) {
                document.querySelectorAll('.category-card').forEach(card => {
                    card.style.display = 'none';
                });
                const allowed = document.querySelector(
                    `.category-card[onclick="selectCategory('${allowedCategory}')"]`
                );
                if (allowed) {
                    allowed.style.display  = 'block';
                    allowed.style.margin   = '0 auto';
                    allowed.style.maxWidth = '240px';
                }
            }
        } else {
            showAlert('alert', 'Could not load institution info. Please contact support.', 'error');
        }
    } catch (e) {
        showAlert('alert', 'Could not load institution info. Please contact support.', 'error');
    }
}

function selectCategory(category) {
    selectedCategory    = category;
    fingerprintCaptured = false;
    document.querySelectorAll('.category-fields').forEach(f => f.style.display = 'none');
    document.getElementById(`fields-${category}`).style.display = 'block';
    document.getElementById('form-title').textContent = `Step 2 — ${category.charAt(0) + category.slice(1).toLowerCase()} details`;
    document.getElementById('step-category').style.display = 'none';
    document.getElementById('step-form').style.display     = 'block';
    hideAlert('alert');
}

function goBackToCategory() {
    selectedCategory    = null;
    fingerprintCaptured = false;
    document.getElementById('step-form').style.display     = 'none';
    document.getElementById('step-category').style.display = 'block';
    hideAlert('alert');
}

/* ── Fingerprint capture via WebAuthn ── */
async function captureFingerprint() {
    const statusEl  = document.getElementById('fingerprint-status');
    const btn       = document.getElementById('fingerprint-btn');
    const hashInput = document.getElementById('fingerprint_hash');

    btn.disabled         = true;
    btn.textContent      = 'Waiting for fingerprint...';
    statusEl.className   = 'fingerprint-status fingerprint-status--waiting';
    statusEl.textContent = 'Place finger on sensor...';

    try {
        const challenge = crypto.getRandomValues(new Uint8Array(32));
        const userId    = crypto.getRandomValues(new Uint8Array(16));

        const ownerName = (
            document.getElementById('owner_given_names')?.value ||
            document.getElementById('owner_name')?.value ||
            'document-owner'
        ).trim();

        const credential = await navigator.credentials.create({
            publicKey: {
                challenge,
                rp: { name: 'Qentis', id: 'localhost' },
                user: {
                    id:          userId,
                    name:        ownerName,
                    displayName: ownerName,
                },
                pubKeyCredParams: [
                    { alg: -7,   type: 'public-key' },
                    { alg: -257, type: 'public-key' },
                ],
                authenticatorSelection: {
                    authenticatorAttachment: 'platform',
                    userVerification:        'required',
                    residentKey:             'discouraged',
                },
                timeout:     60000,
                attestation: 'none',
            }
        });

        // Hash credential ID → fingerprint_hash
        const credIdBytes = new Uint8Array(credential.rawId);
        const hashBuffer  = await crypto.subtle.digest('SHA-256', credIdBytes);
        const hashArray   = Array.from(new Uint8Array(hashBuffer));
        const hashHex     = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

        // Base64 encode raw credential ID → credential_id
        const credIdB64 = btoa(String.fromCharCode(...credIdBytes));

        hashInput.value = hashHex;

        // Store credential_id in hidden field
        let credInput = document.getElementById('credential_id');
        if (!credInput) {
            credInput      = document.createElement('input');
            credInput.type = 'hidden';
            credInput.id   = 'credential_id';
            document.body.appendChild(credInput);
        }
        credInput.value = credIdB64;

        fingerprintCaptured  = true;
        statusEl.className   = 'fingerprint-status fingerprint-status--captured';
        statusEl.textContent = '✓ Fingerprint captured successfully';
        btn.textContent      = '✓ Captured — click to re-capture';
        btn.disabled         = false;

    } catch (e) {
        console.error('WebAuthn error:', e.name, e.message);
        fingerprintCaptured  = false;
        hashInput.value      = '';
        statusEl.className   = 'fingerprint-status fingerprint-status--error';
        statusEl.textContent = `Capture failed: ${e.message || e.name}. Please try again.`;
        btn.textContent      = '👆 Capture fingerprint';
        btn.disabled         = false;
    }
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
        const owner_surname     = document.getElementById('owner_surname').value.trim();
        const owner_given_names = document.getElementById('owner_given_names').value.trim();
        const issuing_authority = document.getElementById('issuing_authority').value.trim();
        const reference_number  = document.getElementById('reference_number').value.trim();
        const card_number       = document.getElementById('card_number').value.trim();
        const location          = document.getElementById('location').value.trim();
        const issue_date        = document.getElementById('doc_issue_date').value;
        const date_of_birth     = document.getElementById('date_of_birth').value;
        const date_of_expiry    = document.getElementById('date_of_expiry').value;
        const sex               = document.getElementById('sex').value;
        const father_name       = document.getElementById('father_name').value.trim();
        const mother_name       = document.getElementById('mother_name').value.trim();
        const place_of_birth    = document.getElementById('place_of_birth').value.trim();
        const occupation        = document.getElementById('occupation').value.trim();
        const height            = document.getElementById('height').value.trim();
        const mrz_line1         = document.getElementById('mrz_line1').value.trim();
        const mrz_line2         = document.getElementById('mrz_line2').value.trim();
        const mrz_line3         = document.getElementById('mrz_line3').value.trim();
        const fingerprint_hash  = document.getElementById('fingerprint_hash').value;
        const credential_id     = document.getElementById('credential_id')?.value || '';

        // Combined full name
        const owner_name = `${owner_surname} ${owner_given_names}`.trim();

        if (!document_type || !owner_surname || !owner_given_names || !issuing_authority ||
            !reference_number || !card_number || !location || !issue_date ||
            !date_of_birth || !date_of_expiry || !sex || !father_name ||
            !mother_name || !place_of_birth) {
            showAlert('alert', 'Please fill in all required fields.', 'error'); return;
        }
        if (!fingerprintCaptured || !fingerprint_hash) {
            showAlert('alert', 'Please capture the fingerprint before registering.', 'error'); return;
        }

        itemData = {
            ...itemData,
            document_type, owner_name, owner_surname, owner_given_names,
            issuing_authority, reference_number, card_number, location,
            issue_date, date_of_birth, date_of_expiry, sex,
            father_name, mother_name, place_of_birth, occupation, height,
            mrz_line1, mrz_line2, mrz_line3,
            fingerprint_hash, credential_id,
        };

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

    setLoading('submit-btn', true, 'Registering...');
    hideAlert('alert');

    try {
        const data = await ItemsAPI.register(itemData);

        if (data && data.item) {
            document.getElementById('step-form').style.display    = 'none';
            document.getElementById('step-success').style.display = 'block';
            document.getElementById('success-serial').textContent   = data.item.serial_number || 'Pending approval';
            document.getElementById('success-hash').textContent     = formatHash(data.item.blockchain_hash) || '—';
            document.getElementById('success-tx').textContent       = formatHash(data.item.transaction_hash) || '—';
            document.getElementById('success-category').textContent = data.item.category;
            document.getElementById('success-status').textContent   = data.item.status;
        }

    } catch (error) {
        const msg = error.data?.error  ||
                    error.data?.detail ||
                    JSON.stringify(error.data) ||
                    'Registration failed. Please try again.';
        showAlert('alert', msg, 'error');
    } finally {
        setLoading('submit-btn', false, 'Register on blockchain');
    }
}

function registerAnother() {
    selectedCategory    = null;
    fingerprintCaptured = false;
    document.getElementById('step-success').style.display  = 'none';
    document.getElementById('step-category').style.display = 'block';
}

// Init
loadInstitution();