# Unit tests for terms of use agree check endpoint

import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from clientevent.models import Configuration as ClientEventConfiguration
from order.models import Skutype, Skuinventory, Product, Sku, Skuprice, Productsku
from user.models import Termsofuse

from StartupWebApp.utilities import unittest_utilities


class TermsOfUseAgreeCheckAPITest(TestCase):

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

        # Create TOS version 1 (will be used as "old" version in some tests)
        self.tos_v1 = Termsofuse.objects.create(version=1, version_note='Initial Terms', publication_date_time=timezone.now())

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
        self.user = User.objects.get(username='testuser')

    def test_user_agreed_to_latest_tos_returns_true(self):
        """Test that user who agreed to latest TOS receives True response"""
        # User automatically agreed to v1 during account creation (latest version at that time)
        # No need to create agreement manually - it's already there

        response = self.client.get('/user/terms-of-use-agree-check')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertTrue(response_data['terms_of_use_agree_check'],
                       'User who agreed to latest TOS should receive True')

    def test_user_not_agreed_returns_false_with_version_info(self):
        """Test that user who has not agreed to TOS receives False with version details"""
        # User agreed to v1 during registration, but now create v2 after registration
        # User has NOT agreed to v2 yet
        tos_v2 = Termsofuse.objects.create(
            version=2,
            version_note='Updated Terms',
            publication_date_time=timezone.now()
        )

        response = self.client.get('/user/terms-of-use-agree-check')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertFalse(response_data['terms_of_use_agree_check'],
                        'User who has not agreed should receive False')
        self.assertIn('version', response_data, 'Should include version number')
        self.assertIn('version_note', response_data, 'Should include version note')
        self.assertEqual(response_data['version'], 2, 'Should return version 2')
        self.assertEqual(response_data['version_note'], 'Updated Terms',
                        'Should return correct version note')

    def test_user_agreed_to_old_version_returns_false(self):
        """Test that user who agreed to old TOS version receives False when new version exists"""
        # User already agreed to v1 during account creation
        # Now create v2 - user should need to agree to this new version
        tos_v2 = Termsofuse.objects.create(
            version=2,
            version_note='Updated Terms',
            publication_date_time=timezone.now()
        )

        response = self.client.get('/user/terms-of-use-agree-check')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertFalse(response_data['terms_of_use_agree_check'],
                        'User who agreed to old version should receive False')
        self.assertEqual(response_data['version'], 2,
                        'Should return latest version (2)')
        self.assertEqual(response_data['version_note'], 'Updated Terms',
                        'Should return latest version note')

    def test_anonymous_user_fails(self):
        """Test that anonymous user cannot check TOS agreement status"""
        # Logout to become anonymous
        self.client.post('/user/logout')

        # This will cause an AttributeError since anonymous user has no .member attribute
        # The endpoint doesn't handle this gracefully, so it raises an exception
        with self.assertRaises(AttributeError) as context:
            self.client.get('/user/terms-of-use-agree-check')

        # Verify it's the expected error
        self.assertIn('AnonymousUser', str(context.exception),
                     'Should be AnonymousUser attribute error')
