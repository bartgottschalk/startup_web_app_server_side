# Unit tests for reset password endpoint


from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.core import mail

from clientevent.models import Configuration as ClientEventConfiguration
from order.models import Skutype, Skuinventory, Product, Sku, Skuprice, Productsku
from user.models import Termsofuse

from StartupWebApp.utilities import unittest_utilities


class ResetPasswordAPITest(PostgreSQLTestCase):

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

        # Create a test user for password reset tests
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
        # Logout after creating user
        self.client.post('/user/logout')

        # Clear mail outbox
        mail.outbox = []

    def test_valid_reset_password_request(self):
        """Test successful password reset request with valid username and email"""
        response = self.client.post('/user/reset-password', data={
            'username': 'testuser',
            'email_address': 'testuser@test.com'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                             '{"reset_password": "success", "user-api-version": "0.0.1"}',
                             'Valid reset password request should succeed')

        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1, 'Password reset email should be sent')
        self.assertIn(
            'password',
            mail.outbox[0].subject.lower(),
            'Email subject should mention password')
        self.assertEqual(mail.outbox[0].to[0], 'testuser@test.com',
                         'Email should be sent to correct address')

        # Verify token was generated in database
        user = User.objects.get(username='testuser')
        member = user.member
        self.assertIsNotNone(
            member.reset_password_string,
            'Reset password string should be generated')
        self.assertIsNotNone(
            member.reset_password_string_signed,
            'Reset password string signed should be generated')
        self.assertTrue(len(member.reset_password_string) > 0,
                        'Reset password string should not be empty')
        self.assertTrue(len(member.reset_password_string_signed) > 0,
                        'Reset password string signed should not be empty')

    def test_nonexistent_username(self):
        """Test reset password with non-existent username - should return success but not send email"""
        response = self.client.post('/user/reset-password', data={
            'username': 'nonexistentuser',
            'email_address': 'fake@test.com'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(
            response.content.decode('utf8'),
            '{"reset_password": "success", "user-api-version": "0.0.1"}',
            'Reset password with nonexistent username should return success (security)')

        # Verify NO email was sent
        self.assertEqual(len(mail.outbox), 0, 'No email should be sent for nonexistent username')

    def test_wrong_email_for_username(self):
        """Test reset password with valid username but wrong email - should return success but not send email"""
        response = self.client.post('/user/reset-password', data={
            'username': 'testuser',
            'email_address': 'wrongemail@test.com'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                             '{"reset_password": "success", "user-api-version": "0.0.1"}',
                             'Reset password with wrong email should return success (security)')

        # Verify NO email was sent
        self.assertEqual(len(mail.outbox), 0,
                         'No email should be sent when email does not match username')

    def test_email_case_insensitivity(self):
        """Test that email comparison is case-insensitive"""
        response = self.client.post('/user/reset-password', data={
            'username': 'testuser',
            'email_address': 'TESTUSER@TEST.COM'  # Different case
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                             '{"reset_password": "success", "user-api-version": "0.0.1"}',
                             'Reset password with different case email should succeed')

        # Verify email WAS sent (case-insensitive match)
        self.assertEqual(len(mail.outbox), 1,
                         'Password reset email should be sent for case-insensitive email match')

    def test_multiple_reset_requests(self):
        """Test that multiple reset requests generate new tokens (overwriting old ones)"""
        # First reset request
        response1 = self.client.post('/user/reset-password', data={
            'username': 'testuser',
            'email_address': 'testuser@test.com'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response1)

        # Get first token
        user = User.objects.get(username='testuser')
        member = user.member
        first_token = member.reset_password_string
        first_signed_token = member.reset_password_string_signed

        # Second reset request
        response2 = self.client.post('/user/reset-password', data={
            'username': 'testuser',
            'email_address': 'testuser@test.com'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response2)

        # Get second token
        member.refresh_from_db()
        second_token = member.reset_password_string
        second_signed_token = member.reset_password_string_signed

        # Verify tokens changed
        self.assertNotEqual(
            first_token,
            second_token,
            'New reset request should generate new token')
        self.assertNotEqual(
            first_signed_token,
            second_signed_token,
            'New reset request should generate new signed token')

        # Verify two emails were sent
        self.assertEqual(len(mail.outbox), 2, 'Both reset requests should send emails')

    def test_token_structure(self):
        """Test that both plain and signed tokens are stored correctly"""
        response = self.client.post('/user/reset-password', data={
            'username': 'testuser',
            'email_address': 'testuser@test.com'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        # Verify token structure in database
        user = User.objects.get(username='testuser')
        member = user.member

        # Plain token should be alphanumeric
        self.assertTrue(
            member.reset_password_string.isalnum(),
            'Plain token should be alphanumeric')

        # Signed token should contain colon (signature separator)
        self.assertIn(':', member.reset_password_string_signed,
                      'Signed token should contain colon separator')

        # Signed token should be longer than plain token (includes timestamp and signature)
        self.assertGreater(len(member.reset_password_string_signed), len(
            member.reset_password_string), 'Signed token should be longer than plain token')
