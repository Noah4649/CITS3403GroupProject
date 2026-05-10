class TestPublicRoutes:
    """Tests for routes accessible without logging in."""

    def test_welcome_page_logged_out(self, client):
        """GET / should show welcome page for logged out users."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'FitTrack' in response.data

    def test_login_page_get(self, client):
        """GET /login should render the login page."""
        response = client.get('/login')
        assert response.status_code == 200

    def test_signup_page_get(self, client):
        """GET /signup should render the signup page."""
        response = client.get('/signup')
        assert response.status_code == 200

    def test_password_reset_page_get(self, client):
        """GET /password-reset should render the password reset page."""
        response = client.get('/password-reset')
        assert response.status_code == 200

    def test_terms_page_get(self, client):
        """GET /terms should be accessible to everyone."""
        response = client.get('/terms')
        assert response.status_code == 200


class TestAuthRoutes:
    """Tests for login, signup and logout."""

    def test_login_valid_credentials(self, client):
        """POST /login with valid credentials should redirect to dashboard."""
        response = client.post('/login', data={
            'email': 'test@test.com',
            'password': 'password123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Dashboard' in response.data

    def test_login_invalid_password(self, client):
        """POST /login with wrong password should show error."""
        response = client.post('/login', data={
            'email': 'test@test.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Invalid email or password' in response.data

    def test_login_invalid_email(self, client):
        """POST /login with unregistered email should show error."""
        response = client.post('/login', data={
            'email': 'nobody@test.com',
            'password': 'password123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Invalid email or password' in response.data

    def test_signup_new_user(self, client):
        """POST /signup with new credentials should create user and redirect."""
        response = client.post('/signup', data={
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'password123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Dashboard' in response.data

    def test_signup_duplicate_email(self, client):
        """POST /signup with existing email should show error."""
        response = client.post('/signup', data={
            'username': 'anotheruser',
            'email': 'test@test.com',
            'password': 'password123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Email already registered' in response.data

    def test_logout(self, logged_in_client):
        """GET /logout should redirect to login page."""
        response = logged_in_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data


class TestProtectedRoutes:
    """Tests for routes that require login."""

    def test_dashboard_logged_out_redirects(self, client):
        """GET /dashboard without login should redirect to login."""
        response = client.get('/dashboard', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_dashboard_logged_in(self, logged_in_client):
        """GET /dashboard while logged in should render dashboard."""
        response = logged_in_client.get('/dashboard')
        assert response.status_code == 200

    def test_profile_logged_out_redirects(self, client):
        """GET /profile without login should redirect to login."""
        response = client.get('/profile', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_profile_logged_in(self, logged_in_client):
        """GET /profile while logged in should render profile page."""
        response = logged_in_client.get('/profile')
        assert response.status_code == 200

    def test_history_logged_out_redirects(self, client):
        """GET /history without login should redirect to login."""
        response = client.get('/history', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_history_logged_in(self, logged_in_client):
        """GET /history while logged in should render history page."""
        response = logged_in_client.get('/history')
        assert response.status_code == 200

    def test_calories_logged_out_redirects(self, client):
        """GET /calories without login should redirect to login."""
        response = client.get('/calories', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_calories_logged_in(self, logged_in_client):
        """GET /calories while logged in should render calories page."""
        response = logged_in_client.get('/calories')
        assert response.status_code == 200

    def test_leaderboard_logged_out_redirects(self, client):
        """GET /leaderboard without login should redirect to login."""
        response = client.get('/leaderboard', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_leaderboard_logged_in(self, logged_in_client):
        """GET /leaderboard while logged in should render leaderboard page."""
        response = logged_in_client.get('/leaderboard')
        assert response.status_code == 200

    def test_friends_feed_logged_out_redirects(self, client):
        """GET /friends-feed without login should redirect to login."""
        response = client.get('/friends-feed', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_friends_feed_logged_in(self, logged_in_client):
        """GET /friends-feed while logged in should render friends feed."""
        response = logged_in_client.get('/friends-feed')
        assert response.status_code == 200

    def test_settings_logged_out_redirects(self, client):
        """GET /settings without login should redirect to login."""
        response = client.get('/settings', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_settings_logged_in(self, logged_in_client):
        """GET /settings while logged in should render settings page."""
        response = logged_in_client.get('/settings')
        assert response.status_code == 200

    def test_welcome_logged_in_redirects_to_dashboard(self, logged_in_client):
        """GET / while logged in should redirect to dashboard."""
        response = logged_in_client.get('/', follow_redirects=True)
        assert response.status_code == 200
        assert b'Dashboard' in response.data


class TestAdminRoutes:
    """Tests for admin-only routes."""

    def test_admin_logged_out_redirects(self, client):
        """GET /admin without login should redirect to login."""
        response = client.get('/admin', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_admin_non_admin_user_gets_403(self, logged_in_client):
        """GET /admin as non-admin should return 403."""
        response = logged_in_client.get('/admin')
        assert response.status_code == 403

    def test_admin_admin_user_gets_200(self, admin_client):
        """GET /admin as admin should return 200."""
        response = admin_client.get('/admin')
        assert response.status_code == 200