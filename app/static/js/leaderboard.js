/**
 * leaderboard.js
 * - Global username filter across all leaderboards.
 * - Click-to-sort column headers (rank / username / numeric stat).
 * - Highlights the current user's rows.
 */

(function () {
    'use strict';

    const page = document.querySelector('.leaderboard-page');
    if (!page) return;

    const currentUsername = (page.dataset.currentUsername || '').toLowerCase();
    const filterEl        = document.getElementById('leaderboard-filter');
    const tables          = Array.from(document.querySelectorAll('.js-sortable-leaderboard'));

    /* ── Highlight current user on initial render ────────── */
    const highlightCurrentUser = () => {
        if (!currentUsername) return;

        tables.forEach((table) => {
            table.querySelectorAll('tbody tr[data-username]').forEach((tr) => {
                if (tr.dataset.username === currentUsername) {
                    tr.classList.add('is-current-user');
                }
            });
        });
    };

    /* ── Filter across all leaderboards ──────────────────── */
    const applyFilter = () => {
        const term = (filterEl.value || '').trim().toLowerCase();

        tables.forEach((table) => {
            const rows = table.querySelectorAll('tbody tr[data-username]');
            let visible = 0;
            rows.forEach((tr) => {
                const matches = !term || (tr.dataset.username || '').includes(term);
                tr.hidden = !matches;
                if (matches) visible += 1;
            });
            const noResultsRow = table.querySelector('.leaderboard-no-results-row');
            if (noResultsRow && rows.length > 0) {
                noResultsRow.hidden = visible !== 0;
            }
        });
    };

    if (filterEl) {
        filterEl.addEventListener('input', applyFilter);
    }

    /* ── Sortable column headers ─────────────────────────── */
    const sortValue = (tr, key, type) => {
        if (key === 'username') {
            return (tr.dataset.username || '').toLowerCase();
        }
        const raw = tr.dataset[key];
        if (type === 'number') {
            const n = parseFloat(raw);
            return Number.isNaN(n) ? 0 : n;
        }
        return (raw || '').toString().toLowerCase();
    };

    const sortTable = (table, key, type, direction) => {
        const tbody = table.querySelector('tbody');
        if (!tbody) return;

        const dataRows = Array.from(tbody.querySelectorAll('tr[data-username]'));
        const pinnedRows = Array.from(tbody.querySelectorAll('tr:not([data-username])'));

        const factor = direction === 'asc' ? 1 : -1;

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

    highlightCurrentUser();
}());
