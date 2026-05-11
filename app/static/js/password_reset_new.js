// FITTRACK-PASSWORD-RESET-NEW-JS: Runs the password reset page JavaScript after the HTML has fully loaded.
document.addEventListener('DOMContentLoaded', function () {
    // FITTRACK-PASSWORD-RESET-NEW-JS: Finds the checkbox used to show or hide the password fields.
    const showPasswordsCheckbox = document.querySelector('#show-passwords');

    // FITTRACK-PASSWORD-RESET-NEW-JS: Finds both password inputs on password_reset_new.html.
    const passwordFields = document.querySelectorAll('#password, #confirm_password');

    // FITTRACK-PASSWORD-RESET-NEW-JS: Stops safely if the checkbox or password fields cannot be found.
    if (!showPasswordsCheckbox || passwordFields.length === 0) {
        console.log('FITTRACK-PASSWORD-RESET-NEW-JS: Missing checkbox or password fields.');
        return;
    }

    // FITTRACK-PASSWORD-RESET-NEW-JS: Shows that the external JS file has loaded correctly.
    console.log('FITTRACK-PASSWORD-RESET-NEW-JS: Loaded successfully.');

    // FITTRACK-PASSWORD-RESET-NEW-JS: Changes all password fields between hidden and visible.
    showPasswordsCheckbox.addEventListener('change', function () {
        const newInputType = showPasswordsCheckbox.checked ? 'text' : 'password';

        // FITTRACK-PASSWORD-RESET-NEW-JS: Applies the new input type to each password field.
        passwordFields.forEach(function (field) {
            field.setAttribute('type', newInputType);
        });

        // FITTRACK-PASSWORD-RESET-NEW-JS: Confirms in the browser console whether passwords are shown or hidden.
        console.log('FITTRACK-PASSWORD-RESET-NEW-JS: Password fields changed to ' + newInputType);
    });
});
