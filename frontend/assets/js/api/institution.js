// ─────────────────────────────────────────────
// Qentis — Institution Service API
// Base URL: http://localhost:8002/api/institution
// ─────────────────────────────────────────────

const InstitutionAPI = {

    /**
     * Apply for institution registration.
     * POST /api/institution/apply/
     */
    apply: async (institutionData) => {
        return await apiRequest(`${API_BASE.INSTITUTION}/apply/`, {
            method: 'POST',
            headers: headers.auth(),
            body: JSON.stringify(institutionData),
        });
    },

    /**
     * Get current institution status for logged-in issuer.
     * GET /api/institution/status/
     */
    getStatus: async () => {
        return await apiRequest(`${API_BASE.INSTITUTION}/status/`, {
            method: 'GET',
            headers: headers.auth(),
        });
    },

    /**
     * Get all institutions (Admin only).
     * GET /api/institution/all/
     */
    getAll: async () => {
        return await apiRequest(`${API_BASE.INSTITUTION}/all/`, {
            method: 'GET',
            headers: headers.auth(),
        });
    },

    /**
     * Get pending institution applications (Admin only).
     * GET /api/institution/pending/
     */
    getPending: async () => {
        return await apiRequest(`${API_BASE.INSTITUTION}/pending/`, {
            method: 'GET',
            headers: headers.auth(),
        });
    },

    /**
     * Approve an institution (Admin only).
     * PUT /api/institution/{institution_id}/approve/
     */
    approve: async (institutionId, notes = '') => {
        return await apiRequest(`${API_BASE.INSTITUTION}/${institutionId}/approve/`, {
            method: 'PUT',
            headers: headers.auth(),
            body: JSON.stringify({ notes }),
        });
    },

    /**
     * Reject an institution (Admin only).
     * PUT /api/institution/{institution_id}/reject/
     */
    reject: async (institutionId, reason) => {
        return await apiRequest(`${API_BASE.INSTITUTION}/${institutionId}/reject/`, {
            method: 'PUT',
            headers: headers.auth(),
            body: JSON.stringify({ reason }),
        });
    },

    /**
     * Get institution by ID.
     * GET /api/institution/{institution_id}/
     */
    getById: async (institutionId) => {
        return await apiRequest(`${API_BASE.INSTITUTION}/${institutionId}/`, {
            method: 'GET',
            headers: headers.auth(),
        });
    },
};