import uuid

import pytest

selenium = pytest.importorskip('selenium')
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


pytestmark = pytest.mark.selenium


def _wait(browser, timeout=5):
    return WebDriverWait(browser, timeout)


def _login(browser, live_server, email='test@test.com', password='password123'):
    browser.get(f'{live_server}/login')
    browser.find_element(By.ID, 'email').send_keys(email)
    browser.find_element(By.ID, 'password').send_keys(password)
    browser.find_element(By.ID, 'login-submit').click()

    _wait(browser).until(EC.url_contains('/dashboard'))
    _wait(browser).until(EC.text_to_be_present_in_element((By.TAG_NAME, 'body'), 'My Profile'))


def test_signup_page_creates_account(browser, live_server):
    # FITTRACK-SELENIUM-TEST: A new user can complete signup in a real browser.
    username = f'selenium_{uuid.uuid4().hex[:8]}'
    email = f'{username}@example.com'

    browser.get(f'{live_server}/signup')
    browser.find_element(By.ID, 'username').send_keys(username)
    browser.find_element(By.ID, 'email').send_keys(email)
    browser.find_element(By.ID, 'password').send_keys('password123')
    browser.find_element(By.ID, 'retype-password').send_keys('password123')
    browser.find_element(By.ID, 'signup-submit').click()

    _wait(browser).until(EC.url_contains('/dashboard'))
    _wait(browser).until(EC.text_to_be_present_in_element((By.TAG_NAME, 'body'), username))
    assert 'My Profile' in browser.page_source


def test_existing_user_can_log_in(browser, live_server):
    # FITTRACK-SELENIUM-TEST: A seeded user can log in and reach the dashboard.
    _login(browser, live_server)

    assert '/dashboard' in browser.current_url
    assert 'testuser' in browser.page_source
    assert 'test@test.com' in browser.page_source


def test_logged_out_user_is_redirected_from_dashboard(browser, live_server):
    # FITTRACK-SELENIUM-TEST: Protected pages send anonymous users to login.
    browser.get(f'{live_server}/dashboard')

    _wait(browser).until(EC.url_contains('/login'))
    assert 'Login' in browser.page_source
    assert 'Email' in browser.page_source


def test_logged_in_user_can_open_friends_feed(browser, live_server):
    # FITTRACK-SELENIUM-TEST: Authenticated users can access the friend feed UI.
    _login(browser, live_server)

    browser.get(f'{live_server}/friends-feed')

    _wait(browser).until(EC.text_to_be_present_in_element((By.TAG_NAME, 'body'), 'Friend Feed'))
    assert browser.find_element(By.ID, 'post-content').is_displayed()
    assert browser.find_element(By.ID, 'add-post-btn').is_enabled()


def test_logged_in_user_can_create_friend_feed_post(browser, live_server):
    # FITTRACK-SELENIUM-TEST: Browser-created feed posts persist after refresh.
    post_text = f'Selenium feed post {uuid.uuid4().hex[:8]}'
    _login(browser, live_server)

    browser.get(f'{live_server}/friends-feed')
    browser.find_element(By.ID, 'post-content').send_keys(post_text)
    browser.find_element(By.ID, 'add-post-btn').click()

    _wait(browser).until(EC.text_to_be_present_in_element((By.ID, 'feed-container'), post_text))
    browser.refresh()
    _wait(browser).until(EC.text_to_be_present_in_element((By.ID, 'feed-container'), post_text))
    assert 'testuser' in browser.page_source
