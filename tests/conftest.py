import pytest
import os
import socket
import threading
from app import create_app, db
from app.models import User
from sqlalchemy.pool import StaticPool
from werkzeug.security import generate_password_hash
from werkzeug.serving import make_server


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


@pytest.fixture
def selenium_app():
    """Flask app configured for a live Selenium server and isolated database."""
    app = create_app(test_config={
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': TEST_DATABASE_URI,
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'connect_args': {'check_same_thread': False},
            'poolclass': StaticPool,
        },
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'selenium-test-secret-key',
    })

    with app.app_context():
        assert str(db.engine.url) == TEST_DATABASE_URI
        db.create_all()
        _seed_test_data()

    try:
        yield app
    finally:
        with app.app_context():
            db.session.remove()
            db.drop_all()


@pytest.fixture
def live_server(selenium_app):
    """Run the Flask app on a real local port for Selenium WebDriver tests."""
    port = _get_free_port()
    server = make_server('127.0.0.1', port, selenium_app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        yield f'http://127.0.0.1:{port}'
    finally:
        server.shutdown()
        thread.join(timeout=5)


@pytest.fixture
def browser():
    """Open a headless Chrome WebDriver and tear it down after the test."""
    pytest.importorskip('selenium')
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions

    options = ChromeOptions()
    chrome_binary = _chrome_binary_path()
    if chrome_binary:
        options.binary_location = chrome_binary

    if os.getenv('SELENIUM_HEADLESS', '1').lower() not in {'0', 'false', 'no'}:
        options.add_argument('--headless=new')

    options.add_argument('--window-size=1280,900')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(2)

    try:
        yield driver
    finally:
        driver.quit()


def _get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def _chrome_binary_path():
    configured = os.getenv('CHROME_BINARY')
    if configured and os.path.exists(configured):
        return configured

    for path in (
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    ):
        if os.path.exists(path):
            return path

    return None
