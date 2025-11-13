# Unit tests for forgot username endpoint


from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import Group
from django.core import mail

from clientevent.models import Configuration as ClientEventConfiguration
from order.models import Skutype, Skuinventory, Product, Sku, Skuprice, Productsku
from user.models import Termsofuse

from StartupWebApp.utilities import unittest_utilities


class ForgotUsernameAPITest(TestCase):

    def setUp(self):
        # Setup necessary DB Objects
        ClientEventConfiguration.objects.create(id=1, log_client_events=True)

        Skutype.objects.create(id=1, title='product')
        Skuinventory.objects.create(
            id=1,
            title='In Stock',
            identifier='in-stock',
            description='In Stock items are available to purchase.')
        Product.objects.create(
            id=1,
            title='Paper Clips',
            title_url='PaperClips',
            identifier='bSusp6dBHm',
            headline='Paper clips can hold up to 20 pieces of paper together!',
            description_part_1='Made out of high quality metal and folded to exact specifications.',
            description_part_2='Use paperclips for all your paper binding needs!')
        Sku.objects.create(
            id=1,
            color='Silver',
            size='Medium',
            sku_type_id=1,
            description='Left Sided Paperclip',
            sku_inventory_id=1)
        Skuprice.objects.create(id=1, price=3.5, created_date_time=timezone.now(), sku_id=1)
        Productsku.objects.create(id=1, product_id=1, sku_id=1)
        Group.objects.create(name='Members')
        Termsofuse.objects.create(
            version='1',
            version_note='Test Terms',
            publication_date_time=timezone.now())

        # Create a test user
        self.client.post('/user/create-account', data={
            'firstname': 'Test',
            'lastname': 'User',
            'username': 'testuser',
            'email_address': 'testuser@test.com',
            'password': 'ValidPass1!',
            'confirm_password': 'ValidPass1!',
            'newsletter': 'false',
            'remember_me': 'false'
        })
        self.client.post('/user/logout')

        # Clear mail outbox
        mail.outbox = []

    def test_valid_email_sends_username(self):
        """Test that valid email address results in username reminder email"""
        response = self.client.post('/user/forgot-username', data={
            'email_address': 'testuser@test.com'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                             '{"forgot_username": "success", "user-api-version": "0.0.1"}',
                             'Forgot username request should succeed')

        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1, 'Username reminder email should be sent')
        self.assertIn(
            'username',
            mail.outbox[0].subject.lower(),
            'Email subject should mention username')
        self.assertEqual(mail.outbox[0].to[0], 'testuser@test.com',
                         'Email should be sent to correct address')

        # Verify email contains username
        self.assertIn('testuser', mail.outbox[0].body, 'Email should contain username')

    def test_nonexistent_email(self):
        """Test that non-existent email returns success but sends no email (security)"""
        response = self.client.post('/user/forgot-username', data={
            'email_address': 'nonexistent@test.com'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(
            response.content.decode('utf8'),
            '{"forgot_username": "success", "user-api-version": "0.0.1"}',
            'Forgot username with nonexistent email should return success (security)')

        # Verify NO email was sent
        self.assertEqual(len(mail.outbox), 0, 'No email should be sent for nonexistent email')

    def test_email_case_sensitivity(self):
        """Test that email comparison is case-sensitive (Django default behavior)"""
        response = self.client.post('/user/forgot-username', data={
            'email_address': 'TESTUSER@TEST.COM'  # Different case
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                             '{"forgot_username": "success", "user-api-version": "0.0.1"}',
                             'Forgot username returns success regardless of match (security)')

        # Verify email was NOT sent (case-sensitive match failed)
        self.assertEqual(len(mail.outbox), 0,
                         'Email should not be sent for different case email (case-sensitive)')

    def test_multiple_users_same_email(self):
        """Test that multiple users with same email all receive username reminders"""
        # Create a second user with the same email
        self.client.post('/user/create-account', data={
            'firstname': 'Second',
            'lastname': 'User',
            'username': 'seconduser',
            'email_address': 'testuser@test.com',  # Same email
            'password': 'ValidPass2!',
            'confirm_password': 'ValidPass2!',
            'newsletter': 'false',
            'remember_me': 'false'
        })
        self.client.post('/user/logout')

        # Clear mail outbox after second user creation
        mail.outbox = []

        # Request forgot username
        response = self.client.post('/user/forgot-username', data={
            'email_address': 'testuser@test.com'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        # Verify TWO emails were sent (one for each user)
        self.assertEqual(len(mail.outbox), 2,
                         'Should send username reminder to both users with same email')

        # Verify both emails contain different usernames
        email_bodies = [email.body for email in mail.outbox]
        self.assertTrue(any('testuser' in body for body in email_bodies),
                        'One email should contain first username')
        self.assertTrue(any('seconduser' in body for body in email_bodies),
                        'One email should contain second username')
