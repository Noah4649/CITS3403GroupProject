document.addEventListener('DOMContentLoaded', function () {
    const toggleBtn = document.getElementById('toggle-submissions');
    const container = document.getElementById('submissions-container');

    if (!toggleBtn || !container) return;

    toggleBtn.addEventListener('click', function () {
        const isVisible = container.style.display !== 'none';

        container.style.display = isVisible ? 'none' : 'block';
        toggleBtn.textContent = isVisible ? 'Show Previous Submissions' : 'Hide Previous Submissions';
        toggleBtn.setAttribute('aria-expanded', !isVisible);
    });
});