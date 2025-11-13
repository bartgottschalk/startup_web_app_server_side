# Unit tests for account content endpoint

import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from clientevent.models import Configuration as ClientEventConfiguration
from order.models import Order, Skutype, Skuinventory, Product, Sku, Skuprice, Productsku
from user.models import Termsofuse, Membertermsofuseversionagreed

from StartupWebApp.utilities import unittest_utilities


class AccountContentAPITest(TestCase):

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

        # Verify shipping/billing/payment data exists
        self.assertIn('shipping_billing_addresses_and_payment_data', account_content)

        # Verify stripe key included
        self.assertIn('stripe_publishable_key', account_content)

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

    def test_retrieves_stripe_customer_payment_data_with_defaults(self):
        """Test that Stripe customer payment data is retrieved when member has saved defaults"""
        from unittest.mock import patch, MagicMock
        from user.models import Defaultshippingaddress

        # Create default shipping address for member
        user = User.objects.get(username='testuser')
        default_address = Defaultshippingaddress.objects.create(
            name='Test User',
            address_line1='123 Main St',
            city='Anytown',
            state='CA',
            zip='12345',
            country='United States',
            country_code='US'
        )

        # Set member to use defaults with Stripe customer
        user.member.default_shipping_address = default_address
        user.member.use_default_shipping_and_payment_info = True
        user.member.stripe_customer_token = 'cus_test_default_123'
        user.member.save()

        with patch('stripe.Customer.retrieve') as mock_stripe_retrieve, \
                patch('order.utilities.order_utils.get_stripe_customer_payment_data') as mock_get_payment_data:

            # Mock Stripe customer
            mock_customer = MagicMock()
            mock_customer.id = 'cus_test_default_123'
            mock_stripe_retrieve.return_value = mock_customer

            # Mock payment data response
            mock_payment_data = {
                'token': {
                    'card': {
                        'brand': 'Visa',
                        'last4': '4242',
                        'exp_month': 12,
                        'exp_year': 2025
                    },
                    'email': 'testuser@test.com',
                    'type': 'card'
                },
                'args': {
                    'shipping_name': 'Test User',
                    'shipping_address_line1': '123 Main St',
                    'shipping_address_city': 'Anytown'
                }
            }
            mock_get_payment_data.return_value = mock_payment_data

            # Get account content
            response = self.client.get('/user/account-content')
            unittest_utilities.validate_response_is_OK_and_JSON(self, response)

            response_data = json.loads(response.content.decode('utf8'))
            account_content = response_data['account_content']

            # Verify Stripe customer was retrieved
            mock_stripe_retrieve.assert_called_once_with('cus_test_default_123')

            # Verify get_stripe_customer_payment_data was called
            self.assertEqual(mock_get_payment_data.call_count, 1)

            # Verify payment data is in response
            self.assertIn('shipping_billing_addresses_and_payment_data', account_content)
            payment_data = account_content['shipping_billing_addresses_and_payment_data']
            self.assertEqual(payment_data['token']['card']['brand'], 'Visa')
            self.assertEqual(payment_data['token']['card']['last4'], '4242')

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

    def test_stripe_invalid_request_error_handled_gracefully(self):
        """Test that Stripe InvalidRequestError is handled without crashing endpoint"""
        from unittest.mock import patch
        from user.models import Defaultshippingaddress
        import stripe

        # Setup member with saved payment defaults
        user = User.objects.get(username='testuser')
        default_address = Defaultshippingaddress.objects.create(
            name='Test User',
            address_line1='123 Main St',
            city='Anytown',
            state='CA',
            zip='12345',
            country='United States',
            country_code='US'
        )
        user.member.default_shipping_address = default_address
        user.member.use_default_shipping_and_payment_info = True
        user.member.stripe_customer_token = 'cus_invalid_token_123'
        user.member.save()

        # Mock Stripe to raise InvalidRequestError
        with patch('stripe.Customer.retrieve') as mock_stripe_retrieve:
            mock_stripe_retrieve.side_effect = stripe.error.InvalidRequestError(
                message='No such customer: cus_invalid_token_123',
                param='id'
            )

            # Get account content - should NOT crash
            response = self.client.get('/user/account-content')
            unittest_utilities.validate_response_is_OK_and_JSON(self, response)

            response_data = json.loads(response.content.decode('utf8'))
            account_content = response_data['account_content']

            # Verify basic account data is still returned
            self.assertEqual(account_content['authenticated'], 'true')
            self.assertIn('personal_data', account_content)

            # Verify payment data is empty (gracefully degraded)
            self.assertIn('shipping_billing_addresses_and_payment_data', account_content)
            payment_data = account_content['shipping_billing_addresses_and_payment_data']
            self.assertEqual(payment_data, {})

    def test_stripe_authentication_error_handled_gracefully(self):
        """Test that Stripe AuthenticationError is handled without crashing endpoint"""
        from unittest.mock import patch
        from user.models import Defaultshippingaddress
        import stripe

        # Setup member with saved payment defaults
        user = User.objects.get(username='testuser')
        default_address = Defaultshippingaddress.objects.create(
            name='Test User',
            address_line1='456 Oak Ave',
            city='Testville',
            state='NY',
            zip='54321',
            country='United States',
            country_code='US'
        )
        user.member.default_shipping_address = default_address
        user.member.use_default_shipping_and_payment_info = True
        user.member.stripe_customer_token = 'cus_test_auth_error_456'
        user.member.save()

        # Mock Stripe to raise AuthenticationError
        with patch('stripe.Customer.retrieve') as mock_stripe_retrieve:
            mock_stripe_retrieve.side_effect = stripe.error.AuthenticationError(
                message='Invalid API Key provided'
            )

            # Get account content - should NOT crash
            response = self.client.get('/user/account-content')
            unittest_utilities.validate_response_is_OK_and_JSON(self, response)

            response_data = json.loads(response.content.decode('utf8'))
            account_content = response_data['account_content']

            # Verify basic account data is still returned
            self.assertEqual(account_content['authenticated'], 'true')
            self.assertIn('personal_data', account_content)

            # Verify payment data is empty (gracefully degraded)
            payment_data = account_content['shipping_billing_addresses_and_payment_data']
            self.assertEqual(payment_data, {})

    def test_stripe_api_connection_error_handled_gracefully(self):
        """Test that Stripe APIConnectionError is handled without crashing endpoint"""
        from unittest.mock import patch
        from user.models import Defaultshippingaddress
        import stripe

        # Setup member with saved payment defaults
        user = User.objects.get(username='testuser')
        default_address = Defaultshippingaddress.objects.create(
            name='Test User',
            address_line1='789 Pine Rd',
            city='Hometown',
            state='TX',
            zip='67890',
            country='United States',
            country_code='US'
        )
        user.member.default_shipping_address = default_address
        user.member.use_default_shipping_and_payment_info = True
        user.member.stripe_customer_token = 'cus_test_connection_error_789'
        user.member.save()

        # Mock Stripe to raise APIConnectionError
        with patch('stripe.Customer.retrieve') as mock_stripe_retrieve:
            mock_stripe_retrieve.side_effect = stripe.error.APIConnectionError(
                message='Network communication with Stripe failed'
            )

            # Get account content - should NOT crash
            response = self.client.get('/user/account-content')
            unittest_utilities.validate_response_is_OK_and_JSON(self, response)

            response_data = json.loads(response.content.decode('utf8'))
            account_content = response_data['account_content']

            # Verify basic account data is still returned
            self.assertEqual(account_content['authenticated'], 'true')
            self.assertIn('personal_data', account_content)

            # Verify payment data is empty (gracefully degraded)
            payment_data = account_content['shipping_billing_addresses_and_payment_data']
            self.assertEqual(payment_data, {})
