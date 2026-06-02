// ─────────────────────────────────────────────
// Qentis — Register Page
// ─────────────────────────────────────────────

async function handleRegister() {
    const email            = document.getElementById('email').value.trim();
    const password         = document.getElementById('password').value;
    const password2        = document.getElementById('password2').value;
    const institution_name = document.getElementById('institution-name').value.trim();
    const institution_type = document.getElementById('institution-type').value;
    const country          = document.getElementById('country').value.trim();
    const city             = document.getElementById('city').value.trim();

    // Validation
    if (!email || !password || !password2 || !institution_name || !institution_type || !country || !city) {
        showAlert('alert', 'Please fill in all required fields.', 'error');
        return;
    }

    if (password !== password2) {
        showAlert('alert', 'Passwords do not match.', 'error');
        return;
    }

    if (password.length < 8) {
        showAlert('alert', 'Password must be at least 8 characters.', 'error');
        return;
    }

    setLoading('register-btn', true, 'Creating account...');
    hideAlert('alert');

    try {
        // Step 1 — Create user account
        const registerData = await AuthAPI.register(
            email,
            password,
            password2,
            'ISSUER'
        );

        if (!registerData || !registerData.tokens) {
            showAlert('alert', 'Registration failed. Please try again.', 'error');
            return;
        }

        // Step 2 — Submit institution application
        const applyRes = await fetch(`${API_BASE.INSTITUTION}/apply/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${registerData.tokens.access}`,
                'X-User-ID': registerData.user.id,
                'X-User-Role': 'ISSUER',
            },
            body: JSON.stringify({
                name: institution_name,
                institution_type: institution_type,
                country: country,
                city: city,
                contact_email: email,
            }),
        });

        const applyData = await applyRes.json();

        if (applyRes.ok) {
            // Save tokens so user is logged in
            Auth.setTokens(registerData.tokens.access, registerData.tokens.refresh);
            Auth.setUser(registerData.user);
            window.location.href = '/pending-approval.html';
        } else {
            showAlert('alert', applyData.error || 'Account created but institution application failed.', 'error');
        }

    } catch (error) {
        const msg = error.data?.email?.[0] ||
                    error.data?.error ||
                    error.data?.detail ||
                    'Registration failed. Please try again.';
        showAlert('alert', msg, 'error');
    } finally {
        setLoading('register-btn', false, 'Create account');
    }
}

document.addEventListener('keydown', e => {
    if (e.key === 'Enter') handleRegister();
});