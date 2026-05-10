/**
 * workout_active.js
 * Live timer and set/exercise tracking for an in-progress workout.
 * Extracted from workout_active.html.
 */

(function () {
    'use strict';

    const timerEl          = document.getElementById('timer');
    const startBtn         = document.getElementById('timer-start');
    const pauseBtn         = document.getElementById('timer-pause');
    const resetBtn         = document.getElementById('timer-reset');
    const durationInput    = document.getElementById('duration_mins');
    const completedCountEl = document.getElementById('completed-count');
    const exerciseList     = document.getElementById('exercise-list');
    const finishForm       = document.getElementById('finish-form');

    let elapsedSeconds = 0;
    let intervalId     = null;

    const pad = (n) => n.toString().padStart(2, '0');

    const formatTime = (totalSeconds) => {
        const h = Math.floor(totalSeconds / 3600);
        const m = Math.floor((totalSeconds % 3600) / 60);
        const s = totalSeconds % 60;
        return h > 0
            ? pad(h) + ':' + pad(m) + ':' + pad(s)
            : pad(m) + ':' + pad(s);
    };

    const render = () => {
        timerEl.textContent = formatTime(elapsedSeconds);
        const minutes = Math.max(0, Math.floor(elapsedSeconds / 60));
        if (durationInput && document.activeElement !== durationInput) {
            durationInput.value = minutes;
        }
    };

    const tick = () => {
        elapsedSeconds += 1;
        render();
    };

    const start = () => {
        if (intervalId !== null) return;
        intervalId = setInterval(tick, 1000);
        startBtn.disabled = true;
        pauseBtn.disabled = false;
    };

    const pause = () => {
        if (intervalId === null) return;
        clearInterval(intervalId);
        intervalId = null;
        startBtn.disabled = false;
        pauseBtn.disabled = true;
        startBtn.textContent = 'Resume';
    };

    const reset = () => {
        clearInterval(intervalId);
        intervalId = null;
        elapsedSeconds = 0;
        startBtn.disabled = false;
        pauseBtn.disabled = true;
        startBtn.textContent = 'Start';
        render();
    };

    startBtn.addEventListener('click', start);
    pauseBtn.addEventListener('click', pause);
    resetBtn.addEventListener('click', reset);

    /* ── Exercise / set completion tracking ──────────────── */
    const updateCompletedCount = () => {
        if (!exerciseList || !completedCountEl) return;
        const cards = exerciseList.querySelectorAll('.exercise-card');
        let done = 0;
        cards.forEach((card) => {
            const totalSets = parseInt(card.dataset.sets, 10) || 0;
            if (totalSets > 0) {
                const pills     = card.querySelectorAll('.set-pill');
                const doneCount = card.querySelectorAll('.set-pill.is-done').length;
                if (pills.length > 0 && doneCount === pills.length) {
                    card.classList.add('is-complete');
                    done += 1;
                } else {
                    card.classList.remove('is-complete');
                }
            } else {
                if (card.classList.contains('is-complete')) done += 1;
            }
        });
        completedCountEl.textContent = done;
    };

    if (exerciseList) {
        exerciseList.addEventListener('click', (e) => {
            const target = e.target;

            if (target.classList.contains('set-pill')) {
                target.classList.toggle('is-done');
                updateCompletedCount();
                return;
            }

            if (target.classList.contains('mark-done-btn')) {
                const card = target.closest('.exercise-card');
                if (card) {
                    const nowDone = card.classList.toggle('is-complete');
                    target.textContent = nowDone ? 'Completed' : 'Mark Complete';
                }
                updateCompletedCount();
            }
        });
    }

    /* ── Finish form validation ───────────────────────────── */
    finishForm.addEventListener('submit', (e) => {
        const duration = parseInt(durationInput.value, 10);
        const calories = parseInt(document.getElementById('calories_burned').value, 10);
        if (Number.isNaN(duration) || duration < 0) {
            e.preventDefault();
            alert('Enter a valid duration in minutes.');
            return;
        }
        if (Number.isNaN(calories) || calories < 0) {
            e.preventDefault();
            alert('Enter a valid calories number.');
            return;
        }
        if (intervalId !== null) {
            clearInterval(intervalId);
            intervalId = null;
        }
    });

    render();
    updateCompletedCount();
}());
