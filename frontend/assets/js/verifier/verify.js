/* ── State ── */
let activeMethod   = 'qr';
let cameraStream   = null;
let scanLoop       = null;
let sigFile        = null;
let ocrFile        = null;
let wmFile         = null;
let selectedItem   = null;
let activeCategory = null;

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
    document.getElementById('step-categories').style.display = 'none';
    document.getElementById('step-verify').style.display     = 'block';
    document.getElementById('selected-name').textContent     = CATEGORY_LABELS[category] || category;
    document.getElementById('selected-meta').textContent     = CATEGORY_DESCS[category]  || '';
    document.getElementById('result-area').innerHTML         = '';
    selectMethod('qr');
}

function goBack() {
    selectedItem   = null;
    activeCategory = null;
    stopCamera();
    document.getElementById('step-verify').style.display     = 'none';
    document.getElementById('step-categories').style.display = 'block';
    document.getElementById('result-area').innerHTML         = '';
}

/* ── Method switcher ── */
function selectMethod(method) {
    activeMethod = method;
    stopCamera();
    document.querySelectorAll('.method-card').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('.verify-panel').forEach(p => p.classList.remove('active'));
    document.getElementById('m-'     + method).classList.add('active');
    document.getElementById('panel-' + method).classList.add('active');
    document.getElementById('result-area').innerHTML = '';
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

function verifyQRFromFile(input) {
    const file = input.files[0];
    if (!file) return;
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
            if (code) sendVerifyQR(code.data);
            else showResult('unverifiable', 'No QR code detected in this image. Please try a clearer photo.');
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

async function sendVerifyQR(qrData) {
    showVerifying();
    try {
        const res = await fetch(`${API_BASE.VERIFICATION}/qr/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ qr_data: qrData }),
        });
        handleVerifyResponse(await res.json(), res.ok);
    } catch (e) { showResult('unverifiable', 'Connection error. Please try again.'); }
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
    const details  = data.item_details || {};
    const el       = document.getElementById('result-area');
    el.innerHTML = `
        <div class="q-result-authentic">
            <div class="result-header">
                <div class="result-icon result-icon--authentic">✓</div>
                <div>
                    <div class="q-result-title">AUTHENTIC</div>
                    <div class="result-verified-label">Verified on blockchain</div>
                </div>
            </div>
            <div class="result-details">
                ${details.category    ? `<div class="result-detail"><div class="result-detail-label">CATEGORY</div><div class="result-detail-value">${details.category}</div></div>` : ''}
                ${details.issuer      ? `<div class="result-detail"><div class="result-detail-label">ISSUED BY</div><div class="result-detail-value">${details.issuer}</div></div>` : ''}
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