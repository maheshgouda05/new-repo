/**
 * ANALYTIX CLUB - PASSWORD RESET CONTROLLER
 * Handles Supabase email recovery tokens, session extraction, and password updates.
 */

const PasswordReset = {
  recoveryToken: null,

  init() {
    this.extractRecoveryToken();
    this.bindForm();
  },

  extractRecoveryToken() {
    const alertBox = document.getElementById('reset-alert');
    const form = document.getElementById('reset-form');

    // 1. Check URL Hash: #access_token=...&type=recovery
    let token = null;
    if (window.location.hash) {
      const hash = window.location.hash.substring(1);
      const params = new URLSearchParams(hash);
      token = params.get('access_token');
    }

    // 2. Check URL Query Parameters: ?token=... or ?access_token=...
    if (!token && window.location.search) {
      const queryParams = new URLSearchParams(window.location.search);
      token = queryParams.get('token') || queryParams.get('access_token');
    }

    // 3. Check existing authenticated session if user is logged in
    if (!token) {
      token = API.getToken();
    }

    if (!token) {
      if (alertBox) {
        alertBox.innerHTML = `
          <strong>Invalid or Expired Link</strong><br>
          This password recovery link is missing, expired, or invalid.
          <div style="margin-top: 10px;">
            <a href="forgot-password.html" class="btn btn-secondary btn-sm" style="display: inline-block;">Request New Reset Link</a>
          </div>
        `;
        alertBox.style.display = 'block';
      }
      if (form) form.style.display = 'none';
      return null;
    }

    this.recoveryToken = token;
    return token;
  },

  bindForm() {
    const form = document.getElementById('reset-form');
    if (!form) return;

    const alertBox = document.getElementById('reset-alert');
    const successBox = document.getElementById('reset-success');
    const submitBtn = document.getElementById('btn-reset');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      alertBox.style.display = 'none';
      successBox.style.display = 'none';

      const newPassword = document.getElementById('new_password').value;
      const confirmPassword = document.getElementById('confirm_password').value;

      if (!newPassword || newPassword.length < 6) {
        alertBox.textContent = 'Password must be at least 6 characters long.';
        alertBox.style.display = 'flex';
        return;
      }

      if (newPassword !== confirmPassword) {
        alertBox.textContent = 'Passwords do not match. Please verify and try again.';
        alertBox.style.display = 'flex';
        return;
      }

      if (!this.recoveryToken) {
        alertBox.textContent = 'Recovery session not found or expired. Please request a new password reset link.';
        alertBox.style.display = 'flex';
        return;
      }

      submitBtn.disabled = true;
      submitBtn.querySelector('span:first-child').textContent = 'Updating password...';

      try {
        const res = await Auth.resetPassword(this.recoveryToken, newPassword);
        successBox.textContent = res.message || 'Password updated successfully! Redirecting to login...';
        successBox.style.display = 'flex';
        form.style.display = 'none';

        // Clear existing session and redirect to login
        API.clearAuth();
        setTimeout(() => {
          window.location.href = 'login.html';
        }, 2000);
      } catch (err) {
        alertBox.textContent = err.message || 'Failed to update password. Recovery link may have expired.';
        alertBox.style.display = 'flex';
        submitBtn.disabled = false;
        submitBtn.querySelector('span:first-child').textContent = 'Update Password';
      }
    });
  }
};

window.PasswordReset = PasswordReset;

