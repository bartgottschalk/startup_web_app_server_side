# Unit tests for payment processing and order placement endpoints

import json

from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from order.models import (
    Cart, Cartpayment, Cartshippingaddress,
    Orderconfiguration
)
from user.models import Member, Prospect, Termsofuse

from StartupWebApp.utilities import unittest_utilities


class AnonymousEmailAddressPaymentLookupEndpointTest(PostgreSQLTestCase):
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


class ChangeConfirmationEmailAddressEndpointTest(PostgreSQLTestCase):
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
