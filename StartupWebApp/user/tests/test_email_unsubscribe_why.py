# Unit tests for email unsubscribe why (reasons) endpoint

import json

from django.test import TestCase
from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from clientevent.models import Configuration as ClientEventConfiguration
from order.models import Skutype, Skuinventory, Product, Sku, Skuprice, Productsku
from user.models import Termsofuse, Emailunsubscribereasons

from StartupWebApp.utilities import unittest_utilities


class EmailUnsubscribeWhyAPITest(PostgreSQLTestCase):

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

        # Generate unsubscribe token by updating communication preferences
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

        # Confirm unsubscribe so user is in unsubscribed state
        # (The "why" endpoint is shown after confirmation)
        self.client.post('/user/email-unsubscribe-confirm', data={
            'token': self.unsubscribe_token
        })

        # Refresh to get new token after confirmation
        self.member.refresh_from_db()
        self.unsubscribe_token = self.member.email_unsubscribe_string_signed

        # Logout so we can test token-based access (no authentication required)
        self.client.post('/user/logout')

    def test_valid_reasons_recorded_successfully(self):
        """Test that unsubscribe reasons are recorded when provided"""
        response = self.client.post('/user/email-unsubscribe-why', data={
            'token': self.unsubscribe_token,
            'no_longer_want_to_receive': 'true',
            'never_signed_up': 'false',
            'inappropriate': 'false',
            'spam': 'true',
            'other': 'Too many emails per week'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['email_unsubscribe_why'], 'success',
                         'Valid reasons submission should succeed')

        # Verify reasons were recorded in database
        reasons = Emailunsubscribereasons.objects.filter(member=self.member)
        self.assertEqual(reasons.count(), 1, 'Should have one reason record')

        reason = reasons.first()
        self.assertTrue(
            reason.no_longer_want_to_receive,
            'no_longer_want_to_receive should be True')
        self.assertFalse(reason.never_signed_up, 'never_signed_up should be False')
        self.assertFalse(reason.inappropriate, 'inappropriate should be False')
        self.assertTrue(reason.spam, 'spam should be True')
        self.assertEqual(
            reason.other,
            'Too many emails per week',
            'other reason should be recorded')
        self.assertIsNotNone(reason.created_date_time, 'created_date_time should be set')

    def test_invalid_tampered_token_rejected(self):
        """Test that invalid/tampered token is rejected"""
        response = self.client.post('/user/email-unsubscribe-why', data={
            'token': 'invalid_token_12345',
            'no_longer_want_to_receive': 'true',
            'never_signed_up': 'false',
            'inappropriate': 'false',
            'spam': 'false',
            'other': ''
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['email_unsubscribe_why'], 'error',
                         'Invalid token should return error')
        self.assertIn('errors', response_data, 'Should return error details')
        self.assertIn('error', response_data['errors'], 'Should have error field')

        # Verify NO reasons were recorded
        reasons = Emailunsubscribereasons.objects.filter(member=self.member)
        self.assertEqual(reasons.count(), 0, 'No reasons should be recorded for invalid token')

    def test_missing_token_rejected(self):
        """Test that request without token is rejected"""
        response = self.client.post('/user/email-unsubscribe-why', data={
            'no_longer_want_to_receive': 'true',
            'never_signed_up': 'false',
            'inappropriate': 'false',
            'spam': 'false',
            'other': ''
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['email_unsubscribe_why'], 'error',
                         'Missing token should return error')
        self.assertIn('errors', response_data, 'Should return error details')
        self.assertEqual(response_data['errors']['error'], 'token-required',
                         'Should indicate token is required')

    def test_all_reason_categories_recorded(self):
        """Test that all five reason categories can be recorded"""
        response = self.client.post('/user/email-unsubscribe-why', data={
            'token': self.unsubscribe_token,
            'no_longer_want_to_receive': 'true',
            'never_signed_up': 'true',
            'inappropriate': 'true',
            'spam': 'true',
            'other': 'Additional feedback here'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['email_unsubscribe_why'], 'success')

        # Verify all categories recorded
        reason = Emailunsubscribereasons.objects.get(member=self.member)
        self.assertTrue(reason.no_longer_want_to_receive, 'Category 1 should be recorded')
        self.assertTrue(reason.never_signed_up, 'Category 2 should be recorded')
        self.assertTrue(reason.inappropriate, 'Category 3 should be recorded')
        self.assertTrue(reason.spam, 'Category 4 should be recorded')
        self.assertEqual(reason.other, 'Additional feedback here', 'Category 5 should be recorded')

    def test_record_created_even_when_all_false(self):
        """Test that reason record is created even when all categories are false/empty"""
        response = self.client.post('/user/email-unsubscribe-why', data={
            'token': self.unsubscribe_token,
            'no_longer_want_to_receive': 'false',
            'never_signed_up': 'false',
            'inappropriate': 'false',
            'spam': 'false',
            'other': ''
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['email_unsubscribe_why'], 'success',
                         'Should succeed even with no reasons provided')

        # Verify record IS created (to track that user visited "why" page)
        reasons = Emailunsubscribereasons.objects.filter(member=self.member)
        self.assertEqual(reasons.count(), 1, 'Reason record should be created to track page visit')

        # Verify all flags are False
        reason = reasons.first()
        self.assertFalse(reason.no_longer_want_to_receive, 'Should be False')
        self.assertFalse(reason.never_signed_up, 'Should be False')
        self.assertFalse(reason.inappropriate, 'Should be False')
        self.assertFalse(reason.spam, 'Should be False')
        self.assertEqual(reason.other, '', 'Should be empty string')
