/**
 * login.js
 * Client-side behaviour for the login page.
 * Vanilla JS — this page does not extend base.html so main.js is not available.
 */

(function () {
    'use strict';

    const form     = document.getElementById('login-form');
    const emailEl  = document.getElementById('email');
    const passEl   = document.getElementById('password');
    const showPass = document.getElementById('show-password');
    const submitBtn = form.querySelector('[type="submit"]');

    /* ── Show / hide password ─────────────────────────────── */
    showPass.addEventListener('change', function () {
        passEl.type = this.checked ? 'text' : 'password';
    });

    /* ── Helpers ──────────────────────────────────────────── */
    const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

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
    emailEl.addEventListener('blur', function () {
        if (!this.value.trim()) {
            setError(this, 'Email is required.');
        } else if (!EMAIL_RE.test(this.value.trim())) {
            setError(this, 'Enter a valid email address.');
        } else {
            clearError(this);
        }
    });

    passEl.addEventListener('blur', function () {
        if (!this.value) {
            setError(this, 'Password is required.');
        } else {
            clearError(this);
        }
    });

    /* ── Submit validation ────────────────────────────────── */
    form.addEventListener('submit', function (e) {
        let valid = true;

        clearError(emailEl);
        clearError(passEl);

        if (!emailEl.value.trim()) {
            setError(emailEl, 'Email is required.');
            valid = false;
        } else if (!EMAIL_RE.test(emailEl.value.trim())) {
            setError(emailEl, 'Enter a valid email address.');
            valid = false;
        }

        if (!passEl.value) {
            setError(passEl, 'Password is required.');
            valid = false;
        }

        if (!valid) {
            e.preventDefault();
            return;
        }

        submitBtn.disabled = true;
        submitBtn.innerHTML =
            '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Logging in…';
    });
}());
