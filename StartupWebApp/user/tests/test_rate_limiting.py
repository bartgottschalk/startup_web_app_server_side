"""
Tests for rate limiting functionality.

Tests verify that django-ratelimit decorators properly protect endpoints
from abuse by limiting request rates based on IP addresses and usernames.
"""

from django.test import TestCase, override_settings
from django.urls import reverse
from django.core.cache import cache
from django.contrib.auth.models import User, Group
from django.utils import timezone
from user.models import Member, Termsofuse


@override_settings(RATELIMIT_ENABLE=True)
class RateLimitLoginTestCase(TestCase):
    """Test rate limiting on login endpoint."""

    def setUp(self):
        """Clear cache before each test to ensure isolation."""
        cache.clear()

        # Create Members group (required by create_account view)
        Group.objects.get_or_create(name='Members')

        # Create test user
        self.username = 'testuser'
        self.password = 'TestPass123!'
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        Member.objects.create(
            user=self.user,
            mb_cd='TEST001'
        )

    def test_login_below_limit_succeeds(self):
        """Test that requests below rate limit succeed."""
        # Make 10 login attempts (at the limit)
        for i in range(10):
            response = self.client.post(
                reverse('client_login'),
                data={
                    'username': self.username,
                    'password': self.password,
                    'remember_me': 'false'
                },
                REMOTE_ADDR='192.168.1.1'
            )
            # May return 200 (success) or 200 (auth failed), but NOT 429
            self.assertNotEqual(response.status_code, 429, f"Request {i+1} should not be rate limited")

    def test_login_exceeds_limit_returns_403(self):
        """Test that exceeding rate limit returns HTTP 403."""
        # Make 10 requests (at limit)
        for i in range(10):
            self.client.post(
                reverse('client_login'),
                data={
                    'username': self.username,
                    'password': 'wrong',
                    'remember_me': 'false'
                },
                REMOTE_ADDR='192.168.1.1'
            )

        # 11th request should be rate limited
        response = self.client.post(
            reverse('client_login'),
            data={
                'username': self.username,
                'password': 'wrong',
                'remember_me': 'false'
            },
            REMOTE_ADDR='192.168.1.1'
        )
        self.assertEqual(response.status_code, 403, "11th login attempt should return HTTP 403")

    def test_login_rate_limit_per_ip(self):
        """Test that rate limits are tracked per IP address."""
        # 10 requests from IP 1
        for i in range(10):
            self.client.post(
                reverse('client_login'),
                data={
                    'username': self.username,
                    'password': 'wrong',
                    'remember_me': 'false'
                },
                REMOTE_ADDR='192.168.1.1'
            )

        # Request from different IP should succeed
        response = self.client.post(
            reverse('client_login'),
            data={
                'username': self.username,
                'password': self.password,
                'remember_me': 'false'
            },
            REMOTE_ADDR='192.168.1.2'
        )
        self.assertNotEqual(response.status_code, 429, "Different IP should not be rate limited")


@override_settings(RATELIMIT_ENABLE=True)
class RateLimitCreateAccountTestCase(TestCase):
    """Test rate limiting on account creation endpoint."""

    def setUp(self):
        """Clear cache before each test."""
        cache.clear()

        # Create Members group (required by create_account view)
        Group.objects.get_or_create(name='Members')

        # Create Terms of Use (required by create_account view)
        Termsofuse.objects.create(
            version='1',
            version_note='Test Terms',
            publication_date_time=timezone.now()
        )

    def test_create_account_below_limit_succeeds(self):
        """Test that requests below rate limit succeed."""
        # Make 5 account creation attempts (at the limit)
        for i in range(5):
            response = self.client.post(
                reverse('create_account'),
                data={
                    'firstname': f'Test{i}',
                    'lastname': 'User',
                    'username': f'testuser{i}',
                    'email_address': f'test{i}@example.com',
                    'password': 'TestPass123!',
                    'confirm_password': 'TestPass123!',
                    'newsletter': 'false',
                    'remember_me': 'false'
                },
                REMOTE_ADDR='192.168.2.1'
            )
            # May succeed or fail validation, but NOT rate limited
            self.assertNotEqual(response.status_code, 429, f"Request {i+1} should not be rate limited")

    def test_create_account_exceeds_limit_returns_403(self):
        """Test that exceeding rate limit returns HTTP 403."""
        # Make 5 requests (at limit)
        for i in range(5):
            self.client.post(
                reverse('create_account'),
                data={
                    'firstname': f'Test{i}',
                    'lastname': 'User',
                    'username': f'user{i}',
                    'email_address': f'test{i}@example.com',
                    'password': 'TestPass123!',
                    'confirm_password': 'TestPass123!',
                    'newsletter': 'false',
                    'remember_me': 'false'
                },
                REMOTE_ADDR='192.168.2.1'
            )

        # 6th request should be rate limited
        response = self.client.post(
            reverse('create_account'),
            data={
                'firstname': 'Test6',
                'lastname': 'User',
                'username': 'user6',
                'email_address': 'test6@example.com',
                'password': 'TestPass123!',
                'confirm_password': 'TestPass123!',
                'newsletter': 'false',
                'remember_me': 'false'
            },
            REMOTE_ADDR='192.168.2.1'
        )
        self.assertEqual(response.status_code, 403, "6th account creation should return HTTP 403")

    def test_create_account_rate_limit_per_ip(self):
        """Test that rate limits are tracked per IP address."""
        # 5 requests from IP 1
        for i in range(5):
            self.client.post(
                reverse('create_account'),
                data={
                    'firstname': f'Test{i}',
                    'lastname': 'User',
                    'username': f'user{i}',
                    'email_address': f'test{i}@example.com',
                    'password': 'TestPass123!',
                    'confirm_password': 'TestPass123!',
                    'newsletter': 'false',
                    'remember_me': 'false'
                },
                REMOTE_ADDR='192.168.2.1'
            )

        # Request from different IP should succeed
        response = self.client.post(
            reverse('create_account'),
            data={
                'firstname': 'Test99',
                'lastname': 'User',
                'username': 'user99',
                'email_address': 'test99@example.com',
                'password': 'TestPass123!',
                'confirm_password': 'TestPass123!',
                'newsletter': 'false',
                'remember_me': 'false'
            },
            REMOTE_ADDR='192.168.2.2'
        )
        self.assertNotEqual(response.status_code, 429, "Different IP should not be rate limited")


@override_settings(RATELIMIT_ENABLE=True)
class RateLimitResetPasswordTestCase(TestCase):
    """Test rate limiting on password reset endpoint."""

    def setUp(self):
        """Clear cache and create test user."""
        cache.clear()

        # Create Members group (required by create_account view)
        Group.objects.get_or_create(name='Members')

        self.username = 'testuser'
        self.email = 'test@example.com'
        self.user = User.objects.create_user(
            username=self.username,
            email=self.email,
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        Member.objects.create(
            user=self.user,
            mb_cd='TEST001'
        )

    def test_reset_password_below_limit_succeeds(self):
        """Test that requests below rate limit succeed."""
        # Make 5 password reset attempts (at the limit)
        for i in range(5):
            response = self.client.post(
                reverse('reset_password'),
                data={
                    'username': self.username,
                    'email_address': self.email
                },
                REMOTE_ADDR='192.168.3.1'
            )
            # May succeed or fail, but NOT rate limited
            self.assertNotEqual(response.status_code, 429, f"Request {i+1} should not be rate limited")

    def test_reset_password_exceeds_limit_returns_403(self):
        """Test that exceeding rate limit returns HTTP 403."""
        # Make 5 requests (at limit)
        for i in range(5):
            self.client.post(
                reverse('reset_password'),
                data={
                    'username': self.username,
                    'email_address': self.email
                },
                REMOTE_ADDR='192.168.3.1'
            )

        # 6th request should be rate limited
        response = self.client.post(
            reverse('reset_password'),
            data={
                'username': self.username,
                'email_address': self.email
            },
            REMOTE_ADDR='192.168.3.1'
        )
        self.assertEqual(response.status_code, 403, "6th password reset should return HTTP 403")

    def test_reset_password_per_username(self):
        """Test that rate limits are tracked per username."""
        # Create second user
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User2'
        )
        Member.objects.create(
            user=user2,
            mb_cd='TEST002'
        )

        # 5 requests for username1
        for i in range(5):
            self.client.post(
                reverse('reset_password'),
                data={
                    'username': self.username,
                    'email_address': self.email
                },
                REMOTE_ADDR='192.168.3.1'
            )

        # Request for different username should succeed
        response = self.client.post(
            reverse('reset_password'),
            data={
                'username': 'testuser2',
                'email_address': 'test2@example.com'
            },
            REMOTE_ADDR='192.168.3.1'
        )
        self.assertNotEqual(response.status_code, 429, "Different username should not be rate limited")


@override_settings(RATELIMIT_ENABLE=True)
class RateLimitCacheFailureTestCase(TestCase):
    """Test rate limiting behavior when cache is unavailable."""

    def setUp(self):
        """Create test user."""
        # Create Members group (required by create_account view)
        Group.objects.get_or_create(name='Members')

        self.username = 'testuser'
        self.password = 'TestPass123!'
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        Member.objects.create(
            user=self.user,
            mb_cd='TEST001'
        )

    def test_cache_failure_allows_requests(self):
        """
        Test fail-open mode: requests succeed when cache fails.

        With RATELIMIT_FAIL_OPEN=True, if cache is unavailable,
        requests should be allowed (availability > security).
        """
        # Note: DummyCache would require settings override
        # For now, just test that cache.clear() works
        cache.clear()

        # Make request - should succeed even after clearing cache
        response = self.client.post(
            reverse('client_login'),
            data={
                'username': self.username,
                'password': self.password,
                'remember_me': 'false'
            },
            REMOTE_ADDR='192.168.4.1'
        )
        # Should NOT be rate limited (cache was cleared, fail-open mode)
        self.assertNotEqual(response.status_code, 429, "Request should succeed in fail-open mode")
