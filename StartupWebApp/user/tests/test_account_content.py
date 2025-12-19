# Unit tests for account content endpoint

import json

from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from clientevent.models import Configuration as ClientEventConfiguration
from order.models import Order, Skutype, Skuinventory, Product, Sku, Skuprice, Productsku
from user.models import Termsofuse, Membertermsofuseversionagreed

from StartupWebApp.utilities import unittest_utilities


class AccountContentAPITest(PostgreSQLTestCase):

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
        self.terms = Termsofuse.objects.create(
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

    def test_authenticated_user_retrieves_account_data(self):
        """Test that authenticated user can retrieve comprehensive account data"""
        response = self.client.get('/user/account-content')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))

        # Verify top-level structure
        self.assertIn('account_content', response_data)
        account_content = response_data['account_content']
        self.assertEqual(account_content['authenticated'], 'true')

        # Verify personal data
        self.assertIn('personal_data', account_content)
        personal_data = account_content['personal_data']
        self.assertEqual(personal_data['username'], 'testuser')
        self.assertEqual(personal_data['first_name'], 'Test')
        self.assertEqual(personal_data['last_name'], 'User')
        self.assertFalse(personal_data['newsletter_subscriber'])
        self.assertFalse(personal_data['email_unsubscribed'])
        self.assertIsNotNone(personal_data['joined_date_time'])
        self.assertIsNotNone(personal_data['last_login_date_time'])
        self.assertIsNotNone(personal_data['terms_of_use_agreed_date_time'])

        # Verify email data
        self.assertIn('email_data', account_content)
        email_data = account_content['email_data']
        self.assertEqual(email_data['email_address'], 'testuser@test.com')
        self.assertFalse(email_data['email_verified'])
        # Verification tokens are generated during account creation, so this should be true
        self.assertTrue(email_data['verification_request_sent_within_24_hours'])

        # Verify orders data exists (empty for new user)
        self.assertIn('orders_data', account_content)

    def test_unauthenticated_user_receives_minimal_response(self):
        """Test that unauthenticated user receives minimal response"""
        # Logout first
        self.client.post('/user/logout')

        response = self.client.get('/user/account-content')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))

        # Verify minimal response for anonymous users
        self.assertIn('account_content', response_data)
        account_content = response_data['account_content']
        self.assertEqual(account_content['authenticated'], 'false')

        # Verify no personal data leaked
        self.assertNotIn('personal_data', account_content)
        self.assertNotIn('email_data', account_content)
        self.assertNotIn('orders_data', account_content)

    def test_email_verification_status_reflected(self):
        """Test that email verification status is correctly reflected"""
        # Initially email should not be verified
        response = self.client.get('/user/account-content')
        response_data = json.loads(response.content.decode('utf8'))
        email_data = response_data['account_content']['email_data']
        self.assertFalse(email_data['email_verified'])

        # Verify email
        user = User.objects.get(username='testuser')
        user.member.email_verified = True
        user.member.save()

        # Check again
        response = self.client.get('/user/account-content')
        response_data = json.loads(response.content.decode('utf8'))
        email_data = response_data['account_content']['email_data']
        self.assertTrue(email_data['email_verified'])

    def test_verification_request_within_24_hours_detected(self):
        """Test that recent verification request (within 24 hours) is detected"""
        # Request email verification
        self.client.post('/user/verify-email-address')

        # Check account content
        response = self.client.get('/user/account-content')
        response_data = json.loads(response.content.decode('utf8'))
        email_data = response_data['account_content']['email_data']

        # Should show verification request sent within 24 hours
        self.assertTrue(email_data['verification_request_sent_within_24_hours'])

    def test_orders_data_included_for_users_with_orders(self):
        """Test that orders data is included for users with order history"""
        # Create an order for the user
        user = User.objects.get(username='testuser')
        Order.objects.create(
            member=user.member,
            identifier='TEST123',
            order_date_time=timezone.now(),
            sales_tax_amt=5.00,
            order_total=55.00
        )

        # Get account content
        response = self.client.get('/user/account-content')
        response_data = json.loads(response.content.decode('utf8'))
        orders_data = response_data['account_content']['orders_data']

        # Verify order is included
        self.assertGreater(len(orders_data), 0, 'Orders data should include user orders')

        # Verify order details
        first_order = orders_data['1']  # Orders are keyed by counter starting at 1
        self.assertEqual(first_order['identifier'], 'TEST123')
        self.assertEqual(float(first_order['sales_tax_amt']), 5.00)
        self.assertEqual(float(first_order['order_total']), 55.00)

    def test_expired_email_verification_token_handled(self):
        """Test that expired email verification tokens are handled gracefully"""
        from django.core.signing import TimestampSigner

        user = User.objects.get(username='testuser')

        # Create an expired verification token (simulate old token)
        TimestampSigner(salt='emailverificationsalt')
        # Create a token that's already expired by setting it manually
        # We'll use an invalid signature format to trigger the exception
        user.member.email_verification_string_signed = 'invalid_signature_that_will_fail'
        user.member.email_verified = False
        user.member.save()

        # Get account content
        response = self.client.get('/user/account-content')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        email_data = response_data['account_content']['email_data']

        # Should show verification NOT sent within 24 hours (expired/invalid token)
        self.assertFalse(email_data['verification_request_sent_within_24_hours'])
        self.assertFalse(email_data['email_verified'])

    def test_member_with_no_terms_agreed(self):
        """Test that member with no terms agreed shows None for agreed_date_time"""
        user = User.objects.get(username='testuser')

        # Delete any existing terms agreements
        Membertermsofuseversionagreed.objects.filter(member=user.member).delete()

        # Get account content
        response = self.client.get('/user/account-content')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        personal_data = response_data['account_content']['personal_data']

        # Should show None for terms_of_use_agreed_date_time
        self.assertIsNone(personal_data['terms_of_use_agreed_date_time'])
