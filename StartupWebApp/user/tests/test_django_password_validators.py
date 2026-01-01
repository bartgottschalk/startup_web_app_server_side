# Unit tests for Django password validators (AUTH_PASSWORD_VALIDATORS)
# Tests enforcement of UserAttributeSimilarityValidator and CommonPasswordValidator

import json

from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from clientevent.models import Configuration as ClientEventConfiguration
from order.models import Skutype, Skuinventory, Product, Sku, Skuprice, Productsku
from user.models import Termsofuse

from StartupWebApp.utilities import unittest_utilities


class DjangoPasswordValidatorCreateAccountTest(PostgreSQLTestCase):
    """Test Django password validators on create_account endpoint"""

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

    def test_create_account_password_similar_to_username(self):
        """Test that password similar to username is rejected by Django UserAttributeSimilarityValidator"""
        response = self.client.post('/user/create-account', data={
            'firstname': 'Test',
            'lastname': 'User',
            'username': 'testuser',
            'email_address': 'testuser@example.com',
            'password': 'Testuser123!',  # Similar to username "testuser"
            'confirm_password': 'Testuser123!',
            'newsletter': 'false',
            'remember_me': 'false'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        response_data = json.loads(response.content.decode('utf8'))

        # Should return errors (create_account returns 'false' on validation errors)
        self.assertEqual(
            response_data['create_account'],
            'false',
            'Password similar to username should be rejected')
        self.assertIn('errors', response_data, 'Should return error messages')
        self.assertIn('password', response_data['errors'], 'Should have password error')

        # Verify the error message mentions username similarity
        password_errors = response_data['errors']['password']
        self.assertTrue(
            any('similar' in error['description'].lower() and 'username' in error['description'].lower()
                for error in password_errors),
            'Error should mention password similarity to username')

        # Verify user was NOT created
        self.assertEqual(User.objects.filter(username='testuser').count(), 0,
                         'User should not be created with invalid password')

    def test_create_account_common_password(self):
        """Test that common password is rejected by Django CommonPasswordValidator"""
        response = self.client.post('/user/create-account', data={
            'firstname': 'Test',
            'lastname': 'User',
            'username': 'uniqueuser123',
            'email_address': 'uniqueuser@example.com',
            'password': 'Password1!',  # Contains "password" which is too common
            'confirm_password': 'Password1!',
            'newsletter': 'false',
            'remember_me': 'false'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        response_data = json.loads(response.content.decode('utf8'))

        # Should return errors (create_account returns 'false' on validation errors)
        self.assertEqual(
            response_data['create_account'],
            'false',
            'Common password should be rejected')
        self.assertIn('errors', response_data, 'Should return error messages')
        self.assertIn('password', response_data['errors'], 'Should have password error')

        # Verify the error message mentions common password
        password_errors = response_data['errors']['password']
        self.assertTrue(
            any('common' in error['description'].lower()
                for error in password_errors),
            'Error should mention common password')

        # Verify user was NOT created
        self.assertEqual(User.objects.filter(username='uniqueuser123').count(), 0,
                         'User should not be created with common password')


class DjangoPasswordValidatorSetNewPasswordTest(PostgreSQLTestCase):
    """Test Django password validators on set_new_password endpoint (password reset flow)"""

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

        # Create a test user
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
        self.client.post('/user/logout')

        # Request password reset to generate token
        self.client.post('/user/reset-password', data={
            'username': 'testuser',
            'email_address': 'testuser@test.com'
        })

        # Get the generated token
        user = User.objects.get(username='testuser')
        self.member = user.member
        self.reset_token = self.member.reset_password_string
        self.reset_token_signed = self.member.reset_password_string_signed

    def test_set_new_password_similar_to_username(self):
        """Test that password similar to username is rejected in password reset flow"""
        response = self.client.post('/user/set-new-password', data={
            'username': 'testuser',
            'password_reset_code': self.reset_token_signed,
            'new_password': 'Testuser456!',  # Similar to username "testuser"
            'confirm_new_password': 'Testuser456!'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        response_data = json.loads(response.content.decode('utf8'))

        # Should return errors (set_new_password returns 'password-error' on validation errors)
        self.assertEqual(
            response_data['set_new_password'],
            'password-error',
            'Password similar to username should be rejected in reset flow')
        self.assertIn('errors', response_data, 'Should return error messages')
        self.assertIn('new-password', response_data['errors'], 'Should have new-password error')

        # Verify the error message mentions username similarity
        password_errors = response_data['errors']['new-password']
        self.assertTrue(
            any('similar' in error['description'].lower() and 'username' in error['description'].lower()
                for error in password_errors),
            'Error should mention password similarity to username')

        # Verify password was NOT changed
        user = User.objects.get(username='testuser')
        self.assertTrue(user.check_password('ValidPass1!'), 'Password should still be old password')


class DjangoPasswordValidatorChangePasswordTest(PostgreSQLTestCase):
    """Test Django password validators on change_my_password endpoint"""

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

    def test_change_password_similar_to_username(self):
        """Test that password similar to username is rejected in password change flow"""
        response = self.client.post('/user/change-my-password', data={
            'current_password': 'ValidPass1!',
            'new_password': 'Testuser789!',  # Similar to username "testuser"
            'confirm_new_password': 'Testuser789!'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        response_data = json.loads(response.content.decode('utf8'))

        # Should return errors
        self.assertEqual(
            response_data['change_my_password'],
            'errors',
            'Password similar to username should be rejected in change password flow')
        self.assertIn('errors', response_data, 'Should return error messages')
        self.assertIn('password', response_data['errors'], 'Should have password error')

        # Verify the error message mentions username similarity
        password_errors = response_data['errors']['password']
        self.assertTrue(
            any('similar' in error['description'].lower() and 'username' in error['description'].lower()
                for error in password_errors),
            'Error should mention password similarity to username')

        # Verify password was NOT changed
        user = User.objects.get(username='testuser')
        self.assertTrue(user.check_password('ValidPass1!'), 'Password should still be old password')
