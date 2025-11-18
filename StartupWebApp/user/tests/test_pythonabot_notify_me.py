# Unit tests for pythonabot notify me endpoint

import json

from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from django.contrib.auth.models import Group

from clientevent.models import Configuration as ClientEventConfiguration
from order.models import Skutype, Skuinventory, Product, Sku, Skuprice, Productsku
from user.models import Termsofuse, Prospect

from StartupWebApp.utilities import unittest_utilities


class PythonabotNotifyMeAPITest(PostgreSQLTestCase):

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

    def test_valid_prospect_signup_succeeds(self):
        """Test that valid prospect signup succeeds and creates prospect record"""
        response = self.client.post('/user/pythonabot-notify-me', data={
            'email_address': 'newprospect@test.com',
            'how_excited': '5'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['pythonabot_notify_me'], 'success',
                         'Valid prospect signup should succeed')

        # Verify prospect was created
        prospect = Prospect.objects.get(email='newprospect@test.com')
        self.assertIsNotNone(prospect, 'Prospect should be created')
        self.assertTrue(prospect.email_unsubscribed,
                        'Prospect should have email_unsubscribed=True')
        self.assertIsNotNone(prospect.pr_cd, 'Prospect should have pr_cd')
        self.assertIsNotNone(prospect.email_unsubscribe_string,
                             'Prospect should have unsubscribe string')

    def test_duplicate_email_rejected(self):
        """Test that duplicate prospect email is rejected"""
        # Create initial prospect
        Prospect.objects.create(
            email='existing@test.com',
            email_unsubscribed=True,
            email_unsubscribe_string='test_string',
            email_unsubscribe_string_signed='test_signed',
            pr_cd='TEST123',
            created_date_time=timezone.now()
        )

        # Try to create duplicate
        response = self.client.post('/user/pythonabot-notify-me', data={
            'email_address': 'existing@test.com',
            'how_excited': '4'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['pythonabot_notify_me'], 'duplicate_prospect',
                         'Duplicate email should return duplicate_prospect error')
        self.assertIn('errors', response_data, 'Should return error details')
        self.assertIn('email_address', response_data['errors'],
                      'Should indicate email_address error')

        # Verify error has correct structure (list of error objects)
        email_errors = response_data['errors']['email_address']
        self.assertIsInstance(email_errors, list, 'Email errors should be a list')
        self.assertEqual(email_errors[0]['type'], 'duplicate',
                         'Error type should be duplicate')
        self.assertIn('already know', email_errors[0]['description'],
                      'Error description should mention duplicate')

    def test_invalid_email_rejected(self):
        """Test that invalid email is rejected with validation error"""
        response = self.client.post('/user/pythonabot-notify-me', data={
            'email_address': 'invalid-email',
            'how_excited': '3'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['pythonabot_notify_me'], 'validation_error',
                         'Invalid email should return validation error')
        self.assertIn('errors', response_data, 'Should return error details')
        self.assertIn('email_address', response_data['errors'],
                      'Should indicate email validation failed')

    def test_invalid_how_excited_rejected(self):
        """Test that invalid how_excited value is rejected with validation error"""
        # Test with invalid value (not 1-5)
        response = self.client.post('/user/pythonabot-notify-me', data={
            'email_address': 'test@example.com',
            'how_excited': '10'  # Should be 1-5
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['pythonabot_notify_me'], 'validation_error',
                         'Invalid how_excited should return validation error')
        self.assertIn('errors', response_data, 'Should return error details')
        self.assertIn('how_excited', response_data['errors'],
                      'Should indicate how_excited validation failed')

    def test_prospect_record_created_with_correct_data(self):
        """Test that prospect record is created with all correct fields"""
        response = self.client.post('/user/pythonabot-notify-me', data={
            'email_address': 'prospect@example.com',
            'how_excited': '4'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['pythonabot_notify_me'], 'success')

        # Verify all prospect fields
        prospect = Prospect.objects.get(email='prospect@example.com')
        self.assertEqual(prospect.email, 'prospect@example.com')
        self.assertTrue(prospect.email_unsubscribed,
                        'email_unsubscribed should be True')
        self.assertIsNotNone(prospect.email_unsubscribe_string,
                             'email_unsubscribe_string should be set')
        self.assertIsNotNone(prospect.email_unsubscribe_string_signed,
                             'email_unsubscribe_string_signed should be set')
        self.assertIsNotNone(prospect.pr_cd, 'pr_cd should be set')
        self.assertIsNotNone(prospect.created_date_time,
                             'created_date_time should be set')

        # Verify swa_comment
        self.assertEqual(
            prospect.swa_comment,
            'This prospect would like to be notified when PythonABot is ready to be purchased.',
            'swa_comment should have correct message')

        # Verify timestamp is recent
        time_diff = timezone.now() - prospect.created_date_time
        self.assertLess(time_diff.total_seconds(), 10,
                        'created_date_time should be recent')

    def test_excitement_rating_stored_in_prospect_comment(self):
        """Test that excitement rating is correctly stored in prospect_comment"""
        response = self.client.post('/user/pythonabot-notify-me', data={
            'email_address': 'excited@example.com',
            'how_excited': '5'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['pythonabot_notify_me'], 'success')

        # Verify excitement rating in prospect_comment
        prospect = Prospect.objects.get(email='excited@example.com')
        self.assertIn('5 on a scale of 1-5', prospect.prospect_comment,
                      'prospect_comment should contain excitement rating')
        self.assertIn('how excited', prospect.prospect_comment,
                      'prospect_comment should mention excitement')

        # Test with different excitement level
        self.client.post('/user/pythonabot-notify-me', data={
            'email_address': 'lessexcited@example.com',
            'how_excited': '2'
        })
        prospect2 = Prospect.objects.get(email='lessexcited@example.com')
        self.assertIn('2 on a scale of 1-5', prospect2.prospect_comment,
                      'prospect_comment should contain different excitement rating')
