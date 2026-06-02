// ─────────────────────────────────────────────
// Qentis — Item Registration Service API
// Base URL: http://localhost:8003/api/items
// ─────────────────────────────────────────────

const ItemsAPI = {

    /**
     * Register a new item.
     * POST /api/items/register/
     */
    register: async (itemData) => {
        return await apiRequest(`${API_BASE.ITEMS}/register/`, {
            method: 'POST',
            headers: headers.auth(),
            body: JSON.stringify(itemData),
        });
    },

    /**
     * Get all items for the logged-in issuer.
     * GET /api/items/my-items/
     */
    myItems: async () => {
        return await apiRequest(`${API_BASE.ITEMS}/my-items/`, {
            method: 'GET',
            headers: headers.auth(),
        });
    },

    /**
     * Get a single item by ID.
     * GET /api/items/{item_id}/
     */
    getItem: async (itemId) => {
        return await apiRequest(`${API_BASE.ITEMS}/${itemId}/`, {
            method: 'GET',
            headers: headers.auth(),
        });
    },

    /**
     * Revoke an item.
     * PUT /api/items/{item_id}/revoke/
     */
    revokeItem: async (itemId, reason) => {
        return await apiRequest(`${API_BASE.ITEMS}/${itemId}/revoke/`, {
            method: 'PUT',
            headers: headers.auth(),
            body: JSON.stringify({ reason }),
        });
    },

    /**
     * Get item by serial number.
     * GET /api/items/serial/{serial_number}/
     */
    getBySerial: async (serialNumber) => {
        return await apiRequest(`${API_BASE.ITEMS}/serial/${serialNumber}/`, {
            method: 'GET',
            headers: headers.json(),
        });
    },
};