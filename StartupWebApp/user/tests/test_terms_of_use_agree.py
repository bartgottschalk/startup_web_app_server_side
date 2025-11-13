# Unit tests for terms of use agree endpoint

import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from clientevent.models import Configuration as ClientEventConfiguration
from order.models import Skutype, Skuinventory, Product, Sku, Skuprice, Productsku
from user.models import Termsofuse, Membertermsofuseversionagreed

from StartupWebApp.utilities import unittest_utilities


class TermsOfUseAgreeAPITest(TestCase):

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

        # Create TOS version 1 (will be used during registration)
        self.tos_v1 = Termsofuse.objects.create(
            version=1,
            version_note='Initial Terms',
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
        # User also automatically agreed to TOS v1 during registration
        self.user = User.objects.get(username='testuser')

    def test_valid_agreement_to_latest_tos_succeeds(self):
        """Test that agreeing to latest TOS version succeeds"""
        # Create TOS version 2 AFTER registration (user hasn't agreed to it yet)
        tos_v2 = Termsofuse.objects.create(
            version=2,
            version_note='Updated Terms',
            publication_date_time=timezone.now()
        )

        response = self.client.post('/user/terms-of-use-agree', data={
            'version': '2'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['terms_of_use_agree'], 'success',
                         'Valid agreement should succeed')
        self.assertEqual(response_data['version'], '2',
                         'Should return agreed version')

        # Verify agreement record was created
        agreement_exists = Membertermsofuseversionagreed.objects.filter(
            member=self.user.member,
            termsofuseversion=tos_v2
        ).exists()
        self.assertTrue(agreement_exists, 'Agreement record should be created')

        # Verify agreed_date_time was set
        agreement = Membertermsofuseversionagreed.objects.get(
            member=self.user.member,
            termsofuseversion=tos_v2
        )
        self.assertIsNotNone(agreement.agreed_date_time,
                             'agreed_date_time should be set')

    def test_agreeing_to_old_version_rejected(self):
        """Test that agreeing to non-latest version is rejected"""
        # Create TOS version 2 AFTER registration
        Termsofuse.objects.create(
            version=2,
            version_note='Updated Terms',
            publication_date_time=timezone.now()
        )

        # Try to agree to v1 (old version) when v2 is latest
        response = self.client.post('/user/terms-of-use-agree', data={
            'version': '1'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['terms_of_use_agree'], 'error',
                         'Old version agreement should return error')
        self.assertIn('errors', response_data, 'Should return error details')
        self.assertEqual(response_data['errors']['error'], 'version-provided-not-most-recent',
                         'Should indicate version is not most recent')

    def test_agreeing_to_nonexistent_version_rejected(self):
        """Test that agreeing to non-existent version is rejected"""
        response = self.client.post('/user/terms-of-use-agree', data={
            'version': '999'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['terms_of_use_agree'], 'error',
                         'Non-existent version should return error')
        self.assertIn('errors', response_data, 'Should return error details')
        self.assertEqual(response_data['errors']['error'], 'version-not-found',
                         'Should indicate version not found')

    def test_missing_version_parameter_rejected(self):
        """Test that request without version parameter is rejected"""
        response = self.client.post('/user/terms-of-use-agree', data={})
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['terms_of_use_agree'], 'error',
                         'Missing version should return error')
        self.assertIn('errors', response_data, 'Should return error details')
        self.assertEqual(response_data['errors']['error'], 'version-required',
                         'Should indicate version is required')

    def test_duplicate_agreement_rejected(self):
        """Test that duplicate agreement to same version is rejected"""
        # User already agreed to v1 during registration
        # Try to agree to v1 again
        response = self.client.post('/user/terms-of-use-agree', data={
            'version': '1'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['terms_of_use_agree'], 'error',
                         'Duplicate agreement should return error')
        self.assertIn('errors', response_data, 'Should return error details')
        self.assertEqual(response_data['errors']['error'], 'version-already-agreed',
                         'Should indicate version already agreed')

    def test_anonymous_user_rejected(self):
        """Test that anonymous user cannot agree to TOS"""
        # Logout to become anonymous
        self.client.post('/user/logout')

        response = self.client.post('/user/terms-of-use-agree', data={
            'version': '1'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['terms_of_use_agree'], 'user_not_authenticated',
                         'Anonymous user should be rejected')

    def test_agreement_record_created_with_correct_associations(self):
        """Test that agreement record has correct member and TOS associations"""
        # Create TOS version 2 AFTER registration
        tos_v2 = Termsofuse.objects.create(
            version=2,
            version_note='Updated Terms',
            publication_date_time=timezone.now()
        )

        response = self.client.post('/user/terms-of-use-agree', data={
            'version': '2'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['terms_of_use_agree'], 'success')

        # Verify agreement record associations
        agreement = Membertermsofuseversionagreed.objects.get(
            member=self.user.member,
            termsofuseversion=tos_v2
        )
        self.assertEqual(agreement.member.id, self.user.member.id,
                         'Agreement should be associated with correct member')
        self.assertEqual(agreement.termsofuseversion.id, tos_v2.id,
                         'Agreement should be associated with correct TOS version')
        self.assertEqual(agreement.termsofuseversion.version, 2,
                         'TOS version should be 2')
        self.assertIsNotNone(agreement.agreed_date_time,
                             'agreed_date_time should be set')

        # Verify timestamp is recent (within last 10 seconds)
        time_diff = timezone.now() - agreement.agreed_date_time
        self.assertLess(time_diff.total_seconds(), 10,
                        'agreed_date_time should be recent')
