# Unit tests for change my password endpoint

import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.core import mail

from clientevent.models import Configuration as ClientEventConfiguration
from order.models import Skutype, Skuinventory, Product, Sku, Skuprice, Productsku
from user.models import Termsofuse

from StartupWebApp.utilities import unittest_utilities


class ChangeMyPasswordAPITest(TestCase):

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

    def test_valid_password_change(self):
        """Test successful password change for authenticated user"""
        response = self.client.post('/user/change-my-password', data={
            'current_password': 'ValidPass1!',
            'new_password': 'NewValidPass2!',
            'confirm_new_password': 'NewValidPass2!'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                             '{"change_my_password": "success", "user-api-version": "0.0.1"}',
                             'Valid password change should succeed')

        # Verify password was changed
        user = User.objects.get(username='testuser')
        self.assertTrue(
            user.check_password('NewValidPass2!'),
            'Password should be changed to new password')

        # Verify confirmation email was sent
        self.assertEqual(len(mail.outbox), 1, 'Password change confirmation email should be sent')
        self.assertIn(
            'password',
            mail.outbox[0].subject.lower(),
            'Email subject should mention password')

        # Verify user is still logged in after password change
        response = self.client.get('/user/logged-in')
        response_data = json.loads(response.content.decode('utf8'))
        self.assertTrue(response_data['logged_in'],
                        'User should still be logged in after password change')

    def test_unauthenticated_user(self):
        """Test that unauthenticated user cannot change password"""
        # Logout first
        self.client.post('/user/logout')

        response = self.client.post('/user/change-my-password', data={
            'current_password': 'ValidPass1!',
            'new_password': 'NewValidPass2!',
            'confirm_new_password': 'NewValidPass2!'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(
            response.content.decode('utf8'),
            '{"change_my_password": "user_not_authenticated", "user-api-version": "0.0.1"}',
            'Unauthenticated user should not be able to change password')

    def test_incorrect_current_password(self):
        """Test that incorrect current password is rejected"""
        response = self.client.post('/user/change-my-password', data={
            'current_password': 'WrongPassword!',
            'new_password': 'NewValidPass2!',
            'confirm_new_password': 'NewValidPass2!'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(
            response_data['change_my_password'],
            'errors',
            'Incorrect current password should fail')
        self.assertIn('errors', response_data, 'Should return error messages')
        self.assertIn(
            'current-password',
            response_data['errors'],
            'Should have current-password error')

        # Verify password was NOT changed
        user = User.objects.get(username='testuser')
        self.assertTrue(user.check_password('ValidPass1!'), 'Password should still be old password')

    def test_weak_new_password(self):
        """Test that weak new password is rejected"""
        response = self.client.post('/user/change-my-password', data={
            'current_password': 'ValidPass1!',
            'new_password': 'weak',
            'confirm_new_password': 'weak'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(
            response_data['change_my_password'],
            'errors',
            'Weak new password should be rejected')
        self.assertIn('errors', response_data, 'Should return error messages')

        # Verify password was NOT changed
        user = User.objects.get(username='testuser')
        self.assertTrue(user.check_password('ValidPass1!'), 'Password should still be old password')

    def test_password_mismatch(self):
        """Test that mismatched new passwords are rejected"""
        response = self.client.post('/user/change-my-password', data={
            'current_password': 'ValidPass1!',
            'new_password': 'NewValidPass2!',
            'confirm_new_password': 'DifferentPass3!'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(
            response_data['change_my_password'],
            'errors',
            'Mismatched passwords should be rejected')

        # Verify password was NOT changed
        user = User.objects.get(username='testuser')
        self.assertTrue(user.check_password('ValidPass1!'), 'Password should still be old password')

    def test_new_password_same_as_current(self):
        """Test that new password cannot be the same as current password"""
        response = self.client.post('/user/change-my-password', data={
            'current_password': 'ValidPass1!',
            'new_password': 'ValidPass1!',  # Same as current
            'confirm_new_password': 'ValidPass1!'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['change_my_password'], 'errors',
                         'New password same as current should be rejected')
        self.assertIn('errors', response_data, 'Should return error messages')
        self.assertIn('password', response_data['errors'], 'Should have password error')

    def test_login_with_new_password(self):
        """Test that user can login with new password and old password no longer works"""
        # Change password
        response = self.client.post('/user/change-my-password', data={
            'current_password': 'ValidPass1!',
            'new_password': 'NewValidPass2!',
            'confirm_new_password': 'NewValidPass2!'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        # Logout
        self.client.post('/user/logout')

        # Try to login with new password
        response = self.client.post('/user/login', data={
            'username': 'testuser',
            'password': 'NewValidPass2!',
            'remember_me': 'false'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                             '{"login": "true", "user-api-version": "0.0.1"}',
                             'User should be able to login with new password')

        # Logout and try old password (should fail)
        self.client.post('/user/logout')
        response = self.client.post('/user/login', data={
            'username': 'testuser',
            'password': 'ValidPass1!',  # Old password
            'remember_me': 'false'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                             '{"login": "false", "user-api-version": "0.0.1"}',
                             'Old password should no longer work')
