/**
 * history.js
 * Client-side filter, sort, and delete-confirm modal for the workout history page.
 */

(function () {
    'use strict';

    const list        = document.getElementById('workout-list');
    const filterEl    = document.getElementById('history-filter');
    const sortEl      = document.getElementById('history-sort');
    const noResultsEl = document.getElementById('history-no-results');
    const modalEl     = document.getElementById('deleteWorkoutModal');

    if (!list) return;

    const cards = Array.from(list.querySelectorAll('.workout-item-card'));

    /* ── Filter ───────────────────────────────────────────── */
    const applyFilter = () => {
        const term = (filterEl.value || '').trim().toLowerCase();
        let visibleCount = 0;

        cards.forEach((card) => {
            const title = card.dataset.title || '';
            const matches = !term || title.includes(term);
            card.hidden = !matches;
            if (matches) visibleCount += 1;
        });

        if (noResultsEl) noResultsEl.hidden = visibleCount !== 0;
    };

    /* ── Sort ─────────────────────────────────────────────── */
    const numericAttr = (el, name) => {
        const n = parseFloat(el.dataset[name]);
        return Number.isNaN(n) ? 0 : n;
    };

    const sorters = {
        'date-desc':     (a, b) => (a.dataset.date < b.dataset.date ? 1 : -1),
        'date-asc':      (a, b) => (a.dataset.date > b.dataset.date ? 1 : -1),
        'duration-desc': (a, b) => numericAttr(b, 'duration') - numericAttr(a, 'duration'),
        'calories-desc': (a, b) => numericAttr(b, 'calories') - numericAttr(a, 'calories'),
        'title-asc':     (a, b) => (a.dataset.title > b.dataset.title ? 1 : -1)
    };

    const applySort = () => {
        const key = sortEl.value;
        const sorter = sorters[key];
        if (!sorter) return;

        const sorted = cards.slice().sort(sorter);
        sorted.forEach((card) => list.appendChild(card));
    };

    if (filterEl) {
        filterEl.addEventListener('input', applyFilter);
    }
    if (sortEl) {
        sortEl.addEventListener('change', applySort);
    }

    /* ── Delete confirm modal ─────────────────────────────── */
    if (modalEl) {
        const titleEl   = modalEl.querySelector('#delete-workout-title');
        const confirmEl = modalEl.querySelector('#delete-workout-confirm');

        modalEl.addEventListener('show.bs.modal', (event) => {
            const trigger = event.relatedTarget;
            if (!trigger) return;

            const url   = trigger.getAttribute('data-delete-url');
            const title = trigger.getAttribute('data-workout-title');

            if (confirmEl && url) confirmEl.setAttribute('href', url);
            if (titleEl && title) titleEl.textContent = '"' + title + '"';
        });
    }
}());
