# Unit tests for update my information endpoint

import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.core import mail

from clientevent.models import Configuration as ClientEventConfiguration
from order.models import Skutype, Skuinventory, Product, Sku, Skuprice, Productsku
from user.models import Termsofuse

from StartupWebApp.utilities import unittest_utilities


class UpdateMyInformationAPITest(TestCase):

    def setUp(self):
        # Setup necessary DB Objects
        ClientEventConfiguration.objects.create(id=1, log_client_events=True)

        Skutype.objects.create(id=1, title='product')
        Skuinventory.objects.create(id=1, title='In Stock', identifier='in-stock', description='In Stock items are available to purchase.')
        Product.objects.create(id=1, title='Paper Clips', title_url='PaperClips', identifier='bSusp6dBHm', headline='Paper clips can hold up to 20 pieces of paper together!', description_part_1='Made out of high quality metal and folded to exact specifications.', description_part_2='Use paperclips for all your paper binding needs!')
        Sku.objects.create(id=1, color='Silver', size='Medium', sku_type_id=1, description='Left Sided Paperclip', sku_inventory_id=1)
        Skuprice.objects.create(id=1, price=3.5, created_date_time=timezone.now(), sku_id=1)
        Productsku.objects.create(id=1, product_id=1, sku_id=1)
        Group.objects.create(name='Members')
        Termsofuse.objects.create(version='1', version_note='Test Terms', publication_date_time=timezone.now())

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

    def test_valid_update_name_only(self):
        """Test successful update of name without changing email"""
        response = self.client.post('/user/update-my-information', data={
            'firstname': 'Updated',
            'lastname': 'Name',
            'email_address': 'testuser@test.com'  # Same email
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                            '{"update_my_information": "success", "user-api-version": "0.0.1"}',
                            'Valid update should succeed')

        # Verify user data was updated
        user = User.objects.get(username='testuser')
        self.assertEqual(user.first_name, 'Updated')
        self.assertEqual(user.last_name, 'Name')
        self.assertEqual(user.email, 'testuser@test.com')

        # Verify NO email was sent (email didn't change)
        self.assertEqual(len(mail.outbox), 0, 'No email should be sent when email unchanged')

    def test_valid_update_with_email_change(self):
        """Test successful update with email change triggers notification and verification reset"""
        # Set email as verified initially
        user = User.objects.get(username='testuser')
        user.member.email_verified = True
        user.member.save()

        response = self.client.post('/user/update-my-information', data={
            'firstname': 'Updated',
            'lastname': 'Name',
            'email_address': 'newemail@test.com'  # Changed email
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                            '{"update_my_information": "success", "user-api-version": "0.0.1"}',
                            'Valid update with email change should succeed')

        # Verify user data was updated
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Updated')
        self.assertEqual(user.last_name, 'Name')
        self.assertEqual(user.email, 'newemail@test.com')

        # Verify email_verified was reset to False
        self.assertFalse(user.member.email_verified, 'Email verified should be reset to False on email change')

        # Verify new verification tokens were generated
        self.assertIsNotNone(user.member.email_verification_string, 'New verification token should be generated')
        self.assertIsNotNone(user.member.email_verification_string_signed, 'New signed token should be generated')

        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1, 'Email notification should be sent on email change')

    def test_email_change_notification_sent_to_both_addresses(self):
        """Test that email change notification is sent to both old and new email addresses"""
        response = self.client.post('/user/update-my-information', data={
            'firstname': 'Test',
            'lastname': 'User',
            'email_address': 'newemail@test.com'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        # Verify email was sent to both addresses
        self.assertEqual(len(mail.outbox), 1, 'Email should be sent')
        email = mail.outbox[0]
        self.assertEqual(len(email.to), 2, 'Email should be sent to 2 recipients')
        self.assertIn('newemail@test.com', email.to, 'New email should receive notification')
        self.assertIn('testuser@test.com', email.to, 'Old email should receive notification')

        # Verify email contains relevant info
        self.assertIn('testuser@test.com', email.body, 'Email should mention old address')
        self.assertIn('newemail@test.com', email.body, 'Email should mention new address')

    def test_invalid_firstname_rejected(self):
        """Test that invalid first name is rejected"""
        # Name validation requires non-empty string, max length 30
        response = self.client.post('/user/update-my-information', data={
            'firstname': '',  # Empty - invalid
            'lastname': 'User',
            'email_address': 'testuser@test.com'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['update_my_information'], 'errors', 'Invalid first name should be rejected')
        self.assertIn('errors', response_data, 'Should return error messages')
        self.assertIn('firstname', response_data['errors'], 'Should have firstname error')

        # Verify user data was NOT updated
        user = User.objects.get(username='testuser')
        self.assertEqual(user.first_name, 'Test', 'First name should not be updated')

    def test_invalid_lastname_rejected(self):
        """Test that invalid last name is rejected"""
        response = self.client.post('/user/update-my-information', data={
            'firstname': 'Test',
            'lastname': '',  # Empty - invalid
            'email_address': 'testuser@test.com'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['update_my_information'], 'errors', 'Invalid last name should be rejected')
        self.assertIn('errors', response_data, 'Should return error messages')
        self.assertIn('lastname', response_data['errors'], 'Should have lastname error')

        # Verify user data was NOT updated
        user = User.objects.get(username='testuser')
        self.assertEqual(user.last_name, 'User', 'Last name should not be updated')

    def test_invalid_email_rejected(self):
        """Test that invalid email address is rejected"""
        response = self.client.post('/user/update-my-information', data={
            'firstname': 'Test',
            'lastname': 'User',
            'email_address': 'not-a-valid-email'  # Invalid format
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['update_my_information'], 'errors', 'Invalid email should be rejected')
        self.assertIn('errors', response_data, 'Should return error messages')
        self.assertIn('email-address', response_data['errors'], 'Should have email-address error')

        # Verify user data was NOT updated
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'testuser@test.com', 'Email should not be updated')

    def test_unauthenticated_user_rejected(self):
        """Test that unauthenticated user cannot update information"""
        # Logout first
        self.client.post('/user/logout')

        response = self.client.post('/user/update-my-information', data={
            'firstname': 'Hacker',
            'lastname': 'Attempt',
            'email_address': 'hacker@test.com'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                            '{"update_my_information": "user_not_authenticated", "user-api-version": "0.0.1"}',
                            'Unauthenticated user should be rejected')

    def test_email_verification_tokens_regenerated_on_email_change(self):
        """Test that new verification tokens are generated when email changes"""
        # Get initial tokens
        user = User.objects.get(username='testuser')
        initial_token = user.member.email_verification_string
        initial_signed_token = user.member.email_verification_string_signed

        # Change email
        response = self.client.post('/user/update-my-information', data={
            'firstname': 'Test',
            'lastname': 'User',
            'email_address': 'newemail@test.com'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        # Verify tokens changed
        user.refresh_from_db()
        self.assertNotEqual(user.member.email_verification_string, initial_token,
                           'Plain token should change on email change')
        self.assertNotEqual(user.member.email_verification_string_signed, initial_signed_token,
                           'Signed token should change on email change')

        # Verify new tokens are valid (20 chars, not None)
        self.assertIsNotNone(user.member.email_verification_string)
        self.assertEqual(len(user.member.email_verification_string), 20)
        self.assertIn(':', user.member.email_verification_string_signed)
