from app import db
from app.models import User, Workout, Comment, FeedPost, FeedPostComment


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

    def test_friends_feed_uses_user_ids_for_ownership(self, app, logged_in_client):
        """Friend feed should render immutable user IDs for ownership checks."""
        with app.app_context():
            user = User.query.filter_by(email='test@test.com').first()
            workout = Workout(
                user_id=user.id,
                title='Public test workout',
                is_public=True
            )
            db.session.add(workout)
            db.session.commit()
            user_id = user.id

        response = logged_in_client.get('/friends-feed')

        assert response.status_code == 200
        assert b'id="post-username"' not in response.data
        assert f'data-current-user-id="{user_id}"'.encode() in response.data
        assert b'data-current-username=' not in response.data
        assert f'data-owner-id="{user_id}"'.encode() in response.data
        assert b'Public test workout' in response.data

    def test_logged_in_user_can_save_friend_feed_comment(self, app, logged_in_client):
        """POST friend feed comment should save it against the workout and user IDs."""
        with app.app_context():
            user = User.query.filter_by(email='test@test.com').first()
            workout = Workout(
                user_id=user.id,
                title='Commentable workout',
                is_public=True
            )
            db.session.add(workout)
            db.session.commit()
            workout_id = workout.id
            user_id = user.id

        response = logged_in_client.post(
            f'/friends-feed/{workout_id}/comments',
            json={'text': 'Nice session!'}
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['comment']['owner_id'] == user_id
        assert data['comment']['username'] == 'testuser'
        assert data['comment']['text'] == 'Nice session!'

        with app.app_context():
            saved_comment = Comment.query.filter_by(workout_id=workout_id).first()
            assert saved_comment is not None
            assert saved_comment.user_id == user_id
            assert saved_comment.text == 'Nice session!'

    def test_friend_feed_renders_saved_comments(self, app, logged_in_client):
        """GET friend feed should render comments that were already saved."""
        with app.app_context():
            user = User.query.filter_by(email='test@test.com').first()
            workout = Workout(
                user_id=user.id,
                title='Workout with comments',
                is_public=True
            )
            db.session.add(workout)
            db.session.flush()
            db.session.add(Comment(
                workout_id=workout.id,
                user_id=user.id,
                text='Still here after refresh'
            ))
            db.session.commit()

        response = logged_in_client.get('/friends-feed')

        assert response.status_code == 200
        assert b'Workout with comments' in response.data
        assert b'Still here after refresh' in response.data
        assert b'data-owner-id=' in response.data

    def test_logged_out_user_cannot_save_friend_feed_comment(self, app, client):
        """POST friend feed comment without login should redirect to login."""
        with app.app_context():
            user = User.query.filter_by(email='test@test.com').first()
            workout = Workout(
                user_id=user.id,
                title='Protected comment workout',
                is_public=True
            )
            db.session.add(workout)
            db.session.commit()
            workout_id = workout.id

        response = client.post(
            f'/friends-feed/{workout_id}/comments',
            json={'text': 'Should not save'}
        )

        assert response.status_code == 302

    def test_logged_in_user_can_save_manual_feed_post(self, app, logged_in_client):
        """POST manual friend feed post should save it against the logged-in user."""
        with app.app_context():
            user_id = User.query.filter_by(email='test@test.com').first().id

        response = logged_in_client.post(
            '/friends-feed/posts',
            json={'content': 'Manual post that should persist'}
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['post']['owner_id'] == user_id
        assert data['post']['username'] == 'testuser'
        assert data['post']['content'] == 'Manual post that should persist'

        with app.app_context():
            saved_post = FeedPost.query.filter_by(user_id=user_id).first()
            assert saved_post is not None
            assert saved_post.content == 'Manual post that should persist'

    def test_friend_feed_renders_saved_manual_feed_post(self, app, logged_in_client):
        """GET friend feed should render manual posts that were already saved."""
        with app.app_context():
            user = User.query.filter_by(email='test@test.com').first()
            db.session.add(FeedPost(
                user_id=user.id,
                content='Still here after page refresh'
            ))
            db.session.commit()

        response = logged_in_client.get('/friends-feed')

        assert response.status_code == 200
        assert b'Still here after page refresh' in response.data
        assert b'data-feed-post-id=' in response.data

    def test_logged_in_user_can_save_manual_feed_post_comment(self, app, logged_in_client):
        """POST manual feed post comment should save it against the post and user IDs."""
        with app.app_context():
            user = User.query.filter_by(email='test@test.com').first()
            feed_post = FeedPost(
                user_id=user.id,
                content='Commentable manual post'
            )
            db.session.add(feed_post)
            db.session.commit()
            feed_post_id = feed_post.id
            user_id = user.id

        response = logged_in_client.post(
            f'/friends-feed/posts/{feed_post_id}/comments',
            json={'text': 'Manual post comment'}
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['comment']['owner_id'] == user_id
        assert data['comment']['username'] == 'testuser'
        assert data['comment']['text'] == 'Manual post comment'

        with app.app_context():
            saved_comment = FeedPostComment.query.filter_by(feed_post_id=feed_post_id).first()
            assert saved_comment is not None
            assert saved_comment.user_id == user_id
            assert saved_comment.text == 'Manual post comment'

    def test_logged_out_user_cannot_save_manual_feed_post(self, client):
        """POST manual friend feed post without login should redirect to login."""
        response = client.post(
            '/friends-feed/posts',
            json={'content': 'Should not save'}
        )

        assert response.status_code == 302

    def test_owner_can_delete_friend_feed_workout(self, app, logged_in_client):
        """DELETE friend feed workout should remove the owner's workout from the public feed."""
        with app.app_context():
            user = User.query.filter_by(email='test@test.com').first()
            workout = Workout(
                user_id=user.id,
                title='Delete me from feed',
                is_public=True
            )
            db.session.add(workout)
            db.session.commit()
            workout_id = workout.id

        response = logged_in_client.delete(f'/friends-feed/workouts/{workout_id}')

        assert response.status_code == 200
        assert response.get_json()['success'] is True

        with app.app_context():
            saved_workout = Workout.query.get(workout_id)
            assert saved_workout is not None
            assert saved_workout.is_public is False

    def test_non_owner_cannot_delete_friend_feed_workout(self, app, logged_in_client):
        """DELETE friend feed workout should reject users who do not own the workout."""
        with app.app_context():
            admin = User.query.filter_by(email='admin@test.com').first()
            workout = Workout(
                user_id=admin.id,
                title='Not your workout',
                is_public=True
            )
            db.session.add(workout)
            db.session.commit()
            workout_id = workout.id

        response = logged_in_client.delete(f'/friends-feed/workouts/{workout_id}')

        assert response.status_code == 403

        with app.app_context():
            assert Workout.query.get(workout_id) is not None

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
