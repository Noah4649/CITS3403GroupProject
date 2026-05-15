/**
 * profile.js
 * ----------
 * Handles AJAX profile editing via the Edit Profile modal.
 */

document.addEventListener('DOMContentLoaded', function () {

    const saveBtn = document.getElementById('save-profile-btn');
    if (!saveBtn) return;

    saveBtn.addEventListener('click', function () {

        // Gather form values
        const username = document.getElementById('edit-username').value.trim();
        const bio = document.getElementById('edit-bio').value.trim();
        const weight = document.getElementById('edit-weight').value.trim();
        const height = document.getElementById('edit-height').value.trim();
        const goal = document.getElementById('edit-goal').value.trim();
        const dailyCalorieGoal = document.getElementById('edit-daily-calorie-goal').value.trim();

        // Clear previous messages
        const errorBox = document.getElementById('edit-profile-error');
        const successBox = document.getElementById('edit-profile-success');
        errorBox.style.display = 'none';
        successBox.style.display = 'none';

        // Basic client-side validation
        if (!username) {
            errorBox.textContent = 'Username cannot be empty.';
            errorBox.style.display = 'block';
            return;
        }

        // Disable button while request is in flight
        saveBtn.disabled = true;
        saveBtn.textContent = 'Saving...';

        // Send AJAX request
        fetch('/api/edit-profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username, bio, weight, height, goal,
                daily_calorie_goal: dailyCalorieGoal
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show success message
                successBox.textContent = data.message;
                successBox.style.display = 'block';

                // Update displayed values on the page without reloading
                if (username) {
                    document.querySelectorAll('.profile-username').forEach(el => el.textContent = username);
                }
                if (weight) {
                    const weightEl = document.getElementById('profile-weight');
                    if (weightEl) weightEl.textContent = weight + ' kg';
                }
                if (height) {
                    const heightEl = document.getElementById('profile-height');
                    if (heightEl) heightEl.textContent = height + ' cm';
                }
                if (goal) {
                    const goalEl = document.getElementById('profile-goal');
                    if (goalEl) goalEl.textContent = goal;
                }
                if (bio) {
                    const bioEl = document.getElementById('profile-bio');
                    if (bioEl) bioEl.textContent = bio;
                }

                // Close modal after 1.5 seconds
                setTimeout(() => {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('editProfileModal'));
                    if (modal) modal.hide();
                    successBox.style.display = 'none';
                }, 1500);

            } else {
                errorBox.textContent = data.error || 'Something went wrong.';
                errorBox.style.display = 'block';
            }
        })
        .catch(() => {
            errorBox.textContent = 'Network error. Please try again.';
            errorBox.style.display = 'block';
        })
        .finally(() => {
            saveBtn.disabled = false;
            saveBtn.textContent = 'Save Changes';
        });
    });
});