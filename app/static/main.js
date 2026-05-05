/**
 * main.js
 * -------
 * Shared utilities for the FitTrack web application.
 * Loaded on every page. Depends on: jQuery, Bootstrap 5.
 */


/* ============================================================
   1. AJAX HELPERS
   Wrapper functions around jQuery $.ajax so every other JS
   file makes requests the same consistent way.
   ============================================================ */

/**
 * Send a GET request to a Flask route.
 * @param {string}   url       - e.g. '/api/user/profile'
 * @param {function} onSuccess - called with the parsed JSON data on success
 * @param {function} [onError] - optional, called with the xhr object on failure
 */
function apiGet(url, onSuccess, onError) {
    $.ajax({
        url: url,
        type: 'GET',
        dataType: 'json',
        success: function (data) {
            onSuccess(data);
        },
        error: function (xhr) {
            handleAjaxError(xhr);
            if (onError) onError(xhr);
        }
    });
}

/**
 * Send a POST request with a JSON body to a Flask route.
 * @param {string}   url       - e.g. '/api/workout/log'
 * @param {object}   payload   - JS object to send as JSON
 * @param {function} onSuccess - called with the parsed JSON data on success
 * @param {function} [onError] - optional, called with the xhr object on failure
 */
function apiPost(url, payload, onSuccess, onError) {
    $.ajax({
        url: url,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(payload),
        dataType: 'json',
        success: function (data) {
            onSuccess(data);
        },
        error: function (xhr) {
            handleAjaxError(xhr);
            if (onError) onError(xhr);
        }
    });
}

/**
 * Send a PUT request (used for editing/updating existing data).
 */
function apiPut(url, payload, onSuccess, onError) {
    $.ajax({
        url: url,
        type: 'PUT',
        contentType: 'application/json',
        data: JSON.stringify(payload),
        dataType: 'json',
        success: function (data) {
            onSuccess(data);
        },
        error: function (xhr) {
            handleAjaxError(xhr);
            if (onError) onError(xhr);
        }
    });
}

/**
 * Send a DELETE request (used for removing workouts, meals, etc.).
 */
function apiDelete(url, onSuccess, onError) {
    $.ajax({
        url: url,
        type: 'DELETE',
        dataType: 'json',
        success: function (data) {
            onSuccess(data);
        },
        error: function (xhr) {
            handleAjaxError(xhr);
            if (onError) onError(xhr);
        }
    });
}

/**
 * Central error handler for all AJAX failures.
 * Redirects to login on 401 (session expired / not logged in).
 */
function handleAjaxError(xhr) {
    if (xhr.status === 401) {
        showToast('Please log in to continue.', 'warning');
        setTimeout(function () {
            window.location.href = '/login';
        }, 1500);
        return;
    }

    var message = 'Something went wrong. Please try again.';
    try {
        var resp = JSON.parse(xhr.responseText);
        if (resp.error)   message = resp.error;
        if (resp.message) message = resp.message;
    } catch (e) { /* response wasn't JSON, use default */ }

    showToast(message, 'danger');
}


/* ============================================================
   2. TOAST NOTIFICATIONS
   Call showToast() from any JS file to display feedback.
   ============================================================ */

/**
 * Show a Bootstrap 5 toast notification at the bottom-right of the screen.
 * @param {string} message - Text to display
 * @param {string} type    - 'success' | 'danger' | 'warning' | 'info'
 */
function showToast(message, type) {
    type = type || 'info';

    if ($('#toast-container').length === 0) {
        $('body').append(
            '<div id="toast-container" class="toast-container position-fixed bottom-0 end-0 p-3" style="z-index:9999;"></div>'
        );
    }

    var id        = 'toast-' + Date.now();
    var bgClass   = 'bg-' + type;
    var textClass = (type === 'warning' || type === 'info') ? 'text-dark' : 'text-white';

    var html = '<div id="' + id + '" class="toast align-items-center ' + bgClass + ' ' + textClass + ' border-0" role="alert" aria-atomic="true" data-bs-delay="3500">' +
                   '<div class="d-flex">' +
                       '<div class="toast-body fw-semibold">' + message + '</div>' +
                       '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>' +
                   '</div>' +
               '</div>';

    $('#toast-container').append(html);

    var toastEl = document.getElementById(id);
    var bsToast = new bootstrap.Toast(toastEl);
    bsToast.show();

    toastEl.addEventListener('hidden.bs.toast', function () {
        $(toastEl).remove();
    });
}


/* ============================================================
   3. NAVBAR — ACTIVE LINK HIGHLIGHTING
   Marks the correct nav link as active based on the current URL.
   ============================================================ */

function setActiveNavLink() {
    var currentPath = window.location.pathname;

    $('.navbar-nav .nav-link, .sidebar .nav-link').each(function () {
        var linkPath = $(this).attr('href');
        if (!linkPath) return;

        if (linkPath === '/' && currentPath === '/') {
            $(this).addClass('active');
        } else if (linkPath !== '/' && currentPath.startsWith(linkPath)) {
            $(this).addClass('active');
        }
    });
}


/* ============================================================
   4. LOGOUT
   Posts to Flask's logout route, then redirects to login.
   ============================================================ */

function logout() {
    window.location.href = '/logout';
}


/* ============================================================
   5. FORM HELPERS
   Shared across login, signup, profile and settings pages.
   ============================================================ */

/**
 * Show a Bootstrap validation error message under a form field.
 * @param {string} fieldSelector - e.g. '#username-input'
 * @param {string} message       - Error text to show
 */
function showFieldError(fieldSelector, message) {
    $(fieldSelector).addClass('is-invalid');
    $(fieldSelector).siblings('.invalid-feedback').text(message).show();
}

/**
 * Clear all validation errors inside a form.
 * @param {string} formSelector - e.g. '#login-form'
 */
function clearFormErrors(formSelector) {
    $(formSelector + ' .is-invalid').removeClass('is-invalid');
    $(formSelector + ' .invalid-feedback').hide();
}

/**
 * Disable a submit button and show a loading spinner.
 * Prevents the user from double-clicking and sending two requests.
 * @param {string} btnSelector - e.g. '#submit-btn'
 */
function setButtonLoading(btnSelector) {
    var $btn = $(btnSelector);
    $btn.data('original-text', $btn.html())
        .prop('disabled', true)
        .html('<span class="spinner-border spinner-border-sm me-2" role="status"></span>Loading...');
}

/**
 * Restore a button to its original label after a request finishes.
 * @param {string} btnSelector - e.g. '#submit-btn'
 */
function resetButton(btnSelector) {
    var $btn = $(btnSelector);
    $btn.prop('disabled', false).html($btn.data('original-text'));
}


/* ============================================================
   6. DATE & NUMBER UTILITIES
   Used on the dashboard, history, and nutrition pages.
   ============================================================ */

/**
 * Format a date string from Flask/SQLite into a readable AU date.
 * e.g. "2025-04-20" → "Sun 20 Apr 2025"
 */
function formatDate(dateInput) {
    var d = new Date(dateInput);
    return d.toLocaleDateString('en-AU', {
        weekday: 'short', day: 'numeric', month: 'short', year: 'numeric'
    });
}

/**
 * Format a duration given in seconds into a readable string.
 * e.g. 3725 → "1h 2m"
 */
function formatDuration(totalSeconds) {
    var h = Math.floor(totalSeconds / 3600);
    var m = Math.floor((totalSeconds % 3600) / 60);
    var s = totalSeconds % 60;
    if (h > 0) return h + 'h ' + m + 'm';
    if (m > 0) return m + 'm ' + s + 's';
    return s + 's';
}


/* ============================================================
   7. DOCUMENT READY
   Runs once when the page has fully loaded.
   ============================================================ */

$(document).ready(function () {

    // Highlight the current page's nav link
    setActiveNavLink();

    // Wire up logout to any .logout-btn element on the page.
    // Event delegation via $(document).on() means this works even
    // if the button is inside a Bootstrap dropdown rendered after load.
    $(document).on('click', '.logout-btn', function (e) {
        e.preventDefault();
        logout();
    });

    // Initialise Bootstrap tooltips for any [data-bs-toggle="tooltip"] elements
    $('[data-bs-toggle="tooltip"]').each(function () {
        new bootstrap.Tooltip(this);
    });

    // Auto-hide Flask flash message alerts after 4 seconds
    setTimeout(function () {
        $('.alert-dismissible').fadeOut(600, function () {
            $(this).remove();
        });
    }, 4000);

});