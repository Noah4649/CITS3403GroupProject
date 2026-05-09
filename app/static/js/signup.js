/**
 * signup.js
 * Client-side behaviour for the sign-up page.
 * Vanilla JS — this page does not extend base.html so main.js is not available.
 */

(function () {
    'use strict';

    const form         = document.getElementById('signup-form');
    const usernameEl   = document.getElementById('username');
    const emailEl      = document.getElementById('email');
    const passEl       = document.getElementById('password');
    const retypeEl     = document.getElementById('retype-password');
    const showPass     = document.getElementById('show-password');
    const submitBtn    = form.querySelector('[type="submit"]');

    /* ── Show / hide password ─────────────────────────────── */
    showPass.addEventListener('change', function () {
        const type = this.checked ? 'text' : 'password';
        passEl.type  = type;
        retypeEl.type = type;
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
    usernameEl.addEventListener('blur', function () {
        if (!this.value.trim()) {
            setError(this, 'Username is required.');
        } else {
            clearError(this);
        }
    });

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
        } else if (this.value.length < 8) {
            setError(this, 'Password must be at least 8 characters.');
        } else {
            clearError(this);
        }
    });

    retypeEl.addEventListener('blur', function () {
        if (!this.value) {
            setError(this, 'Please confirm your password.');
        } else if (this.value !== passEl.value) {
            setError(this, 'Passwords do not match.');
        } else {
            clearError(this);
        }
    });

    /* ── Submit validation ────────────────────────────────── */
    form.addEventListener('submit', function (e) {
        let valid = true;

        [usernameEl, emailEl, passEl, retypeEl].forEach(clearError);

        if (!usernameEl.value.trim()) {
            setError(usernameEl, 'Username is required.');
            valid = false;
        }

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
        } else if (passEl.value.length < 8) {
            setError(passEl, 'Password must be at least 8 characters.');
            valid = false;
        }

        if (!retypeEl.value) {
            setError(retypeEl, 'Please confirm your password.');
            valid = false;
        } else if (retypeEl.value !== passEl.value) {
            setError(retypeEl, 'Passwords do not match.');
            valid = false;
        }

        if (!valid) {
            e.preventDefault();
            return;
        }

        submitBtn.disabled = true;
        submitBtn.innerHTML =
            '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Creating account…';
    });
}());
