# Functional test for Django Admin login
# This test ensures that superusers can access and log into the Django Admin interface

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from django.contrib.auth.models import User

from functional_tests.base_functional_test import BaseFunctionalTest


class DjangoAdminLoginTest(BaseFunctionalTest):
    """
    Test that Django Admin login works correctly with CSRF cookies.

    This test catches regressions where:
    - CSRF configuration changes break admin login
    - Superuser creation doesn't work properly
    - Admin URLs become inaccessible
    """

    def test_superuser_can_login_to_django_admin(self):
        """
        Test that a superuser can successfully log into Django Admin.

        This test verifies:
        1. Admin login page is accessible
        2. CSRF cookies work correctly with .startupwebapp.com domain
        3. Superuser authentication works
        4. Admin interface loads after successful login
        """
        # Create a superuser for testing
        admin_username = 'functionaladmin'
        admin_password = 'FunctionalTestPass123'
        admin_email = 'functionaladmin@test.com'

        User.objects.create_superuser(
            username=admin_username,
            email=admin_email,
            password=admin_password
        )

        # Navigate to Django Admin login page
        # Use localliveservertestcaseapi.startupwebapp.com (LiveServerTestCase backend API domain)
        admin_url = f'http://localliveservertestcaseapi.startupwebapp.com:{self.port}/admin/'
        self.browser.get(admin_url)

        # Wait for login form to load
        wait = WebDriverWait(self.browser, 10)
        username_input = wait.until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )

        # Verify we're on the login page
        self.assertIn('Log in', self.browser.title)

        # Fill in login form
        username_input.send_keys(admin_username)
        password_input = self.browser.find_element(By.NAME, 'password')
        password_input.send_keys(admin_password)

        # Submit the form
        login_button = self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]')
        login_button.click()

        # Wait for admin dashboard to load
        wait.until(
            EC.presence_of_element_located((By.ID, 'site-name'))
        )

        # Verify successful login by checking for admin dashboard elements
        self.assertIn('Site administration', self.browser.page_source)
        self.assertIn('Django administration', self.browser.page_source)

        # Verify the admin user is shown as logged in
        # Django admin displays username in uppercase, so check case-insensitively
        user_tools = self.browser.find_element(By.ID, 'user-tools')
        self.assertIn(admin_username.upper(), user_tools.text.upper())

    def test_admin_login_fails_with_wrong_password(self):
        """
        Test that Django Admin login correctly rejects invalid credentials.

        This ensures error handling works and doesn't expose security issues.
        """
        # Create a superuser for testing
        admin_username = 'testadmin'
        admin_password = 'CorrectPassword123'

        User.objects.create_superuser(
            username=admin_username,
            email='testadmin@test.com',
            password=admin_password
        )

        # Navigate to Django Admin login page
        admin_url = f'http://localliveservertestcaseapi.startupwebapp.com:{self.port}/admin/'
        self.browser.get(admin_url)

        # Wait for login form to load
        wait = WebDriverWait(self.browser, 10)
        username_input = wait.until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )

        # Try logging in with wrong password
        username_input.send_keys(admin_username)
        password_input = self.browser.find_element(By.NAME, 'password')
        password_input.send_keys('WrongPassword123')

        # Submit the form
        login_button = self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]')
        login_button.click()

        # Wait for error message
        wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'errornote'))
        )

        # Verify error message is displayed
        error_message = self.browser.find_element(By.CLASS_NAME, 'errornote')
        self.assertIn('Please enter the correct username and password', error_message.text)

        # Verify we're still on the login page (not logged in)
        self.assertIn('Log in', self.browser.title)

    def test_non_staff_user_cannot_access_admin(self):
        """
        Test that non-staff users are denied access to Django Admin.

        This ensures proper permission checking is in place.
        """
        # Create a regular user (not staff, not superuser)
        regular_username = 'regularuser'
        regular_password = 'RegularPass123'

        User.objects.create_user(
            username=regular_username,
            email='regular@test.com',
            password=regular_password,
            is_staff=False,
            is_superuser=False
        )

        # Navigate to Django Admin login page
        admin_url = f'http://localliveservertestcaseapi.startupwebapp.com:{self.port}/admin/'
        self.browser.get(admin_url)

        # Wait for login form to load
        wait = WebDriverWait(self.browser, 10)
        username_input = wait.until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )

        # Try logging in as regular user
        username_input.send_keys(regular_username)
        password_input = self.browser.find_element(By.NAME, 'password')
        password_input.send_keys(regular_password)

        # Submit the form
        login_button = self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]')
        login_button.click()

        # Wait for error message
        wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'errornote'))
        )

        # Verify error message about staff account
        error_message = self.browser.find_element(By.CLASS_NAME, 'errornote')
        self.assertIn('staff account', error_message.text.lower())

        # Verify we're still on the login page (not logged in)
        self.assertIn('Log in', self.browser.title)
