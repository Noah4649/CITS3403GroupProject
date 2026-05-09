/**
 * password_reset.js
 * Client-side behaviour for the password reset page.
 * Vanilla JS — this page does not extend base.html so main.js is not available.
 *
 * The reset route has no POST handler yet, so we keep e.preventDefault() and
 * show a success state to give the user feedback without a server round-trip.
 */

(function () {
    'use strict';

    const form      = document.getElementById('reset-form');
    const emailEl   = document.getElementById('email');
    const submitBtn = form.querySelector('[type="submit"]');

    const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    function setError(inputEl, message) {
        inputEl.classList.add('is-invalid');
        const fb = inputEl.nextElementSibling;
        if (fb && fb.classList.contains('invalid-feedback')) {
            fb.textContent = message;
        }
    }

    function clearError(inputEl) {
        inputEl.classList.remove('is-invalid');
    }

    emailEl.addEventListener('blur', function () {
        if (!this.value.trim()) {
            setError(this, 'Email is required.');
        } else if (!EMAIL_RE.test(this.value.trim())) {
            setError(this, 'Enter a valid email address.');
        } else {
            clearError(this);
        }
    });

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        clearError(emailEl);

        if (!emailEl.value.trim()) {
            setError(emailEl, 'Email is required.');
            return;
        }

        if (!EMAIL_RE.test(emailEl.value.trim())) {
            setError(emailEl, 'Enter a valid email address.');
            return;
        }

        submitBtn.disabled = true;
        submitBtn.innerHTML =
            '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Sending…';

        setTimeout(function () {
            submitBtn.innerHTML = '✓ Reset link sent';
            submitBtn.classList.replace('btn-primary', 'btn-success');
            emailEl.value = '';

            setTimeout(function () {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Send Reset Link';
                submitBtn.classList.replace('btn-success', 'btn-primary');
            }, 3000);
        }, 800);
    });
}());
