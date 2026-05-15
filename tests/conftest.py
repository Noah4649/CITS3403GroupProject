import pytest
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash


@pytest.fixture
def app(monkeypatch):
    """Create a fresh app instance with in-memory database for each test."""
    monkeypatch.setenv('SECRET_KEY', 'test-secret-key')
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })

    with app.app_context():
        db.create_all()
        _seed_test_data()
        yield app
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
