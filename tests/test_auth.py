"""
Authentication tests for FitTrack.

Covers behaviour not already tested in test_routes.py:
  - password hashing on signup
  - duplicate email does not insert a second record
  - new users are not admins by default
  - signup auto-logs the user in
  - password check is case-sensitive
  - password change via /settings (all valid and invalid cases)

Fixtures (app, client, logged_in_client, admin_client) are defined
in tests/conftest.py. The seeded users are:
  - test@test.com  / password123  (regular)
  - admin@test.com / password123  (admin)
"""

from werkzeug.security import check_password_hash

from app import db
from app.models import User


# ─── REGISTRATION ────────────────────────────────────────────────────────────

class TestRegistration:

    def test_signup_stores_hashed_password_not_plaintext(self, app, client):
        """The stored password_hash must not equal the original plaintext."""
        plain = 'securepass99'
        client.post('/signup', data={
            'username': 'hashcheck',
            'email': 'hashcheck@example.com',
            'password': plain
        })

        with app.app_context():
            user = User.query.filter_by(email='hashcheck@example.com').first()
            assert user is not None
            assert user.password_hash != plain
            assert check_password_hash(user.password_hash, plain)

    def test_signup_new_user_is_not_admin(self, app, client):
        """A user who registers through /signup must not be granted admin."""
        client.post('/signup', data={
            'username': 'regularjoe',
            'email': 'regularjoe@example.com',
            'password': 'securepass99'
        })

        with app.app_context():
            user = User.query.filter_by(email='regularjoe@example.com').first()
            assert user.is_admin is False

    def test_signup_duplicate_email_does_not_create_second_record(self, app, client):
        """A duplicate-email attempt must not insert a second User row."""
        client.post('/signup', data={
            'username': 'dupeuser',
            'email': 'test@test.com',   # already seeded
            'password': 'securepass99'
        })

        with app.app_context():
            count = User.query.filter_by(email='test@test.com').count()
            assert count == 1

    def test_signup_logs_user_in_automatically(self, client):
        """After a successful signup the user should be redirected to the
        dashboard, not to login — confirming they were auto-authenticated."""
        response = client.post('/signup', data={
            'username': 'autologin',
            'email': 'autologin@example.com',
            'password': 'securepass99'
        }, follow_redirects=False)

        assert response.status_code == 302
        assert '/dashboard' in response.headers['Location']


# ─── LOGIN ───────────────────────────────────────────────────────────────────

class TestLogin:

    def test_login_password_check_is_case_sensitive(self, client):
        """Passwords are case-sensitive — wrong case must be rejected."""
        response = client.post('/login', data={
            'email': 'test@test.com',
            'password': 'PASSWORD123'    # correct letters, wrong case
        }, follow_redirects=True)

        assert b'Invalid email or password' in response.data

    def test_login_empty_email_does_not_authenticate(self, client):
        """Submitting with a blank email must not grant access."""
        response = client.post('/login', data={
            'email': '',
            'password': 'password123'
        }, follow_redirects=True)

        assert b'Dashboard' not in response.data

    def test_login_empty_password_does_not_authenticate(self, client):
        """Submitting with a blank password must not grant access."""
        response = client.post('/login', data={
            'email': 'test@test.com',
            'password': ''
        }, follow_redirects=True)

        assert b'Dashboard' not in response.data


# ─── PASSWORD CHANGE (/settings POST) ────────────────────────────────────────

class TestPasswordChange:

    def test_valid_password_change_is_accepted(self, logged_in_client):
        """Valid current password and matching new passwords should succeed."""
        response = logged_in_client.post('/settings', data={
            'current_password': 'password123',
            'new_password':     'newSecure456',
            'confirm_password': 'newSecure456'
        }, follow_redirects=True)

        assert b'Password updated successfully' in response.data

    def test_password_change_updates_hash_in_database(self, app, logged_in_client):
        """After a successful change the new hash must verify against the new
        password, and the old password must no longer verify."""
        logged_in_client.post('/settings', data={
            'current_password': 'password123',
            'new_password':     'brandNew789',
            'confirm_password': 'brandNew789'
        })

        with app.app_context():
            user = User.query.filter_by(email='test@test.com').first()
            assert check_password_hash(user.password_hash, 'brandNew789')
            assert not check_password_hash(user.password_hash, 'password123')

    def test_wrong_current_password_is_rejected(self, logged_in_client):
        """Supplying the wrong current password must be refused."""
        response = logged_in_client.post('/settings', data={
            'current_password': 'wrongcurrent',
            'new_password':     'newSecure456',
            'confirm_password': 'newSecure456'
        }, follow_redirects=True)

        assert b'Current password is incorrect' in response.data

    def test_mismatched_new_passwords_are_rejected(self, logged_in_client):
        """new_password and confirm_password that differ must be refused."""
        response = logged_in_client.post('/settings', data={
            'current_password': 'password123',
            'new_password':     'newSecure456',
            'confirm_password': 'differentNew789'
        }, follow_redirects=True)

        assert b'New passwords do not match' in response.data

    def test_new_password_same_as_old_is_rejected(self, logged_in_client):
        """Setting the new password to the same value as the current one
        must be refused."""
        response = logged_in_client.post('/settings', data={
            'current_password': 'password123',
            'new_password':     'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)

        assert b'New password must be different' in response.data

    def test_password_change_does_not_log_user_out(self, logged_in_client):
        """A successful password change should keep the current session active."""
        logged_in_client.post('/settings', data={
            'current_password': 'password123',
            'new_password':     'newSecure456',
            'confirm_password': 'newSecure456'
        })

        response = logged_in_client.get('/dashboard')
        assert response.status_code == 200
        assert b'My Profile' in response.data
        assert b'testuser' in response.data

    def test_old_password_rejected_after_change(self, client):
        """After a password change, logging in with the old password must fail."""
        client.post('/login', data={
            'email': 'test@test.com', 'password': 'password123'
        })
        client.post('/settings', data={
            'current_password': 'password123',
            'new_password':     'updatedPass99',
            'confirm_password': 'updatedPass99'
        })
        client.get('/logout')

        response = client.post('/login', data={
            'email':    'test@test.com',
            'password': 'password123'       # old password
        }, follow_redirects=True)

        assert b'Invalid email or password' in response.data

    def test_new_password_works_after_change(self, client):
        """After a password change, logging in with the new password must succeed."""
        client.post('/login', data={
            'email': 'test@test.com', 'password': 'password123'
        })
        client.post('/settings', data={
            'current_password': 'password123',
            'new_password':     'updatedPass99',
            'confirm_password': 'updatedPass99'
        })
        client.get('/logout')

        response = client.post('/login', data={
            'email':    'test@test.com',
            'password': 'updatedPass99'     # new password
        }, follow_redirects=True)

        assert b'Dashboard' in response.data
