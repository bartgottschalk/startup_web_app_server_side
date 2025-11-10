# Unit tests for email unsubscribe lookup endpoint

import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from clientevent.models import Configuration as ClientEventConfiguration
from order.models import Skutype, Skuinventory, Product, Sku, Skuprice, Productsku
from user.models import Termsofuse

from StartupWebApp.utilities import unittest_utilities


class EmailUnsubscribeLookupAPITest(TestCase):

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

        # Set email_unsubscribed back to False so we can test the lookup flow
        # (In real workflow, user gets email with token before clicking it)
        self.member.email_unsubscribed = False
        self.member.save()

        # Logout so we can test token-based access (no authentication required)
        self.client.post('/user/logout')

    def test_valid_token_returns_masked_email(self):
        """Test that valid unsubscribe token returns masked email address"""
        response = self.client.get(f'/user/email-unsubscribe-lookup?token={self.unsubscribe_token}')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['email_unsubscribe_lookup'], 'success',
                        'Valid token lookup should succeed')
        self.assertIn('email_address', response_data, 'Should return email address')

        # Verify email is masked (should contain asterisks)
        masked_email = response_data['email_address']
        self.assertIn('*', masked_email, 'Email should be masked with asterisks')
        self.assertIn('@', masked_email, 'Masked email should still contain @ symbol')

    def test_invalid_tampered_token_rejected(self):
        """Test that invalid/tampered token is rejected"""
        response = self.client.get('/user/email-unsubscribe-lookup?token=invalid_token_12345')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['email_unsubscribe_lookup'], 'error',
                        'Invalid token should return error')
        self.assertIn('errors', response_data, 'Should return error details')
        # Could be 'token-altered' or 'member-not-found' depending on token format
        self.assertIn('error', response_data['errors'], 'Should have error field')

    def test_already_unsubscribed_user_shows_error(self):
        """Test that already unsubscribed user receives appropriate error"""
        # Set user as already unsubscribed
        self.member.email_unsubscribed = True
        self.member.save()

        response = self.client.get(f'/user/email-unsubscribe-lookup?token={self.unsubscribe_token}')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['email_unsubscribe_lookup'], 'error',
                        'Already unsubscribed should return error')
        self.assertIn('errors', response_data, 'Should return error details')
        self.assertEqual(response_data['errors']['error'], 'email-address-already-unsubscribed',
                        'Should indicate email already unsubscribed')

    def test_missing_token_rejected(self):
        """Test that request without token is rejected"""
        response = self.client.get('/user/email-unsubscribe-lookup')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['email_unsubscribe_lookup'], 'error',
                        'Missing token should return error')
        self.assertIn('errors', response_data, 'Should return error details')
        self.assertEqual(response_data['errors']['error'], 'token-required',
                        'Should indicate token is required')

    def test_nonexistent_member_token_rejected(self):
        """Test that token for non-existent member is rejected"""
        # Use a token that's properly formatted but doesn't exist in database
        fake_token = 'abcdef123456'  # Valid format but not in database

        response = self.client.get(f'/user/email-unsubscribe-lookup?token={fake_token}')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['email_unsubscribe_lookup'], 'error',
                        'Non-existent member token should return error')
        self.assertIn('errors', response_data, 'Should return error details')
        self.assertEqual(response_data['errors']['error'], 'member-not-found',
                        'Should indicate member not found')
