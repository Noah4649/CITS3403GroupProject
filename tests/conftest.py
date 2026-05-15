import pytest
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash


TEST_DATABASE_URI = 'sqlite:///:memory:'


@pytest.fixture
def app():
    """Create a fresh app instance with in-memory database for each test."""
    app = create_app(test_config={
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': TEST_DATABASE_URI,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })

    with app.app_context():
        assert app.config['SQLALCHEMY_DATABASE_URI'] == TEST_DATABASE_URI
        assert str(db.engine.url) == TEST_DATABASE_URI
        db.create_all()
        _seed_test_data()
        try:
            yield app
        finally:
            db.session.remove()
            db.drop_all()


def _seed_test_data():
    """Create minimal test users for route testing."""
    regular_user = User(
        username='testuser',
        email='test@test.com',
        password_hash=generate_password_hash('password123'),
        is_admin=False
    )
    admin_user = User(
        username='adminuser',
        email='admin@test.com',
        password_hash=generate_password_hash('password123'),
        is_admin=True
    )
    db.session.add_all([regular_user, admin_user])
    db.session.commit()


@pytest.fixture
def client(app):
    """Test client for making requests."""
    return app.test_client()


@pytest.fixture
def logged_in_client(client):
    """Test client with a regular user already logged in."""
    client.post('/login', data={
        'email': 'test@test.com',
        'password': 'password123'
    }, follow_redirects=True)
    return client


@pytest.fixture
def admin_client(client):
    """Test client with an admin user already logged in."""
    client.post('/login', data={
        'email': 'admin@test.com',
        'password': 'password123'
    }, follow_redirects=True)
    return client
