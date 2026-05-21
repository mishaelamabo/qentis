// ─────────────────────────────────────────────
// Qentis — Account Page
// ─────────────────────────────────────────────

Auth.guard('ISSUER');

async function loadProfile() {
    try {
        const user = Auth.getUser();
        if (user) {
            document.getElementById('profile-email').textContent = user.email || '—';
            document.getElementById('profile-role').textContent  = user.role  || '—';
        }

        const data = await InstitutionAPI.getStatus();
        if (data && data.institution) {
            document.getElementById('profile-institution').textContent = data.institution.name   || '—';
            document.getElementById('profile-status').textContent      = data.institution.status || '—';
        }

        document.getElementById('profile-loading').style.display = 'none';
        document.getElementById('profile-content').style.display = 'block';

    } catch (e) {
        document.getElementById('profile-loading').style.display = 'none';
        document.getElementById('profile-content').style.display = 'block';
    }
}

async function handleChangePassword() {
    const old_password        = document.getElementById('old-password').value;
    const new_password        = document.getElementById('new-password').value;
    const new_password2       = document.getElementById('new-password2').value;

    if (!old_password || !new_password || !new_password2) {
        showAlert('password-alert', 'Please fill in all fields.', 'error');
        return;
    }

    if (new_password !== new_password2) {
        showAlert('password-alert', 'New passwords do not match.', 'error');
        return;
    }

    if (new_password.length < 8) {
        showAlert('password-alert', 'Password must be at least 8 characters.', 'error');
        return;
    }

    setLoading('change-password-btn', true, 'Updating...');
    hideAlert('password-alert');

    try {
        await AuthAPI.changePassword(old_password, new_password, new_password2);
        showAlert('password-alert', 'Password updated successfully.', 'success');
        document.getElementById('old-password').value  = '';
        document.getElementById('new-password').value  = '';
        document.getElementById('new-password2').value = '';
    } catch (e) {
        const msg = e.data?.old_password?.[0] ||
                    e.data?.error ||
                    'Failed to update password.';
        showAlert('password-alert', msg, 'error');
    } finally {
        setLoading('change-password-btn', false, 'Update password');
    }
}

// Init
loadProfile();