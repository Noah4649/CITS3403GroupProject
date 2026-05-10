/**
 * start_workout.js
 * Dynamic exercise row management for the Start Workout form.
 * Extracted from start_workout.html.
 */

(function () {
    'use strict';

    const list      = document.getElementById('exercise-list');
    const template  = document.getElementById('exercise-row-template');
    const addBtn    = document.getElementById('add-exercise');
    const form      = document.getElementById('start-workout-form');
    const emptyMsg  = document.getElementById('no-exercises-msg');

    const renumber = () => {
        const rows = list.querySelectorAll('.exercise-row');
        rows.forEach((row, i) => {
            const label = row.querySelector('.exercise-index');
            if (label) label.textContent = 'Exercise ' + (i + 1);
        });
        emptyMsg.hidden = rows.length !== 0;
    };

    const addRow = () => {
        const clone = template.content.firstElementChild.cloneNode(true);
        list.appendChild(clone);
        renumber();
        const firstInput = clone.querySelector('input[name="exercise_name[]"]');
        if (firstInput) firstInput.focus();
    };

    addBtn.addEventListener('click', addRow);

    list.addEventListener('click', (e) => {
        if (e.target.classList.contains('remove-exercise')) {
            const row = e.target.closest('.exercise-row');
            if (row) row.remove();
            renumber();
        }
    });

    form.addEventListener('submit', (e) => {
        const rows = list.querySelectorAll('.exercise-row');
        if (rows.length === 0) {
            e.preventDefault();
            emptyMsg.hidden = false;
            emptyMsg.textContent = 'Add at least one exercise before starting.';
            return;
        }
        const hasName = Array.from(rows).some((r) => {
            const input = r.querySelector('input[name="exercise_name[]"]');
            return input && input.value.trim() !== '';
        });
        if (!hasName) {
            e.preventDefault();
            alert('At least one exercise needs a name.');
        }
    });

    addRow();
}());
