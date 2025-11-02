# Unit tests for update communication preferences endpoint

import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from clientevent.models import Configuration as ClientEventConfiguration
from order.models import Skutype, Skuinventory, Product, Sku, Skuprice, Productsku
from user.models import Member, Termsofuse, Emailunsubscribereasons

from StartupWebApp.utilities import unittest_utilities


class UpdateCommunicationPreferencesAPITest(TestCase):

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

    def test_valid_newsletter_subscription_update(self):
        """Test successful newsletter subscription update"""
        # Subscribe to newsletter
        response = self.client.post('/user/update-communication-preferences', data={
            'newsletter': 'true',
            'email_unsubscribe': 'false',
            'no_longer_want_to_receive': 'false',
            'never_signed_up': 'false',
            'inappropriate': 'false',
            'spam': 'false',
            'other': ''
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                            '{"update_communication_preferences": "success", "user-api-version": "0.0.1"}',
                            'Valid newsletter subscription should succeed')

        # Verify member preferences were updated
        user = User.objects.get(username='testuser')
        self.assertTrue(user.member.newsletter_subscriber, 'Newsletter subscriber should be True')
        self.assertFalse(user.member.email_unsubscribed, 'Email unsubscribed should be False')

    def test_valid_email_unsubscribe_with_reasons(self):
        """Test successful email unsubscribe with reasons tracking"""
        response = self.client.post('/user/update-communication-preferences', data={
            'newsletter': 'false',
            'email_unsubscribe': 'true',
            'no_longer_want_to_receive': 'true',
            'never_signed_up': 'false',
            'inappropriate': 'false',
            'spam': 'true',
            'other': 'Too many emails'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                            '{"update_communication_preferences": "success", "user-api-version": "0.0.1"}',
                            'Valid unsubscribe should succeed')

        # Verify member preferences were updated
        user = User.objects.get(username='testuser')
        self.assertFalse(user.member.newsletter_subscriber, 'Newsletter subscriber should be False')
        self.assertTrue(user.member.email_unsubscribed, 'Email unsubscribed should be True')

        # Verify unsubscribe reasons were recorded
        reasons = Emailunsubscribereasons.objects.filter(member=user.member)
        self.assertEqual(reasons.count(), 1, 'Unsubscribe reason should be recorded')
        reason = reasons.first()
        self.assertTrue(reason.no_longer_want_to_receive, 'No longer want to receive should be True')
        self.assertFalse(reason.never_signed_up, 'Never signed up should be False')
        self.assertFalse(reason.inappropriate, 'Inappropriate should be False')
        self.assertTrue(reason.spam, 'Spam should be True')
        self.assertEqual(reason.other, 'Too many emails', 'Other reason should be recorded')

    def test_cannot_enable_both_newsletter_and_unsubscribe(self):
        """Test that enabling both newsletter and unsubscribe is rejected"""
        response = self.client.post('/user/update-communication-preferences', data={
            'newsletter': 'true',
            'email_unsubscribe': 'true',  # Conflicting
            'no_longer_want_to_receive': 'false',
            'never_signed_up': 'false',
            'inappropriate': 'false',
            'spam': 'false',
            'other': ''
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['update_communication_preferences'], 'errors',
                        'Conflicting preferences should be rejected')
        self.assertIn('errors', response_data, 'Should return error messages')
        self.assertIn('invalid_data', response_data['errors'], 'Should have invalid_data error')

        # Verify member preferences were NOT updated
        user = User.objects.get(username='testuser')
        self.assertFalse(user.member.newsletter_subscriber, 'Newsletter subscriber should remain False')
        self.assertFalse(user.member.email_unsubscribed, 'Email unsubscribed should remain False')

    def test_unsubscribe_token_regenerated_when_flag_changes(self):
        """Test that unsubscribe token is regenerated when email_unsubscribed changes"""
        # Get initial unsubscribe tokens
        user = User.objects.get(username='testuser')
        initial_token = user.member.email_unsubscribe_string
        initial_signed_token = user.member.email_unsubscribe_string_signed

        # Change email_unsubscribed to True
        response = self.client.post('/user/update-communication-preferences', data={
            'newsletter': 'false',
            'email_unsubscribe': 'true',
            'no_longer_want_to_receive': 'true',
            'never_signed_up': 'false',
            'inappropriate': 'false',
            'spam': 'false',
            'other': ''
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        # Verify tokens changed
        user.refresh_from_db()
        self.assertNotEqual(user.member.email_unsubscribe_string, initial_token,
                           'Unsubscribe token should change when flag changes')
        self.assertNotEqual(user.member.email_unsubscribe_string_signed, initial_signed_token,
                           'Signed unsubscribe token should change when flag changes')

        # Verify new tokens are not None
        self.assertIsNotNone(user.member.email_unsubscribe_string)
        self.assertIsNotNone(user.member.email_unsubscribe_string_signed)

    def test_unauthenticated_user_rejected(self):
        """Test that unauthenticated user cannot update communication preferences"""
        # Logout first
        self.client.post('/user/logout')

        response = self.client.post('/user/update-communication-preferences', data={
            'newsletter': 'true',
            'email_unsubscribe': 'false',
            'no_longer_want_to_receive': 'false',
            'never_signed_up': 'false',
            'inappropriate': 'false',
            'spam': 'false',
            'other': ''
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                            '{"update_communication_preferences": "user_not_authenticated", "user-api-version": "0.0.1"}',
                            'Unauthenticated user should be rejected')

    def test_missing_required_data_rejected(self):
        """Test that request with missing required data is rejected"""
        # Missing 'email_unsubscribe' parameter
        response = self.client.post('/user/update-communication-preferences', data={
            'newsletter': 'true',
            # 'email_unsubscribe' missing
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['update_communication_preferences'], 'errors',
                        'Missing required data should be rejected')
        self.assertIn('errors', response_data, 'Should return error messages')
        self.assertIn('data_missing', response_data['errors'], 'Should have data_missing error')

    def test_unsubscribe_reasons_not_recorded_when_all_false(self):
        """Test that unsubscribe reasons are not recorded when all are false/empty"""
        response = self.client.post('/user/update-communication-preferences', data={
            'newsletter': 'false',
            'email_unsubscribe': 'true',
            'no_longer_want_to_receive': 'false',
            'never_signed_up': 'false',
            'inappropriate': 'false',
            'spam': 'false',
            'other': ''  # Empty
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        # Verify NO unsubscribe reasons were recorded (all false/empty)
        user = User.objects.get(username='testuser')
        reasons = Emailunsubscribereasons.objects.filter(member=user.member)
        self.assertEqual(reasons.count(), 0, 'No reasons should be recorded when all are false/empty')
