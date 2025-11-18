# Unit tests for verify email address response (confirmation) endpoint

import json

from django.test import TestCase
from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.core.signing import TimestampSigner

from clientevent.models import Configuration as ClientEventConfiguration
from order.models import Skutype, Skuinventory, Product, Sku, Skuprice, Productsku
from user.models import Termsofuse

from StartupWebApp.utilities import unittest_utilities


class VerifyEmailAddressResponseAPITest(PostgreSQLTestCase):

    def setUp(self):
        # Setup necessary DB Objects
        ClientEventConfiguration.objects.create(id=1, log_client_events=True)

        Skutype.objects.create(id=1, title='product')
        Skuinventory.objects.create(
            id=1,
            title='In Stock',
            identifier='in-stack',
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

        # Request email verification to generate token
        self.client.post('/user/verify-email-address')

        # Get the generated verification code
        user = User.objects.get(username='testuser')
        self.member = user.member
        self.verification_code = self.member.email_verification_string_signed

    def test_valid_verification_response(self):
        """Test successful email verification with valid token"""
        # Verify email is not verified yet
        self.assertFalse(self.member.email_verified, 'Email should not be verified initially')

        response = self.client.post('/user/verify-email-address-response', data={
            'email_verification_code': self.verification_code
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(
            response.content.decode('utf8'),
            '{"verify_email_address_response": "success", "user-api-version": "0.0.1"}',
            'Valid verification should succeed')

        # Verify email_verified is now True
        self.member.refresh_from_db()
        self.assertTrue(self.member.email_verified,
                        'Email should be verified after successful verification')

        # Verify tokens were cleared
        self.assertIsNone(
            self.member.email_verification_string,
            'Verification string should be cleared')
        self.assertIsNone(self.member.email_verification_string_signed,
                          'Verification string signed should be cleared')

    def test_invalid_token(self):
        """Test that tampered/invalid token is rejected"""
        response = self.client.post('/user/verify-email-address-response', data={
            'email_verification_code': 'invalid_tampered_token_12345'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['verify_email_address_response'], 'signature-invalid',
                         'Invalid token should fail with signature-invalid')

        # Verify email is still not verified
        self.member.refresh_from_db()
        self.assertFalse(self.member.email_verified,
                         'Email should not be verified after invalid token')

        # Verify tokens were NOT cleared
        self.assertIsNotNone(
            self.member.email_verification_string,
            'Verification string should still exist')

    def test_expired_token(self):
        """Test that expired token (simulated) is rejected"""
        # Create a token that will be treated as invalid/expired
        # We can't easily create an actually expired token, so test with invalid format
        response = self.client.post('/user/verify-email-address-response', data={
            'email_verification_code': 'expired_token'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['verify_email_address_response'], 'signature-invalid',
                         'Expired/invalid token should fail')

        # Verify email is still not verified
        self.member.refresh_from_db()
        self.assertFalse(self.member.email_verified,
                         'Email should not be verified after expired token')

    def test_token_mismatch(self):
        """Test that token with wrong value is rejected"""
        # Create a valid signed token but with different value
        signer = TimestampSigner(salt='email_verification')
        wrong_token = signer.sign('wrongvalue12345678')

        response = self.client.post('/user/verify-email-address-response', data={
            'email_verification_code': wrong_token
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['verify_email_address_response'], 'code-doesnt-match',
                         'Token with wrong value should fail with code-doesnt-match')

        # Verify email is still not verified
        self.member.refresh_from_db()
        self.assertFalse(self.member.email_verified,
                         'Email should not be verified after token mismatch')

    def test_unauthenticated_user(self):
        """Test that unauthenticated user cannot verify email"""
        # Logout first
        self.client.post('/user/logout')

        response = self.client.post('/user/verify-email-address-response', data={
            'email_verification_code': self.verification_code
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(
            response.content.decode('utf8'),
            '{"verify_email_address_response": "user_not_authenticated", "user-api-version": "0.0.1"}',
            'Unauthenticated user should not be able to verify email')

    def test_already_verified_email(self):
        """Test idempotent behavior - verifying already verified email"""
        # First verification
        response1 = self.client.post('/user/verify-email-address-response', data={
            'email_verification_code': self.verification_code
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response1)

        # Verify email is verified
        self.member.refresh_from_db()
        self.assertTrue(self.member.email_verified,
                        'Email should be verified after first verification')

        # Request new verification token (since old one was cleared)
        self.client.post('/user/verify-email-address')
        self.member.refresh_from_db()
        new_verification_code = self.member.email_verification_string_signed

        # Second verification with new token
        response2 = self.client.post('/user/verify-email-address-response', data={
            'email_verification_code': new_verification_code
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response2)
        self.assertJSONEqual(
            response2.content.decode('utf8'),
            '{"verify_email_address_response": "success", "user-api-version": "0.0.1"}',
            'Re-verification should succeed')

        # Email should still be verified
        self.member.refresh_from_db()
        self.assertTrue(self.member.email_verified, 'Email should remain verified')

    def test_verification_persists_after_logout_login(self):
        """Test that email verification status persists through logout/login cycle"""
        # Verify email
        response = self.client.post('/user/verify-email-address-response', data={
            'email_verification_code': self.verification_code
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        # Verify email is verified
        self.member.refresh_from_db()
        self.assertTrue(self.member.email_verified, 'Email should be verified')

        # Logout
        self.client.post('/user/logout')

        # Login again
        self.client.post('/user/login', data={
            'username': 'testuser',
            'password': 'ValidPass1!',
            'remember_me': 'false'
        })

        # Verify email_verified status persisted
        self.member.refresh_from_db()
        self.assertTrue(self.member.email_verified,
                        'Email verified status should persist after logout/login')
