# Unit tests for payment processing and order placement endpoints

import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from order.models import (
    Cart, Cartsku, Cartpayment, Cartshippingaddress,
    Product, Productsku, Productimage,
    Sku, Skuprice, Skutype, Skuinventory,
    Orderconfiguration
)
from user.models import Member, Prospect, Termsofuse

from StartupWebApp.utilities import unittest_utilities


class AnonymousEmailAddressPaymentLookupEndpointTest(TestCase):
    """Test the anonymous_email_address_payment_lookup endpoint"""

    def setUp(self):
        # Create order configuration for checkout
        Orderconfiguration.objects.create(
            key='usernames_allowed_to_checkout',
            string_value='*'
        )

        Orderconfiguration.objects.create(
            key='an_ct_values_allowed_to_checkout',
            string_value='*'
        )

        # Create existing member with email
        Group.objects.create(name='Members')
        Termsofuse.objects.create(
            version='1',
            version_note='Test',
            publication_date_time=timezone.now()
        )

        self.user = User.objects.create_user(
            username='existinguser',
            email='existing@test.com',
            password='testpass123'
        )
        self.member = Member.objects.create(user=self.user, mb_cd='MEMBER123')

        # Create existing prospect
        self.prospect = Prospect.objects.create(
            email='prospect@test.com',
            pr_cd='PROSPECT456',
            created_date_time=timezone.now()
        )

    def test_anonymous_email_address_payment_lookup_when_checkout_not_allowed(self):
        """Test that endpoint requires checkout permission"""
        config = Orderconfiguration.objects.get(
            key='an_ct_values_allowed_to_checkout'
        )
        config.string_value = ''
        config.save()

        response = self.client.post('/order/anonymous-email-address-payment-lookup', {
            'anonymous_email_address': 'test@test.com'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertFalse(data['checkout_allowed'])

    def test_anonymous_email_address_payment_lookup_without_email(self):
        """Test error when email address is missing"""
        response = self.client.post('/order/anonymous-email-address-payment-lookup', {})

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['anonymous_email_address_payment_lookup'], 'error')
        self.assertEqual(data['errors']['error'], 'anonymous-email-address-required')

    def test_anonymous_email_address_payment_lookup_with_member_email(self):
        """Test error when email is already associated with member"""
        response = self.client.post('/order/anonymous-email-address-payment-lookup', {
            'anonymous_email_address': 'existing@test.com'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['anonymous_email_address_payment_lookup'], 'error')
        self.assertEqual(data['errors']['error'], 'email-address-is-associated-with-member')
        self.assertIn('login', data['errors']['description'])

    def test_anonymous_email_address_payment_lookup_with_existing_prospect(self):
        """Test success when email is already a prospect"""
        response = self.client.post('/order/anonymous-email-address-payment-lookup', {
            'anonymous_email_address': 'prospect@test.com'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['anonymous_email_address_payment_lookup'], 'success')
        self.assertIn('stripe_publishable_key', data)

    def test_anonymous_email_address_payment_lookup_creates_new_prospect(self):
        """Test that new prospect is created for new email"""
        self.assertEqual(Prospect.objects.filter(email='newuser@test.com').count(), 0)

        response = self.client.post('/order/anonymous-email-address-payment-lookup', {
            'anonymous_email_address': 'newuser@test.com'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['anonymous_email_address_payment_lookup'], 'success')

        # Verify prospect was created
        self.assertEqual(Prospect.objects.filter(email='newuser@test.com').count(), 1)
        prospect = Prospect.objects.get(email='newuser@test.com')
        self.assertTrue(prospect.email_unsubscribed)  # Default to unsubscribed
        self.assertIsNotNone(prospect.pr_cd)
        self.assertIsNotNone(prospect.email_unsubscribe_string)


class ChangeConfirmationEmailAddressEndpointTest(TestCase):
    """Test the change_confirmation_email_address endpoint"""

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

        # Create order configuration for checkout
        Orderconfiguration.objects.create(
            key='usernames_allowed_to_checkout',
            string_value='*'
        )

        Orderconfiguration.objects.create(
            key='an_ct_values_allowed_to_checkout',
            string_value='*'
        )

        # Create cart with payment and shipping
        self.cart = Cart.objects.create(member=self.member)

        self.cart_payment = Cartpayment.objects.create(
            stripe_customer_token='cus_test123',
            stripe_card_id='card_test456',
            email='test@test.com'
        )
        self.cart.payment = self.cart_payment

        self.cart_shipping = Cartshippingaddress.objects.create(
            name='Test User',
            address_line1='123 Main St',
            city='Anytown',
            state='CA',
            zip='12345'
        )
        self.cart.shipping_address = self.cart_shipping
        self.cart.save()

    def test_change_confirmation_email_address_when_checkout_not_allowed(self):
        """Test that endpoint requires checkout permission"""
        config = Orderconfiguration.objects.get(
            key='usernames_allowed_to_checkout'
        )
        config.string_value = ''
        config.save()

        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/change-confirmation-email-address', {})

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertFalse(data['checkout_allowed'])

    def test_change_confirmation_email_address_clears_cart_payment(self):
        """Test that changing email clears cart payment"""
        self.client.login(username='testuser', password='testpass123')

        self.assertIsNotNone(self.cart.payment)
        self.assertIsNotNone(self.cart.shipping_address)

        response = self.client.post('/order/change-confirmation-email-address', {})

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['change_confirmation_email_address'], 'success')

        # Verify payment and shipping were cleared
        self.cart.refresh_from_db()
        self.assertIsNone(self.cart.payment)
        self.assertIsNone(self.cart.shipping_address)


class ProcessStripePaymentTokenEndpointTest(TestCase):
    """Test the process_stripe_payment_token endpoint (simplified - no Stripe API mocking)"""

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

        # Create order configuration for checkout
        Orderconfiguration.objects.create(
            key='usernames_allowed_to_checkout',
            string_value='*'
        )

        Orderconfiguration.objects.create(
            key='an_ct_values_allowed_to_checkout',
            string_value='*'
        )

        # Create cart
        self.cart = Cart.objects.create(member=self.member)

    def test_process_stripe_payment_token_when_checkout_not_allowed(self):
        """Test that endpoint requires checkout permission"""
        config = Orderconfiguration.objects.get(
            key='usernames_allowed_to_checkout'
        )
        config.string_value = ''
        config.save()

        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/process-stripe-payment-token', {
            'stripe_token': 'tok_test123',
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
        self.assertFalse(data['checkout_allowed'])

    def test_process_stripe_payment_token_without_token(self):
        """Test error when stripe_token is missing"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/process-stripe-payment-token', {
            'email': 'test@test.com',
            'stripe_payment_args': json.dumps({})
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['process_stripe_payment_token'], 'error')
        self.assertEqual(data['errors']['error'], 'stripe-token-required')


class ConfirmPlaceOrderEndpointTest(TestCase):
    """Test the confirm_place_order endpoint (simplified - no actual order creation)"""

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

        # Create order configuration for checkout
        Orderconfiguration.objects.create(
            key='usernames_allowed_to_checkout',
            string_value='*'
        )

        Orderconfiguration.objects.create(
            key='an_ct_values_allowed_to_checkout',
            string_value='*'
        )

        # Create cart
        self.cart = Cart.objects.create(member=self.member)

    def test_confirm_place_order_when_checkout_not_allowed(self):
        """Test that endpoint requires checkout permission"""
        config = Orderconfiguration.objects.get(
            key='usernames_allowed_to_checkout'
        )
        config.string_value = ''
        config.save()

        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/confirm-place-order', {
            'agree_to_terms_of_sale': 'true'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertFalse(data['checkout_allowed'])

    def test_confirm_place_order_without_terms_agreement(self):
        """Test error when terms of sale not provided"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/confirm-place-order', {
            'stripe_payment_info': json.dumps({}),
            'stripe_shipping_addr': json.dumps({}),
            'stripe_billing_addr': json.dumps({})
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['confirm_place_order'], 'error')
        self.assertEqual(data['errors']['error'], 'agree-to-terms-of-sale-required')

    def test_confirm_place_order_with_false_terms_agreement(self):
        """Test error when terms of sale not agreed to"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/confirm-place-order', {
            'agree_to_terms_of_sale': 'false',
            'stripe_payment_info': json.dumps({}),
            'stripe_shipping_addr': json.dumps({}),
            'stripe_billing_addr': json.dumps({})
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['confirm_place_order'], 'error')
        self.assertEqual(data['errors']['error'],
                        'agree-to-terms-of-sale-must-be-checked')

    def test_confirm_place_order_when_no_cart(self):
        """Test error when cart doesn't exist"""
        self.cart.delete()

        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/confirm-place-order', {
            'agree_to_terms_of_sale': 'true',
            'stripe_payment_info': json.dumps({
                'email': 'test@test.com',
                'payment_type': 'card',
                'card_name': 'Test User',
                'card_brand': 'Visa',
                'card_last4': '4242',
                'card_exp_month': '12',
                'card_exp_year': '2025',
                'card_zip': '12345'
            }),
            'stripe_shipping_addr': json.dumps({
                'name': 'Test User',
                'address_line1': '123 Main St',
                'address_city': 'Anytown',
                'address_state': 'CA',
                'address_zip': '12345',
                'address_country': 'United States',
                'address_country_code': 'US'
            }),
            'stripe_billing_addr': json.dumps({
                'name': 'Test User',
                'address_line1': '123 Main St',
                'address_city': 'Anytown',
                'address_state': 'CA',
                'address_zip': '12345',
                'address_country': 'United States',
                'address_country_code': 'US'
            })
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['confirm_place_order'], 'error')
        self.assertEqual(data['errors']['error'], 'cart-not-found')
