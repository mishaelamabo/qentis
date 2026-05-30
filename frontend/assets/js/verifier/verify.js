/* ── State ── */
let activeMethod          = 'qr';
let cameraStream          = null;
let scanLoop              = null;
let sigFile               = null;
let ocrFile               = null;
let wmFile                = null;
let selectedItem          = null;
let activeCategory        = null;
let verifyFingerprintHash = null;

const CATEGORY_LABELS = {
    Drug:        'Pharmaceutical',
    Certificate: 'School Certificate',
    Document:    'Official Document',
    Banknote:    'Money',
};

const CATEGORY_DESCS = {
    Drug:        'Drug & medicine verification',
    Certificate: 'Diploma & degree verification',
    Document:    'Official identity document verification',
    Banknote:    'Banknote & currency verification',
};

/* ── Category picker ── */
function selectCategory(category) {
    activeCategory = category;
    selectedItem   = { category, name: CATEGORY_LABELS[category] };

    document.getElementById('step-categories').style.display     = 'none';
    document.getElementById('result-area') && (document.getElementById('result-area').innerHTML = '');

    if (category === 'Document') {
        // Document — show biometric verification flow
        document.getElementById('step-document-verify').style.display = 'block';
        document.getElementById('step-verify').style.display          = 'none';
        document.getElementById('doc-result-area').innerHTML          = '';
        resetDocumentForm();
    } else {
        // Other categories — show standard verification
        document.getElementById('step-verify').style.display          = 'block';
        document.getElementById('step-document-verify').style.display = 'none';
        document.getElementById('selected-name').textContent          = CATEGORY_LABELS[category] || category;
        document.getElementById('selected-meta').textContent          = CATEGORY_DESCS[category]  || '';
        selectMethod('qr');
    }
}

function resetDocumentForm() {
    document.getElementById('doc-reference').value        = '';
    document.getElementById('doc-card-number').value      = '';
    document.getElementById('verify-fingerprint-hash').value = '';
    verifyFingerprintHash = null;
    const statusEl = document.getElementById('verify-fingerprint-status');
    statusEl.className   = 'fingerprint-status fingerprint-status--waiting';
    statusEl.textContent = 'Waiting for fingerprint...';
    const btn = document.getElementById('verify-fingerprint-btn');
    btn.textContent = '👆 Scan fingerprint';
    btn.disabled    = false;
}

function goBack() {
    selectedItem          = null;
    activeCategory        = null;
    verifyFingerprintHash = null;
    stopCamera();
    document.getElementById('step-verify').style.display          = 'none';
    document.getElementById('step-document-verify').style.display = 'none';
    document.getElementById('step-categories').style.display      = 'block';
    if (document.getElementById('result-area'))
        document.getElementById('result-area').innerHTML = '';
    if (document.getElementById('doc-result-area'))
        document.getElementById('doc-result-area').innerHTML = '';
}

/* ── Method switcher ── */
function selectMethod(method) {
    activeMethod = method;
    stopCamera();
    document.querySelectorAll('.method-card').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('.verify-panel').forEach(p => p.classList.remove('active'));
    document.getElementById('m-'     + method).classList.add('active');
    document.getElementById('panel-' + method).classList.add('active');
    if (document.getElementById('result-area'))
        document.getElementById('result-area').innerHTML = '';
}

/* ── Document fingerprint capture ── */
async function captureVerifyFingerprint(credentialIdB64) {
    const statusEl = document.getElementById('verify-fingerprint-status');
    const btn      = document.getElementById('verify-fingerprint-btn');

    btn.disabled         = true;
    btn.textContent      = 'Waiting for fingerprint...';
    statusEl.className   = 'fingerprint-status fingerprint-status--waiting';
    statusEl.textContent = 'Place finger on sensor...';

    try {
        // Decode stored credential ID from base64
        const credIdBytes = Uint8Array.from(atob(credentialIdB64), c => c.charCodeAt(0));

        const challenge = crypto.getRandomValues(new Uint8Array(32));

        // Use GET — authenticates with existing credential
        const assertion = await navigator.credentials.get({
            publicKey: {
                challenge,
                rpId:             'localhost',
                allowCredentials: [{
                    type: 'public-key',
                    id:   credIdBytes,
                }],
                userVerification: 'required',
                timeout:          60000,
            }
        });

        // Hash the credential ID same way as registration
        const credId     = new Uint8Array(assertion.rawId);
        const hashBuffer = await crypto.subtle.digest('SHA-256', credId);
        const hashArray  = Array.from(new Uint8Array(hashBuffer));
        const hashHex    = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

        verifyFingerprintHash = hashHex;
        document.getElementById('verify-fingerprint-hash').value = hashHex;

        statusEl.className   = 'fingerprint-status fingerprint-status--captured';
        statusEl.textContent = '✓ Fingerprint verified successfully';
        btn.textContent      = '✓ Verified — click to re-scan';
        btn.disabled         = false;

    } catch (e) {
        console.error('WebAuthn error:', e.name, e.message);
        verifyFingerprintHash = null;
        statusEl.className   = 'fingerprint-status fingerprint-status--error';
        statusEl.textContent = `Scan failed: ${e.message || e.name}. Please try again.`;
        btn.textContent      = '👆 Scan fingerprint';
        btn.disabled         = false;
    }
}

/* ── Document verification ── */
async function verifyDocument() {
    const reference  = document.getElementById('doc-reference').value.trim();
    const cardNumber = document.getElementById('doc-card-number').value.trim();

    if (!reference) {
        showDocResult('error', 'Please enter the Identifiant Unique.'); return;
    }
    if (!cardNumber) {
        showDocResult('error', 'Please enter the Card Number.'); return;
    }

    setLoading('doc-verify-btn', true, 'Looking up document...');

    try {
        // Step 1 — fetch item to get credential ID
        const lookupRes = await fetch(
            `${API_BASE.ITEMS}/reference/${reference}/`,
            { headers: { 'Content-Type': 'application/json' } }
        );

        if (!lookupRes.ok) {
            showDocResult('not-authentic', 'Identifiant Unique not found in our records.');
            return;
        }

        const itemData     = await lookupRes.json();
        const docDetail    = itemData.document_detail;
        const credentialId = docDetail?.credential_id;

        if (!credentialId) {
            showDocResult('unverifiable', 'No biometric data registered for this document.');
            return;
        }

        setLoading('doc-verify-btn', true, 'Scan your fingerprint...');

        // Step 2 — capture fingerprint using stored credential
        await captureVerifyFingerprint(credentialId);

        if (!verifyFingerprintHash) {
            showDocResult('error', 'Fingerprint scan failed. Please try again.');
            return;
        }

        setLoading('doc-verify-btn', true, 'Verifying...');
        showDocVerifying();

        // Step 3 — send full verification request
        const res = await fetch(`${API_BASE.VERIFICATION}/document/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                reference_number: reference,
                card_number:      cardNumber,
                fingerprint_hash: verifyFingerprintHash,
            }),
        });

        const data = await res.json();
        handleDocVerifyResponse(data, res.ok);

    } catch (e) {
        showDocResult('unverifiable', 'Connection error. Please try again.');
    } finally {
        setLoading('doc-verify-btn', false, 'Verify Document');
    }
}

function showDocVerifying() {
    const el = document.getElementById('doc-result-area');
    el.innerHTML = `
        <div class="q-card verifying-card">
            <div class="q-spinner verifying-spinner"></div>
            <div class="verifying-text">Querying blockchain...</div>
        </div>`;
    el.scrollIntoView({ behavior: 'smooth' });
}

function handleDocVerifyResponse(data, ok) {
    if (!ok) { showDocResult('unverifiable', data.detail || data.error || 'Verification failed.'); return; }
    const result = data.result?.toUpperCase();
    if (result === 'AUTHENTIC') showDocResultAuthentic(data);
    else if (result === 'NOT_AUTHENTIC') showDocResult('not-authentic', data.message || 'Document could not be verified.');
    else showDocResult('unverifiable', data.message || 'Could not verify this document.');
}

function showDocResultAuthentic(data) {
    const details = data.item_details || {};
    const el      = document.getElementById('doc-result-area');
    el.innerHTML  = `
        <div class="q-result-authentic">
            <div class="result-header">
                <div class="result-icon result-icon--authentic">✓</div>
                <div>
                    <div class="q-result-title">AUTHENTIC</div>
                    <div class="result-verified-label">Document &amp; fingerprint verified on blockchain</div>
                </div>
            </div>
            <div class="result-details">
                ${details.category      ? `<div class="result-detail"><div class="result-detail-label">CATEGORY</div><div class="result-detail-value">${details.category}</div></div>` : ''}
                ${details.issuer        ? `<div class="result-detail"><div class="result-detail-label">ISSUED BY</div><div class="result-detail-value">${details.issuer}</div></div>` : ''}
                ${details.registered_at ? `<div class="result-detail"><div class="result-detail-label">REGISTERED</div><div class="result-detail-value">${formatDateTime(details.registered_at * 1000)}</div></div>` : ''}
            </div>
            <div class="result-actions">
                <span class="q-blockchain-badge">⛓ On-chain verified</span>
                <button onclick="reportItem('${data.item_id}')" class="btn-report">Report as suspicious</button>
            </div>
        </div>`;
    el.scrollIntoView({ behavior: 'smooth' });
}

function showDocResult(type, message) {
    const config = {
        'not-authentic': { cls: 'q-result-not-authentic', icon: '✗', title: 'NOT AUTHENTIC' },
        'unverifiable':  { cls: 'q-result-unverifiable',  icon: '?', title: 'UNVERIFIABLE'  },
        'error':         { cls: 'q-result-unverifiable',  icon: '!', title: 'Error'          },
    };
    const c  = config[type] || config['unverifiable'];
    const el = document.getElementById('doc-result-area');
    el.innerHTML = `
        <div class="${c.cls}">
            <div class="result-header">
                <div class="result-icon">${c.icon}</div>
                <div>
                    <div class="q-result-title">${c.title}</div>
                    <div class="result-message">${message}</div>
                </div>
            </div>
        </div>`;
    el.scrollIntoView({ behavior: 'smooth' });
}

/* ── QR camera ── */
async function startCamera() {
    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
        const video  = document.getElementById('camera-feed');
        video.srcObject = cameraStream;
        document.getElementById('start-cam-btn').style.display = 'none';
        document.getElementById('stop-cam-btn').style.display  = 'inline-block';
        scanLoop = requestAnimationFrame(scanFrame);
    } catch (e) {
        showResult('unverifiable', 'Camera access denied. Please upload a QR image instead.');
    }
}

function stopCamera() {
    if (cameraStream) { cameraStream.getTracks().forEach(t => t.stop()); cameraStream = null; }
    if (scanLoop)     { cancelAnimationFrame(scanLoop); scanLoop = null; }
    const startBtn = document.getElementById('start-cam-btn');
    const stopBtn  = document.getElementById('stop-cam-btn');
    if (startBtn) startBtn.style.display = 'inline-block';
    if (stopBtn)  stopBtn.style.display  = 'none';
}

function scanFrame() {
    const video  = document.getElementById('camera-feed');
    const canvas = document.getElementById('qr-canvas');
    if (!video.videoWidth) { scanLoop = requestAnimationFrame(scanFrame); return; }
    canvas.width  = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx  = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    const img  = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const code = jsQR(img.data, img.width, img.height);
    if (code) { stopCamera(); sendVerifyQR(code.data); }
    else { scanLoop = requestAnimationFrame(scanFrame); }
}

/* ── QR file upload ── */
function showQRPreview(input) {
    const file = input.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = e => {
        document.getElementById('qr-preview').src              = e.target.result;
        document.getElementById('qr-preview').style.display    = 'block';
        document.getElementById('qr-upload-btn').style.display = 'inline-block';
    };
    reader.readAsDataURL(file);
}

function submitQRFromFile() {
    const input = document.getElementById('qr-file');
    const file  = input.files[0];
    if (!file) return;
    setLoading('qr-upload-btn', true, 'Scanning...');
    const reader = new FileReader();
    reader.onload = e => {
        const img  = new Image();
        img.onload = () => {
            const canvas = document.createElement('canvas');
            canvas.width  = img.width;
            canvas.height = img.height;
            const ctx  = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            const data = ctx.getImageData(0, 0, img.width, img.height);
            const code = jsQR(data.data, data.width, data.height);
            setLoading('qr-upload-btn', false, 'Scan QR code');
            if (code) sendVerifyQR(code.data);
            else showResult('unverifiable', 'No QR code detected. Please try a clearer photo.');
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

async function sendVerifyQR(qrData) {
    showVerifying();
    try {
        let serial = null;
        let hash   = null;
        try {
            const url = new URL(qrData);
            serial = url.searchParams.get('serial');
            hash   = url.searchParams.get('hash');
        } catch (e) {
            hash = qrData;
        }

        let res;
        if (serial) {
            res = await fetch(`${API_BASE.VERIFICATION}/serial/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ serial_number: serial }),
            });
        } else {
            res = await fetch(`${API_BASE.VERIFICATION}/qr/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ qr_data: hash }),
            });
        }
        handleVerifyResponse(await res.json(), res.ok);
    } catch (e) {
        showResult('unverifiable', 'Connection error. Please try again.');
    }
}

/* ── Serial number ── */
async function verifyBySerial() {
    const serial = document.getElementById('serial-input').value.trim();
    if (!serial) { showResult('error', 'Please enter a serial number.'); return; }
    setLoading('serial-btn', true, 'Verifying...');
    showVerifying();
    try {
        const res = await fetch(`${API_BASE.VERIFICATION}/serial/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ serial_number: serial }),
        });
        handleVerifyResponse(await res.json(), res.ok);
    } catch (e) { showResult('unverifiable', 'Connection error.'); }
    finally { setLoading('serial-btn', false, 'Verify'); }
}

/* ── Signature ── */
function verifySignature(input) {
    sigFile = input.files[0];
    if (sigFile) {
        document.getElementById('sig-filename').textContent = '📎 ' + sigFile.name;
        document.getElementById('sig-btn').style.display   = 'inline-block';
    }
}

async function submitSignatureVerify() {
    if (!sigFile) return;
    setLoading('sig-btn', true, 'Verifying...');
    showVerifying();
    const fd = new FormData();
    fd.append('file', sigFile);
    try {
        const res = await fetch(`${API_BASE.VERIFICATION}/signature/`, { method: 'POST', body: fd });
        handleVerifyResponse(await res.json(), res.ok);
    } catch (e) { showResult('unverifiable', 'Connection error.'); }
    finally { setLoading('sig-btn', false, 'Verify signature'); }
}

/* ── OCR ── */
function showOCRPreview(input) {
    ocrFile = input.files[0];
    if (ocrFile) {
        const reader = new FileReader();
        reader.onload = e => {
            document.getElementById('ocr-preview').src           = e.target.result;
            document.getElementById('ocr-preview').style.display = 'block';
            document.getElementById('ocr-btn').style.display     = 'inline-block';
        };
        reader.readAsDataURL(ocrFile);
    }
}

async function submitOCRVerify() {
    if (!ocrFile) return;
    setLoading('ocr-btn', true, 'Scanning...');
    showVerifying();
    const fd = new FormData();
    fd.append('image', ocrFile);
    try {
        const res = await fetch(`${API_BASE.VERIFICATION}/ocr/`, { method: 'POST', body: fd });
        handleVerifyResponse(await res.json(), res.ok);
    } catch (e) { showResult('unverifiable', 'Connection error.'); }
    finally { setLoading('ocr-btn', false, 'Scan & verify'); }
}

/* ── Watermark ── */
function showWMPreview(input) {
    wmFile = input.files[0];
    if (wmFile) {
        const reader = new FileReader();
        reader.onload = e => {
            document.getElementById('wm-preview').src           = e.target.result;
            document.getElementById('wm-preview').style.display = 'block';
            document.getElementById('wm-btn').style.display     = 'inline-block';
        };
        reader.readAsDataURL(wmFile);
    }
}

async function submitWatermarkVerify() {
    if (!wmFile) return;
    setLoading('wm-btn', true, 'Detecting...');
    showVerifying();
    const fd = new FormData();
    fd.append('image', wmFile);
    try {
        const res = await fetch(`${API_BASE.VERIFICATION}/watermark/`, { method: 'POST', body: fd });
        handleVerifyResponse(await res.json(), res.ok);
    } catch (e) { showResult('unverifiable', 'Connection error.'); }
    finally { setLoading('wm-btn', false, 'Detect & verify'); }
}

/* ── Result rendering ── */
function handleVerifyResponse(data, ok) {
    if (!ok) { showResult('unverifiable', data.detail || 'Verification failed.'); return; }
    const result = data.result?.toUpperCase();
    if (result === 'AUTHENTIC') showResultAuthentic(data);
    else if (result === 'NOT_AUTHENTIC') showResult('not-authentic', data.message || 'No matching record found.');
    else showResult('unverifiable', data.message || 'Could not verify this item.');
}

function showVerifying() {
    const el = document.getElementById('result-area');
    el.innerHTML = `
        <div class="q-card verifying-card">
            <div class="q-spinner verifying-spinner"></div>
            <div class="verifying-text">Querying blockchain...</div>
        </div>`;
    el.scrollIntoView({ behavior: 'smooth' });
}

function showResultAuthentic(data) {
    const details = data.item_details || {};
    const el      = document.getElementById('result-area');
    el.innerHTML  = `
        <div class="q-result-authentic">
            <div class="result-header">
                <div class="result-icon result-icon--authentic">✓</div>
                <div>
                    <div class="q-result-title">AUTHENTIC</div>
                    <div class="result-verified-label">Verified on blockchain</div>
                </div>
            </div>
            <div class="result-details">
                ${details.category      ? `<div class="result-detail"><div class="result-detail-label">CATEGORY</div><div class="result-detail-value">${details.category}</div></div>` : ''}
                ${details.issuer        ? `<div class="result-detail"><div class="result-detail-label">ISSUED BY</div><div class="result-detail-value">${details.issuer}</div></div>` : ''}
                ${details.registered_at ? `<div class="result-detail"><div class="result-detail-label">REGISTERED</div><div class="result-detail-value">${formatDateTime(details.registered_at * 1000)}</div></div>` : ''}
            </div>
            <div class="result-actions">
                <span class="q-blockchain-badge">⛓ On-chain verified</span>
                <button onclick="reportItem('${data.item_id}')" class="btn-report">Report as suspicious</button>
            </div>
        </div>`;
    el.scrollIntoView({ behavior: 'smooth' });
}

function showResult(type, message) {
    const config = {
        'not-authentic': { cls: 'q-result-not-authentic', icon: '✗', title: 'NOT AUTHENTIC' },
        'unverifiable':  { cls: 'q-result-unverifiable',  icon: '?', title: 'UNVERIFIABLE'  },
        'error':         { cls: 'q-result-unverifiable',  icon: '!', title: 'Error'          },
    };
    const c  = config[type] || config['unverifiable'];
    const el = document.getElementById('result-area');
    el.innerHTML = `
        <div class="${c.cls}">
            <div class="result-header">
                <div class="result-icon">${c.icon}</div>
                <div>
                    <div class="q-result-title">${c.title}</div>
                    <div class="result-message">${message}</div>
                </div>
            </div>
        </div>`;
    el.scrollIntoView({ behavior: 'smooth' });
}

async function reportItem(itemId) {
    if (!confirm('Report this item as suspicious?')) return;
    await fetch(`${API_BASE.VERIFICATION}/report/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: itemId }),
    });
    alert('Report submitted. Thank you.');
}

function setLoading(buttonId, loading, loadingText = 'Loading...') {
    const btn = document.getElementById(buttonId);
    if (!btn) return;
    btn.disabled = loading;
    if (loading) {
        btn.dataset.originalText = btn.textContent;
        btn.textContent = loadingText;
    } else {
        btn.textContent = btn.dataset.originalText || loadingText;
    }
}

function formatDateTime(ts) {
    if (!ts) return '—';
    return new Date(ts).toLocaleString('en-GB', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}