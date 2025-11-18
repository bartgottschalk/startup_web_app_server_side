# Unit tests for process_stripe_payment_token endpoint

import json

from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from user.models import Member, Termsofuse, Defaultshippingaddress

from StartupWebApp.utilities import unittest_utilities


class ProcessStripePaymentTokenEndpointTest(PostgreSQLTestCase):
    """Test the process_stripe_payment_token endpoint for saving member defaults"""

    def setUp(self):
        # Create user and member
        Group.objects.create(name='Members')
        Termsofuse.objects.create(
            version='1',
            version_note='Test',
            publication_date_time=timezone.now()
        )

        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.member = Member.objects.create(user=self.user, mb_cd='MEMBER123')

    def test_creates_first_stripe_customer_for_member(self):
        """Test creating first Stripe customer and default shipping for member"""
        from unittest.mock import patch, MagicMock

        # Member has no Stripe customer yet
        self.assertIsNone(self.member.stripe_customer_token)
        self.assertIsNone(self.member.default_shipping_address)

        with patch('order.utilities.order_utils.create_stripe_customer') as mock_create_customer:
            # Mock Stripe customer creation
            mock_customer = MagicMock()
            mock_customer.id = 'cus_member_new_123'
            mock_create_customer.return_value = mock_customer

            self.client.login(username='testuser', password='testpass123')

            response = self.client.post('/user/process-stripe-payment-token', {
                'stripe_token': 'tok_test123',
                'email': 'test@test.com',
                'stripe_payment_args': json.dumps({
                    'shipping_name': 'Test User',
                    'shipping_address_line1': '123 Main St',
                    'shipping_address_city': 'Anytown',
                    'shipping_address_state': 'CA',
                    'shipping_address_zip': '12345',
                    'shipping_address_country': 'United States',
                    'shipping_address_country_code': 'US'
                })
            })

            unittest_utilities.validate_response_is_OK_and_JSON(self, response)

            data = json.loads(response.content.decode('utf8'))
            self.assertEqual(data['process_stripe_payment_token'], 'success')

            # Verify Stripe customer was created
            mock_create_customer.assert_called_once_with(
                'tok_test123', 'test@test.com', 'member_username', 'testuser'
            )

            # Verify member was updated
            self.member.refresh_from_db()
            self.assertEqual(self.member.stripe_customer_token, 'cus_member_new_123')
            self.assertTrue(self.member.use_default_shipping_and_payment_info)

            # Verify default shipping address was created
            self.assertIsNotNone(self.member.default_shipping_address)
            self.assertEqual(self.member.default_shipping_address.name, 'Test User')
            self.assertEqual(self.member.default_shipping_address.address_line1, '123 Main St')
            self.assertEqual(self.member.default_shipping_address.city, 'Anytown')
            self.assertEqual(self.member.default_shipping_address.state, 'CA')

    def test_adds_card_to_existing_customer(self):
        """Test adding new card to member with existing Stripe customer"""
        from unittest.mock import patch, MagicMock

        # Member already has Stripe customer
        self.member.stripe_customer_token = 'cus_existing_456'
        self.member.save()

        with patch('order.utilities.order_utils.stripe_customer_add_card') as mock_add_card, \
                patch('order.utilities.order_utils.stripe_customer_change_default_payemnt') as mock_change_default:

            # Mock adding card
            mock_card = MagicMock()
            mock_card.id = 'card_new_789'
            mock_add_card.return_value = mock_card

            self.client.login(username='testuser', password='testpass123')

            response = self.client.post('/user/process-stripe-payment-token', {
                'stripe_token': 'tok_new_card',
                'email': 'test@test.com',
                'stripe_payment_args': json.dumps({
                    'shipping_name': 'Test User',
                    'shipping_address_line1': '456 Oak Ave',
                    'shipping_address_city': 'Newtown',
                    'shipping_address_state': 'NY',
                    'shipping_address_zip': '54321',
                    'shipping_address_country': 'United States',
                    'shipping_address_country_code': 'US'
                })
            })

            unittest_utilities.validate_response_is_OK_and_JSON(self, response)

            data = json.loads(response.content.decode('utf8'))
            self.assertEqual(data['process_stripe_payment_token'], 'success')

            # Verify card was added to existing customer
            mock_add_card.assert_called_once_with('cus_existing_456', 'tok_new_card')

            # Verify default payment method was changed
            mock_change_default.assert_called_once_with('cus_existing_456', 'card_new_789')

            # Verify member still has same customer token
            self.member.refresh_from_db()
            self.assertEqual(self.member.stripe_customer_token, 'cus_existing_456')
            self.assertTrue(self.member.use_default_shipping_and_payment_info)

    def test_updates_existing_default_shipping_address(self):
        """Test updating existing default shipping address"""
        from unittest.mock import patch, MagicMock

        # Create existing default shipping address
        existing_address = Defaultshippingaddress.objects.create(
            name='Old Name',
            address_line1='Old Address',
            city='Old City',
            state='CA',
            zip='11111',
            country='United States',
            country_code='US'
        )
        self.member.default_shipping_address = existing_address
        self.member.save()

        with patch('order.utilities.order_utils.create_stripe_customer') as mock_create_customer:
            mock_customer = MagicMock()
            mock_customer.id = 'cus_test'
            mock_create_customer.return_value = mock_customer

            self.client.login(username='testuser', password='testpass123')

            response = self.client.post('/user/process-stripe-payment-token', {
                'stripe_token': 'tok_test',
                'email': 'test@test.com',
                'stripe_payment_args': json.dumps({
                    'shipping_name': 'Updated Name',
                    'shipping_address_line1': 'Updated Address',
                    'shipping_address_city': 'Updated City',
                    'shipping_address_state': 'TX',
                    'shipping_address_zip': '99999',
                    'shipping_address_country': 'United States',
                    'shipping_address_country_code': 'US'
                })
            })

            unittest_utilities.validate_response_is_OK_and_JSON(self, response)

            data = json.loads(response.content.decode('utf8'))
            self.assertEqual(data['process_stripe_payment_token'], 'success')

            # Verify existing address was updated (not replaced)
            self.member.refresh_from_db()
            self.assertEqual(self.member.default_shipping_address.id, existing_address.id)
            self.assertEqual(self.member.default_shipping_address.name, 'Updated Name')
            self.assertEqual(self.member.default_shipping_address.address_line1, 'Updated Address')
            self.assertEqual(self.member.default_shipping_address.city, 'Updated City')
            self.assertEqual(self.member.default_shipping_address.state, 'TX')

    def test_handles_missing_state_in_shipping_args(self):
        """Test handling optional state field in shipping address"""
        from unittest.mock import patch, MagicMock

        with patch('order.utilities.order_utils.create_stripe_customer') as mock_create_customer:
            mock_customer = MagicMock()
            mock_customer.id = 'cus_test'
            mock_create_customer.return_value = mock_customer

            self.client.login(username='testuser', password='testpass123')

            response = self.client.post('/user/process-stripe-payment-token', {
                'stripe_token': 'tok_test',
                'email': 'test@test.com',
                'stripe_payment_args': json.dumps({
                    'shipping_name': 'International User',
                    'shipping_address_line1': '789 Global St',
                    'shipping_address_city': 'London',
                    # No 'shipping_address_state' provided
                    'shipping_address_zip': 'SW1A 1AA',
                    'shipping_address_country': 'United Kingdom',
                    'shipping_address_country_code': 'GB'
                })
            })

            unittest_utilities.validate_response_is_OK_and_JSON(self, response)

            data = json.loads(response.content.decode('utf8'))
            self.assertEqual(data['process_stripe_payment_token'], 'success')

            # Verify address was created with empty state
            self.member.refresh_from_db()
            self.assertIsNotNone(self.member.default_shipping_address)
            self.assertEqual(self.member.default_shipping_address.state, '')

    def test_stripe_error_handling(self):
        """Test Stripe error handling (CardError, etc.)"""
        from unittest.mock import patch
        import stripe

        with patch('order.utilities.order_utils.create_stripe_customer') as mock_create_customer:
            # Mock Stripe error
            error_body = {
                'error': {
                    'type': 'card_error',
                    'code': 'card_declined',
                    'message': 'Your card was declined.'}}
            mock_create_customer.side_effect = stripe.error.CardError(
                'Card declined', 'card', 'card_declined', http_status=402, json_body=error_body
            )

            self.client.login(username='testuser', password='testpass123')

            response = self.client.post('/user/process-stripe-payment-token', {
                'stripe_token': 'tok_invalid',
                'email': 'test@test.com',
                'stripe_payment_args': json.dumps({
                    'shipping_name': 'Test User',
                    'shipping_address_line1': '123 Main St',
                    'shipping_address_city': 'Anytown',
                    'shipping_address_zip': '12345',
                    'shipping_address_country': 'United States',
                    'shipping_address_country_code': 'US'
                })
            })

            unittest_utilities.validate_response_is_OK_and_JSON(self, response)

            data = json.loads(response.content.decode('utf8'))
            self.assertEqual(data['process_stripe_payment_token'], 'error')
            self.assertEqual(data['errors']['error'], 'error-creating-stripe-customer')
            # Verify checkout_allowed is NOT in response (was causing NameError bug before fix)
            self.assertNotIn('checkout_allowed', data)

    def test_missing_stripe_token_error(self):
        """Test error when stripe_token is missing"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/user/process-stripe-payment-token', {
            # No stripe_token provided
            'email': 'test@test.com',
            'stripe_payment_args': json.dumps({
                'shipping_name': 'Test User',
                'shipping_address_line1': '123 Main St',
                'shipping_address_city': 'Anytown',
                'shipping_address_zip': '12345',
                'shipping_address_country': 'United States',
                'shipping_address_country_code': 'US'
            })
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['process_stripe_payment_token'], 'error')
        self.assertEqual(data['errors']['error'], 'stripe-token-required')
        # Verify checkout_allowed is NOT in response (was causing NameError bug before fix)
        self.assertNotIn('checkout_allowed', data)
