/**
 * settings.js
 * Client-side validation for the change-password form.
 * Mirrors signup.js password rules (required + min 8 chars + match).
 */

(function () {
    'use strict';

    const form       = document.getElementById('settings-form');
    if (!form) return;

    const currentEl  = document.getElementById('current_password');
    const newEl      = document.getElementById('new_password');
    const confirmEl  = document.getElementById('confirm_password');
    const showPass   = document.getElementById('show-password');
    const submitBtn  = form.querySelector('[type="submit"]');

    /* ── Show / hide password ─────────────────────────────── */
    if (showPass) {
        showPass.addEventListener('change', function () {
            const type = this.checked ? 'text' : 'password';
            currentEl.type = type;
            newEl.type     = type;
            confirmEl.type = type;
        });
    }

    /* ── Helpers ──────────────────────────────────────────── */
    function setError(inputEl, message) {
        inputEl.classList.add('is-invalid');
        inputEl.classList.remove('is-valid');
        const fb = inputEl.nextElementSibling;
        if (fb && fb.classList.contains('invalid-feedback')) {
            fb.textContent = message;
        }
    }

    function clearError(inputEl) {
        inputEl.classList.remove('is-invalid');
    }

    /* ── Inline validation on blur ────────────────────────── */
    currentEl.addEventListener('blur', function () {
        if (!this.value) {
            setError(this, 'Current password is required.');
        } else {
            clearError(this);
        }
    });

    newEl.addEventListener('blur', function () {
        if (!this.value) {
            setError(this, 'New password is required.');
        } else if (this.value.length < 8) {
            setError(this, 'Password must be at least 8 characters.');
        } else if (currentEl.value && this.value === currentEl.value) {
            setError(this, 'New password must be different from current.');
        } else {
            clearError(this);
        }
    });

    confirmEl.addEventListener('blur', function () {
        if (!this.value) {
            setError(this, 'Please confirm your new password.');
        } else if (this.value !== newEl.value) {
            setError(this, 'Passwords do not match.');
        } else {
            clearError(this);
        }
    });

    /* ── Submit validation ────────────────────────────────── */
    form.addEventListener('submit', function (e) {
        let valid = true;

        [currentEl, newEl, confirmEl].forEach(clearError);

        if (!currentEl.value) {
            setError(currentEl, 'Current password is required.');
            valid = false;
        }

        if (!newEl.value) {
            setError(newEl, 'New password is required.');
            valid = false;
        } else if (newEl.value.length < 8) {
            setError(newEl, 'Password must be at least 8 characters.');
            valid = false;
        } else if (currentEl.value && newEl.value === currentEl.value) {
            setError(newEl, 'New password must be different from current.');
            valid = false;
        }

        if (!confirmEl.value) {
            setError(confirmEl, 'Please confirm your new password.');
            valid = false;
        } else if (confirmEl.value !== newEl.value) {
            setError(confirmEl, 'Passwords do not match.');
            valid = false;
        }

        if (!valid) {
            e.preventDefault();
            return;
        }

        submitBtn.disabled = true;
        submitBtn.innerHTML =
            '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Updating…';
    });
}());
