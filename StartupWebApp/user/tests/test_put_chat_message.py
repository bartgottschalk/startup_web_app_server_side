# Unit tests for put chat message endpoint

import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from clientevent.models import Configuration as ClientEventConfiguration
from order.models import Skutype, Skuinventory, Product, Sku, Skuprice, Productsku
from user.models import Member, Termsofuse, Chatmessage, Prospect

from StartupWebApp.utilities import unittest_utilities


class PutChatMessageAPITest(TestCase):

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

    def test_authenticated_user_submits_chat_message(self):
        """Test that authenticated user's chat message is linked to their member account"""
        # Create and login a user
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
        user = User.objects.get(username='testuser')

        response = self.client.post('/user/put-chat-message', data={
            'name': 'Test User',
            'email_address': 'testuser@test.com',
            'message': 'This is a test chat message from an authenticated user.'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        # Note: Response is 'true' (string) or 'email_failed' if email send fails
        self.assertIn(response_data['put_chat_message'], ['true', 'email_failed'],
                     'Chat message submission should succeed or fail email send')

        # Verify chat message was created and linked to member
        chat_message = Chatmessage.objects.get(email_address='testuser@test.com')
        self.assertEqual(chat_message.member.id, user.member.id,
                        'Chat message should be linked to authenticated user member')
        self.assertIsNone(chat_message.prospect,
                         'Chat message should not be linked to prospect')
        self.assertEqual(chat_message.name, 'Test User')
        self.assertEqual(chat_message.message, 'This is a test chat message from an authenticated user.')

    def test_anonymous_user_with_existing_user_email(self):
        """Test that anonymous user submitting chat with existing user email links to that user"""
        # Create a user
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
        user = User.objects.get(username='testuser')

        # Logout to become anonymous
        self.client.post('/user/logout')

        # Submit chat message as anonymous user with existing user's email
        response = self.client.post('/user/put-chat-message', data={
            'name': 'Test User',
            'email_address': 'testuser@test.com',
            'message': 'Anonymous submission with existing user email.'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertIn(response_data['put_chat_message'], ['true', 'email_failed'])

        # Verify chat message was linked to existing user's member
        chat_message = Chatmessage.objects.get(message='Anonymous submission with existing user email.')
        self.assertEqual(chat_message.member.id, user.member.id,
                        'Chat message should be linked to existing user member')
        self.assertIsNone(chat_message.prospect,
                         'Chat message should not be linked to prospect')

    def test_anonymous_user_with_existing_prospect_email(self):
        """Test that anonymous user submitting chat with existing prospect email links to that prospect"""
        # Create a prospect
        prospect = Prospect.objects.create(
            email='prospect@test.com',
            email_unsubscribed=True,
            email_unsubscribe_string='test_string',
            email_unsubscribe_string_signed='test_signed',
            pr_cd='TEST123',
            created_date_time=timezone.now()
        )

        # Submit chat message as anonymous user with existing prospect email
        response = self.client.post('/user/put-chat-message', data={
            'name': 'Prospect User',
            'email_address': 'prospect@test.com',
            'message': 'Chat from existing prospect.'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertIn(response_data['put_chat_message'], ['true', 'email_failed'])

        # Verify chat message was linked to existing prospect
        chat_message = Chatmessage.objects.get(message='Chat from existing prospect.')
        self.assertIsNone(chat_message.member,
                         'Chat message should not be linked to member')
        self.assertEqual(chat_message.prospect.id, prospect.id,
                        'Chat message should be linked to existing prospect')

    def test_anonymous_user_with_new_email_creates_prospect(self):
        """Test that anonymous user with new email creates new prospect and links chat"""
        response = self.client.post('/user/put-chat-message', data={
            'name': 'New User',
            'email_address': 'newuser@test.com',
            'message': 'Chat from completely new user.'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertIn(response_data['put_chat_message'], ['true', 'email_failed'])

        # Verify new prospect was created
        prospect = Prospect.objects.get(email='newuser@test.com')
        self.assertIsNotNone(prospect, 'New prospect should be created')
        self.assertTrue(prospect.email_unsubscribed,
                       'New prospect should have email_unsubscribed=True')
        self.assertIn('Captured from chat message submission', prospect.swa_comment,
                     'Prospect should have correct swa_comment')
        self.assertIsNotNone(prospect.pr_cd, 'Prospect should have pr_cd')
        self.assertIsNotNone(prospect.email_unsubscribe_string,
                            'Prospect should have unsubscribe string')

        # Verify chat message was linked to new prospect
        chat_message = Chatmessage.objects.get(message='Chat from completely new user.')
        self.assertIsNone(chat_message.member,
                         'Chat message should not be linked to member')
        self.assertEqual(chat_message.prospect.id, prospect.id,
                        'Chat message should be linked to new prospect')

    def test_valid_chat_message_creates_record(self):
        """Test that valid chat message creates Chatmessage record with correct data"""
        response = self.client.post('/user/put-chat-message', data={
            'name': 'Test Name',
            'email_address': 'test@example.com',
            'message': 'This is a test message with valid data.'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        # Verify Chatmessage record exists with correct data
        chat_message = Chatmessage.objects.get(email_address='test@example.com')
        self.assertEqual(chat_message.name, 'Test Name')
        self.assertEqual(chat_message.email_address, 'test@example.com')
        self.assertEqual(chat_message.message, 'This is a test message with valid data.')
        self.assertIsNotNone(chat_message.created_date_time,
                            'created_date_time should be set')

        # Verify timestamp is recent (within last 10 seconds)
        time_diff = timezone.now() - chat_message.created_date_time
        self.assertLess(time_diff.total_seconds(), 10,
                       'created_date_time should be recent')

    def test_invalid_name_rejected(self):
        """Test that invalid name is rejected with validation error"""
        # Name too long (over 30 characters)
        response = self.client.post('/user/put-chat-message', data={
            'name': 'A' * 31,  # 31 characters, max is 30
            'email_address': 'test@example.com',
            'message': 'Test message'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['put_chat_message'], 'validation_error',
                        'Invalid name should return validation error')
        self.assertIn('errors', response_data, 'Should return error details')
        self.assertIn('name', response_data['errors'],
                     'Should indicate name validation failed')

    def test_invalid_email_rejected(self):
        """Test that invalid email is rejected with validation error"""
        response = self.client.post('/user/put-chat-message', data={
            'name': 'Test Name',
            'email_address': 'invalid-email',
            'message': 'Test message'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['put_chat_message'], 'validation_error',
                        'Invalid email should return validation error')
        self.assertIn('errors', response_data, 'Should return error details')
        self.assertIn('email_address', response_data['errors'],
                     'Should indicate email validation failed')

    def test_invalid_message_rejected(self):
        """Test that invalid message is rejected with validation error"""
        # Message too long (over 5000 characters)
        response = self.client.post('/user/put-chat-message', data={
            'name': 'Test Name',
            'email_address': 'test@example.com',
            'message': 'A' * 5001  # 5001 characters, max is 5000
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['put_chat_message'], 'validation_error',
                        'Invalid message should return validation error')
        self.assertIn('errors', response_data, 'Should return error details')
        self.assertIn('message', response_data['errors'],
                     'Should indicate message validation failed')
