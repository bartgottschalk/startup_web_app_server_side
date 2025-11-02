# Unit tests for email unsubscribe confirmation endpoint

import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from clientevent.models import Configuration as ClientEventConfiguration
from order.models import Skutype, Skuinventory, Product, Sku, Skuprice, Productsku
from user.models import Member, Termsofuse

from StartupWebApp.utilities import unittest_utilities


class EmailUnsubscribeConfirmAPITest(TestCase):

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
            'newsletter': 'true',  # Start with newsletter enabled
            'remember_me': 'false'
        })
        # User should be automatically logged in after account creation

        # Generate unsubscribe token by updating communication preferences
        # This will set email_unsubscribed to True and generate a token
        self.client.post('/user/update-communication-preferences', data={
            'newsletter': 'false',
            'email_unsubscribe': 'true',
            'no_longer_want_to_receive': 'false',
            'never_signed_up': 'false',
            'inappropriate': 'false',
            'spam': 'false',
            'other': ''
        })

        # Get the generated unsubscribe token
        user = User.objects.get(username='testuser')
        self.member = user.member
        self.unsubscribe_token = self.member.email_unsubscribe_string_signed

        # Set email_unsubscribed back to False so we can test the confirm flow
        # (In real workflow, user clicks lookup, then clicks confirm)
        self.member.email_unsubscribed = False
        self.member.save()

        # Logout so we can test token-based access (no authentication required)
        self.client.post('/user/logout')

    def test_valid_token_confirms_unsubscribe(self):
        """Test that valid token confirms unsubscribe and sets flags correctly"""
        response = self.client.post('/user/email-unsubscribe-confirm', data={
            'token': self.unsubscribe_token
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['email_unsubscribe_confirm'], 'success',
                        'Valid token confirmation should succeed')
        self.assertIn('email_address', response_data, 'Should return masked email address')
        self.assertIn('token', response_data, 'Should return new token')

        # Verify masked email format
        masked_email = response_data['email_address']
        self.assertIn('*', masked_email, 'Email should be masked')
        self.assertIn('@', masked_email, 'Masked email should contain @ symbol')

        # Verify new token was generated
        new_token = response_data['token']
        self.assertIsNotNone(new_token, 'New token should be generated')
        self.assertNotEqual(new_token, self.unsubscribe_token, 'New token should differ from old token')

        # Verify member flags were updated
        self.member.refresh_from_db()
        self.assertTrue(self.member.email_unsubscribed, 'email_unsubscribed should be True')
        self.assertFalse(self.member.newsletter_subscriber, 'newsletter_subscriber should be False')

    def test_invalid_tampered_token_rejected(self):
        """Test that invalid/tampered token is rejected"""
        response = self.client.post('/user/email-unsubscribe-confirm', data={
            'token': 'invalid_token_12345'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['email_unsubscribe_confirm'], 'error',
                        'Invalid token should return error')
        self.assertIn('errors', response_data, 'Should return error details')
        self.assertIn('error', response_data['errors'], 'Should have error field')

        # Verify member flags were NOT updated
        self.member.refresh_from_db()
        self.assertFalse(self.member.email_unsubscribed, 'email_unsubscribed should remain False')

    def test_already_unsubscribed_user_shows_error(self):
        """Test that already unsubscribed user receives appropriate error"""
        # Set user as already unsubscribed
        self.member.email_unsubscribed = True
        self.member.save()

        response = self.client.post('/user/email-unsubscribe-confirm', data={
            'token': self.unsubscribe_token
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['email_unsubscribe_confirm'], 'error',
                        'Already unsubscribed should return error')
        self.assertIn('errors', response_data, 'Should return error details')
        self.assertEqual(response_data['errors']['error'], 'email-address-already-unsubscribed',
                        'Should indicate email already unsubscribed')

    def test_missing_token_rejected(self):
        """Test that request without token is rejected"""
        response = self.client.post('/user/email-unsubscribe-confirm', data={})
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['email_unsubscribe_confirm'], 'error',
                        'Missing token should return error')
        self.assertIn('errors', response_data, 'Should return error details')
        self.assertEqual(response_data['errors']['error'], 'token-required',
                        'Should indicate token is required')

    def test_newsletter_flag_disabled_for_members(self):
        """Test that newsletter_subscriber flag is disabled when Member unsubscribes"""
        # Verify newsletter is initially enabled (set in setUp)
        self.member.refresh_from_db()
        # Note: newsletter might be False from the update-communication-preferences call
        # Let's explicitly set it to True to test this behavior
        self.member.newsletter_subscriber = True
        self.member.save()

        # Confirm unsubscribe
        response = self.client.post('/user/email-unsubscribe-confirm', data={
            'token': self.unsubscribe_token
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['email_unsubscribe_confirm'], 'success')

        # Verify newsletter_subscriber was disabled
        self.member.refresh_from_db()
        self.assertFalse(self.member.newsletter_subscriber,
                        'newsletter_subscriber should be disabled for Members')

    def test_token_regenerated_after_confirmation(self):
        """Test that new unsubscribe token is generated after confirmation"""
        # Store initial tokens
        initial_token = self.member.email_unsubscribe_string
        initial_signed_token = self.member.email_unsubscribe_string_signed

        # Confirm unsubscribe
        response = self.client.post('/user/email-unsubscribe-confirm', data={
            'token': self.unsubscribe_token
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['email_unsubscribe_confirm'], 'success')

        # Verify tokens changed
        self.member.refresh_from_db()
        self.assertNotEqual(self.member.email_unsubscribe_string, initial_token,
                           'Plain token should change after confirmation')
        self.assertNotEqual(self.member.email_unsubscribe_string_signed, initial_signed_token,
                           'Signed token should change after confirmation')

        # Verify new tokens are valid (not None)
        self.assertIsNotNone(self.member.email_unsubscribe_string)
        self.assertIsNotNone(self.member.email_unsubscribe_string_signed)

        # Verify response includes new token
        self.assertIn('token', response_data)
        self.assertEqual(response_data['token'], self.member.email_unsubscribe_string_signed,
                        'Response should return new signed token')
