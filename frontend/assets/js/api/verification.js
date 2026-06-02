// ─────────────────────────────────────────────
// Qentis — Verification Service API
// Base URL: http://localhost:8006/api/verify
// ─────────────────────────────────────────────

const VerificationAPI = {

    /**
     * Verify item by blockchain hash.
     * POST /api/verify/hash/
     */
    verifyByHash: async (itemHash) => {
        return await apiRequest(`${API_BASE.VERIFICATION}/hash/`, {
            method: 'POST',
            headers: headers.json(),
            body: JSON.stringify({ item_hash: itemHash }),
        });
    },

    /**
     * Verify item by serial number.
     * POST /api/verify/serial/
     */
    verifyBySerial: async (serialNumber) => {
        return await apiRequest(`${API_BASE.VERIFICATION}/serial/`, {
            method: 'POST',
            headers: headers.json(),
            body: JSON.stringify({ serial_number: serialNumber }),
        });
    },

    /**
     * Verify item by QR code data.
     * POST /api/verify/qr/
     */
    verifyByQR: async (qrData) => {
        return await apiRequest(`${API_BASE.VERIFICATION}/qr/`, {
            method: 'POST',
            headers: headers.json(),
            body: JSON.stringify({ qr_data: qrData }),
        });
    },

    /**
     * Verify item by digital signature.
     * POST /api/verify/signature/
     */
    verifyBySignature: async (file, itemHash) => {
        const fd = new FormData();
        fd.append('file', file);
        fd.append('item_hash', itemHash);
        return await apiRequest(`${API_BASE.VERIFICATION}/signature/`, {
            method: 'POST',
            headers: headers.authOnly(),
            body: fd,
        });
    },

    /**
     * Verify banknote by OCR photo.
     * POST /api/verify/ocr/
     */
    verifyByOCR: async (image) => {
        const fd = new FormData();
        fd.append('image', image);
        return await apiRequest(`${API_BASE.VERIFICATION}/ocr/`, {
            method: 'POST',
            body: fd,
        });
    },

    /**
     * Verify document by watermark.
     * POST /api/verify/watermark/
     */
    verifyByWatermark: async (image) => {
        const fd = new FormData();
        fd.append('image', image);
        return await apiRequest(`${API_BASE.VERIFICATION}/watermark/`, {
            method: 'POST',
            body: fd,
        });
    },

    /**
     * Get verification history for an item.
     * GET /api/verify/history/{item_id}/
     */
    getHistory: async (itemId) => {
        return await apiRequest(`${API_BASE.VERIFICATION}/history/${itemId}/`, {
            method: 'GET',
            headers: headers.json(),
        });
    },

    /**
     * Report an item as suspicious.
     * POST /api/verify/report/
     */
    reportItem: async (itemId, reason = '') => {
        return await apiRequest(`${API_BASE.VERIFICATION}/report/`, {
            method: 'POST',
            headers: headers.json(),
            body: JSON.stringify({ item_id: itemId, reason }),
        });
    },
};