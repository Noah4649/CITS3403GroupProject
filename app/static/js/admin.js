/**
 * admin.js
 * - Global text filter across the Users, Reports and Feedback tables.
 * - Click-to-sort column headers (string / number / date).
 * - Mirrors the leaderboard.js sort API for consistency.
 */

(function () {
    'use strict';

    const page = document.querySelector('.admin-page');
    if (!page) return;

    const filterEl = document.getElementById('admin-filter');
    const tables   = Array.from(document.querySelectorAll('.js-sortable-table'));

    /* ── Global filter across every table ────────────────── */
    const applyFilter = () => {
        const term = (filterEl.value || '').trim().toLowerCase();

        tables.forEach((table) => {
            const rows = table.querySelectorAll('tbody tr[data-row]');
            let visible = 0;

            rows.forEach((tr) => {
                const haystack = (tr.dataset.search || tr.textContent || '').toLowerCase();
                const matches = !term || haystack.includes(term);
                tr.hidden = !matches;
                if (matches) visible += 1;
            });

            const noResultsRow = table.querySelector('.admin-no-results-row');
            if (noResultsRow && rows.length > 0) {
                noResultsRow.hidden = visible !== 0;
            }
        });
    };

    if (filterEl) {
        filterEl.addEventListener('input', applyFilter);
    }

    /* ── Sortable headers ────────────────────────────────── */
    const sortValue = (tr, key, type) => {
        const raw = tr.dataset[key];
        if (type === 'number') {
            const n = parseFloat(raw);
            return Number.isNaN(n) ? 0 : n;
        }
        if (type === 'date') {
            const t = Date.parse(raw);
            return Number.isNaN(t) ? 0 : t;
        }
        return (raw || '').toString().toLowerCase();
    };

    const sortTable = (table, key, type, direction) => {
        const tbody = table.querySelector('tbody');
        if (!tbody) return;

        const dataRows   = Array.from(tbody.querySelectorAll('tr[data-row]'));
        const pinnedRows = Array.from(tbody.querySelectorAll('tr:not([data-row])'));
        const factor     = direction === 'asc' ? 1 : -1;

        dataRows.sort((a, b) => {
            const va = sortValue(a, key, type);
            const vb = sortValue(b, key, type);
            if (va < vb) return -1 * factor;
            if (va > vb) return  1 * factor;
            return 0;
        });

        dataRows.forEach((tr) => tbody.appendChild(tr));
        pinnedRows.forEach((tr) => tbody.appendChild(tr));
    };

    const setHeaderState = (table, activeTh, direction) => {
        table.querySelectorAll('.js-sort').forEach((th) => {
            th.classList.remove('sort-asc', 'sort-desc');
            th.setAttribute('aria-sort', 'none');
        });
        activeTh.classList.add(direction === 'asc' ? 'sort-asc' : 'sort-desc');
        activeTh.setAttribute('aria-sort', direction === 'asc' ? 'ascending' : 'descending');
    };

    tables.forEach((table) => {
        table.querySelectorAll('.js-sort').forEach((th) => {
            th.setAttribute('tabindex', '0');
            th.addEventListener('click', () => {
                const key  = th.dataset.sortKey;
                const type = th.dataset.sortType || 'string';
                const currentlyAsc = th.classList.contains('sort-asc');
                const direction = currentlyAsc ? 'desc' : 'asc';
                sortTable(table, key, type, direction);
                setHeaderState(table, th, direction);
            });
            th.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    th.click();
                }
            });
        });
    });
}());
