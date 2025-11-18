# Unit tests for verify email address request endpoint


from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.core import mail

from clientevent.models import Configuration as ClientEventConfiguration
from order.models import Skutype, Skuinventory, Product, Sku, Skuprice, Productsku
from user.models import Termsofuse

from StartupWebApp.utilities import unittest_utilities


class VerifyEmailAddressAPITest(PostgreSQLTestCase):

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

        # Create a test user and log them in
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
        # User should be automatically logged in after account creation

        # Clear mail outbox
        mail.outbox = []

    def test_valid_verification_request(self):
        """Test successful email verification request from authenticated user"""
        response = self.client.post('/user/verify-email-address')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(
            response.content.decode('utf8'),
            '{"verify_email_address": "verification_email_sent", "user-api-version": "0.0.1"}',
            'Valid verification request should succeed')

        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1, 'Verification email should be sent')
        self.assertIn(
            'verification',
            mail.outbox[0].subject.lower(),
            'Email subject should mention verification')
        self.assertEqual(
            mail.outbox[0].to[0],
            'testuser@test.com',
            'Email should be sent to user email')

        # Verify tokens were generated in database
        user = User.objects.get(username='testuser')
        member = user.member
        self.assertIsNotNone(
            member.email_verification_string,
            'Email verification string should be generated')
        self.assertIsNotNone(
            member.email_verification_string_signed,
            'Email verification string signed should be generated')
        self.assertEqual(len(member.email_verification_string), 20,
                         'Email verification string should be 20 characters')
        self.assertTrue(len(member.email_verification_string_signed) > 20,
                        'Signed string should be longer than plain string')

        # Verify email_verified is still False
        self.assertFalse(member.email_verified, 'Email should not be verified yet')

    def test_unauthenticated_user(self):
        """Test that unauthenticated user cannot request email verification"""
        # Logout first
        self.client.post('/user/logout')

        response = self.client.post('/user/verify-email-address')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(
            response.content.decode('utf8'),
            '{"verify_email_address": "user_not_authenticated", "user-api-version": "0.0.1"}',
            'Unauthenticated user should not be able to request verification')

        # Verify NO email was sent
        self.assertEqual(len(mail.outbox), 0, 'No email should be sent for unauthenticated user')

    def test_multiple_verification_requests(self):
        """Test that multiple verification requests generate new tokens (overwriting old ones)"""
        # First verification request
        response1 = self.client.post('/user/verify-email-address')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response1)

        # Get first tokens
        user = User.objects.get(username='testuser')
        member = user.member
        first_token = member.email_verification_string
        first_signed_token = member.email_verification_string_signed

        # Second verification request
        response2 = self.client.post('/user/verify-email-address')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response2)

        # Get second tokens
        member.refresh_from_db()
        second_token = member.email_verification_string
        second_signed_token = member.email_verification_string_signed

        # Verify tokens changed
        self.assertNotEqual(
            first_token,
            second_token,
            'New verification request should generate new token')
        self.assertNotEqual(
            first_signed_token,
            second_signed_token,
            'New verification request should generate new signed token')

        # Verify two emails were sent
        self.assertEqual(len(mail.outbox), 2, 'Both verification requests should send emails')

    def test_token_structure(self):
        """Test that both plain and signed tokens are stored correctly"""
        response = self.client.post('/user/verify-email-address')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        # Verify token structure in database
        user = User.objects.get(username='testuser')
        member = user.member

        # Plain token should be exactly 20 characters
        self.assertEqual(len(member.email_verification_string),
                         20, 'Plain token should be 20 characters')
        self.assertTrue(
            member.email_verification_string.isalnum(),
            'Plain token should be alphanumeric')

        # Signed token should contain colon (signature separator)
        self.assertIn(':', member.email_verification_string_signed,
                      'Signed token should contain colon separator')

        # Signed token should be longer than plain token (includes timestamp and signature)
        self.assertGreater(len(member.email_verification_string_signed), len(
            member.email_verification_string), 'Signed token should be longer than plain token')

    def test_email_content_includes_verification_link(self):
        """Test that verification email includes the signed verification code"""
        response = self.client.post('/user/verify-email-address')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        # Get the signed token from database
        user = User.objects.get(username='testuser')
        member = user.member
        signed_token = member.email_verification_string_signed

        # Verify email was sent and contains the signed token
        self.assertEqual(len(mail.outbox), 1, 'Verification email should be sent')
        email_body = mail.outbox[0].body

        # Verify email contains the verification code
        self.assertIn(
            signed_token,
            email_body,
            'Email should contain the signed verification token')
        self.assertIn('email_verification_code=', email_body,
                      'Email should contain verification URL parameter')
        self.assertIn('/account/', email_body, 'Email should contain account page URL')

        # Verify email contains security warnings
        self.assertIn('24 hours', email_body, 'Email should mention 24-hour expiry')
        self.assertIn(
            'DID NOT REQUEST',
            email_body.upper(),
            'Email should include security warning')
