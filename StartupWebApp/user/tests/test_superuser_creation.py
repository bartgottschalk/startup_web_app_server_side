# Unit tests for superuser creation via environment variables

import os
from unittest import mock

from django.contrib.auth.models import User
from django.core.management import call_command
from StartupWebApp.utilities.test_base import PostgreSQLTestCase


class SuperuserCreationTests(PostgreSQLTestCase):
    """
    Test that Django's createsuperuser command works with environment variables.

    This is critical for production deployment where we use GitHub Actions workflows
    to create superusers via ECS tasks. The environment variable approach allows
    non-interactive superuser creation in containerized environments.
    """

    def test_createsuperuser_via_env_vars(self):
        """
        Test that createsuperuser --noinput works with environment variables.

        Django's createsuperuser command supports three environment variables:
        - DJANGO_SUPERUSER_USERNAME
        - DJANGO_SUPERUSER_EMAIL
        - DJANGO_SUPERUSER_PASSWORD

        This test verifies that a superuser can be created using these environment
        variables and that the resulting user has the correct attributes.
        """
        # Define superuser credentials
        test_username = 'testadmin'
        test_email = 'testadmin@example.com'
        test_password = 'TestPass123!'

        # Set environment variables that Django's createsuperuser command reads
        with mock.patch.dict(os.environ, {
            'DJANGO_SUPERUSER_USERNAME': test_username,
            'DJANGO_SUPERUSER_EMAIL': test_email,
            'DJANGO_SUPERUSER_PASSWORD': test_password,
        }):
            # Run the createsuperuser command with --noinput flag
            call_command('createsuperuser', '--noinput')

        # Verify the user was created
        user = User.objects.get(username=test_username)
        self.assertIsNotNone(user)

        # Verify the user has superuser privileges
        self.assertTrue(user.is_superuser, 'User should have is_superuser=True')
        self.assertTrue(user.is_staff, 'User should have is_staff=True')

        # Verify the email was set correctly
        self.assertEqual(user.email, test_email)

        # Verify the password was set correctly (not stored as plaintext)
        self.assertTrue(
            user.check_password(test_password),
            'User should authenticate with the provided password'
        )

        # Verify the password is hashed (not plaintext)
        self.assertNotEqual(
            user.password,
            test_password,
            'Password should be hashed, not stored as plaintext'
        )

    def test_createsuperuser_idempotency(self):
        """
        Test that running createsuperuser twice with the same username fails gracefully.

        This ensures that running the workflow multiple times won't create duplicate
        superusers or cause unexpected errors.
        """
        test_username = 'testadmin2'
        test_email = 'testadmin2@example.com'
        test_password = 'TestPass456!'

        # Create first superuser
        with mock.patch.dict(os.environ, {
            'DJANGO_SUPERUSER_USERNAME': test_username,
            'DJANGO_SUPERUSER_EMAIL': test_email,
            'DJANGO_SUPERUSER_PASSWORD': test_password,
        }):
            call_command('createsuperuser', '--noinput')

        # Attempt to create the same superuser again - should raise an error
        with mock.patch.dict(os.environ, {
            'DJANGO_SUPERUSER_USERNAME': test_username,
            'DJANGO_SUPERUSER_EMAIL': test_email,
            'DJANGO_SUPERUSER_PASSWORD': test_password,
        }):
            with self.assertRaises(Exception) as context:
                call_command('createsuperuser', '--noinput')

        # Verify it's the expected error (username already exists)
        error_message = str(context.exception).lower()
        self.assertTrue(
            'already' in error_message or 'taken' in error_message,
            f'Should raise error indicating user already exists. Got: {context.exception}'
        )

        # Verify only one user was created
        user_count = User.objects.filter(username=test_username).count()
        self.assertEqual(user_count, 1, 'Should only have one user with this username')

    def test_createsuperuser_without_password_creates_unusable_password(self):
        """
        Test that createsuperuser --noinput creates an unusable password if not provided.

        Django's default behavior is to create a user with an unusable password when
        DJANGO_SUPERUSER_PASSWORD is not set. This is good for security but means we
        must ensure the password environment variable is always set in production.
        """
        test_username = 'testadmin3'
        test_email = 'testadmin3@example.com'

        # Create superuser without DJANGO_SUPERUSER_PASSWORD
        with mock.patch.dict(os.environ, {
            'DJANGO_SUPERUSER_USERNAME': test_username,
            'DJANGO_SUPERUSER_EMAIL': test_email,
            # Missing DJANGO_SUPERUSER_PASSWORD - Django will create unusable password
        }, clear=False):
            call_command('createsuperuser', '--noinput')

        # Verify the user was created
        user = User.objects.get(username=test_username)
        self.assertIsNotNone(user)

        # Verify the user has an unusable password (cannot log in)
        self.assertFalse(
            user.has_usable_password(),
            'User should have unusable password when DJANGO_SUPERUSER_PASSWORD not provided'
        )

        # Verify password starts with '!' (Django's convention for unusable passwords)
        self.assertTrue(
            user.password.startswith('!'),
            'Unusable passwords should start with "!"'
        )
