# Unit tests for checkout flow endpoints

import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.conf import settings

from order.models import (
    Cart, Cartsku, Cartpayment, Cartshippingaddress, Cartshippingmethod,
    Product, Productsku, Productimage,
    Sku, Skuprice, Skutype, Skuinventory,
    Shippingmethod, Orderconfiguration
)
from user.models import Member, Defaultshippingaddress, Termsofuse

from StartupWebApp.utilities import unittest_utilities


class CheckoutAllowedEndpointTest(TestCase):
    """Test the checkout_allowed endpoint"""

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
            string_value='testuser'
        )

        Orderconfiguration.objects.create(
            key='an_ct_values_allowed_to_checkout',
            string_value='test_token'
        )

    def test_checkout_allowed_for_authorized_user(self):
        """Test that authorized user can checkout"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/checkout-allowed')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertTrue(data['checkout_allowed'])

    def test_checkout_allowed_for_unauthorized_user(self):
        """Test that unauthorized user cannot checkout"""
        # Create another user not in allowed list
        user2 = User.objects.create_user(
            username='otheruser',
            email='other@test.com',
            password='testpass123'
        )
        Member.objects.create(user=user2, mb_cd='MEMBER456')

        self.client.login(username='otheruser', password='testpass123')

        response = self.client.get('/order/checkout-allowed')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertFalse(data['checkout_allowed'])

    def test_checkout_allowed_with_wildcard(self):
        """Test that wildcard allows all users"""
        # Update config to allow all users
        config = Orderconfiguration.objects.get(
            key='usernames_allowed_to_checkout'
        )
        config.string_value = '*'
        config.save()

        user2 = User.objects.create_user(
            username='anyuser',
            email='any@test.com',
            password='testpass123'
        )
        Member.objects.create(user=user2, mb_cd='MEMBER789')

        self.client.login(username='anyuser', password='testpass123')

        response = self.client.get('/order/checkout-allowed')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertTrue(data['checkout_allowed'])


class ConfirmItemsEndpointTest(TestCase):
    """Test the confirm_items endpoint"""

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

        # Allow checkout
        Orderconfiguration.objects.create(
            key='usernames_allowed_to_checkout',
            string_value='*'
        )

        Orderconfiguration.objects.create(
            key='an_ct_values_allowed_to_checkout',
            string_value='*'
        )

        # Create product and SKU
        skutype = Skutype.objects.create(title='product')
        skuinventory = Skuinventory.objects.create(
            title='In Stock',
            identifier='in-stock'
        )

        product = Product.objects.create(
            title='Test Product',
            title_url='TestProduct',
            identifier='PROD001'
        )

        Productimage.objects.create(
            product=product,
            image_url='https://example.com/product.jpg',
            main_image=True
        )

        self.sku = Sku.objects.create(
            color='Blue',
            size='Medium',
            sku_type=skutype,
            sku_inventory=skuinventory,
            description='Test SKU'
        )

        Skuprice.objects.create(
            sku=self.sku,
            price=10.00,
            created_date_time=timezone.now()
        )

        Productsku.objects.create(product=product, sku=self.sku)

        # Create cart with items
        self.cart = Cart.objects.create(member=self.member)
        Cartsku.objects.create(cart=self.cart, sku=self.sku, quantity=2)

    def test_confirm_items_when_checkout_not_allowed(self):
        """Test that confirm_items requires checkout permission"""
        # Update config to disallow checkout
        config = Orderconfiguration.objects.get(
            key='usernames_allowed_to_checkout'
        )
        config.string_value = ''
        config.save()

        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/confirm-items')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertFalse(data['checkout_allowed'])
        self.assertNotIn('item_data', data)

    def test_confirm_items_returns_cart_items(self):
        """Test that confirm_items returns cart items when allowed"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/confirm-items')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertTrue(data['checkout_allowed'])
        self.assertTrue(data['cart_found'])
        self.assertIn('item_data', data)

        # Verify item data is present
        item_data = data['item_data']['product_sku_data']
        self.assertEqual(len(item_data), 1)


class ConfirmShippingMethodEndpointTest(TestCase):
    """Test the confirm_shipping_method endpoint"""

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

        # Allow checkout
        Orderconfiguration.objects.create(
            key='usernames_allowed_to_checkout',
            string_value='*'
        )

        Orderconfiguration.objects.create(
            key='an_ct_values_allowed_to_checkout',
            string_value='*'
        )

        # Create shipping method
        self.shipping_method = Shippingmethod.objects.create(
            identifier='standard',
            carrier='USPS',
            shipping_cost=5.00,
            tracking_code_base_url='https://tools.usps.com/track'
        )

        # Create cart with shipping method
        self.cart = Cart.objects.create(member=self.member)
        Cartshippingmethod.objects.create(
            cart=self.cart,
            shippingmethod=self.shipping_method
        )

    def test_confirm_shipping_method_when_checkout_not_allowed(self):
        """Test that confirm_shipping_method requires checkout permission"""
        config = Orderconfiguration.objects.get(
            key='usernames_allowed_to_checkout'
        )
        config.string_value = ''
        config.save()

        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/confirm-shipping-method')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertFalse(data['checkout_allowed'])

    def test_confirm_shipping_method_returns_selected_method(self):
        """Test that confirm_shipping_method returns selected shipping method"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/confirm-shipping-method')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertTrue(data['checkout_allowed'])
        self.assertTrue(data['cart_found'])

        shipping_method = data['confirm_shipping_method']
        self.assertEqual(shipping_method['identifier'], 'standard')
        self.assertEqual(shipping_method['carrier'], 'USPS')
        self.assertEqual(shipping_method['shipping_cost'], 5.00)


class ConfirmDiscountCodesEndpointTest(TestCase):
    """Test the confirm_discount_codes endpoint"""

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

        # Allow checkout
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

    def test_confirm_discount_codes_when_checkout_not_allowed(self):
        """Test that confirm_discount_codes requires checkout permission"""
        config = Orderconfiguration.objects.get(
            key='usernames_allowed_to_checkout'
        )
        config.string_value = ''
        config.save()

        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/confirm-discount-codes')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertFalse(data['checkout_allowed'])

    def test_confirm_discount_codes_returns_discount_data(self):
        """Test that confirm_discount_codes returns discount code data"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/confirm-discount-codes')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertTrue(data['checkout_allowed'])
        self.assertTrue(data['cart_found'])
        self.assertIn('discount_code_data', data)


class ConfirmTotalsEndpointTest(TestCase):
    """Test the confirm_totals endpoint"""

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

        # Allow checkout
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

    def test_confirm_totals_when_checkout_not_allowed(self):
        """Test that confirm_totals requires checkout permission"""
        config = Orderconfiguration.objects.get(
            key='usernames_allowed_to_checkout'
        )
        config.string_value = ''
        config.save()

        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/confirm-totals')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertFalse(data['checkout_allowed'])

    def test_confirm_totals_returns_cart_totals(self):
        """Test that confirm_totals returns complete cart totals"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/confirm-totals')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertTrue(data['checkout_allowed'])
        self.assertTrue(data['cart_found'])

        totals = data['confirm_totals_data']
        self.assertIn('item_subtotal', totals)
        self.assertIn('item_discount', totals)
        self.assertIn('shipping_subtotal', totals)
        self.assertIn('shipping_discount', totals)
        self.assertIn('cart_total', totals)


class ConfirmPaymentDataEndpointTest(TestCase):
    """Test the confirm_payment_data endpoint"""

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

        # Allow checkout
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

    def test_confirm_payment_data_when_checkout_not_allowed(self):
        """Test that confirm_payment_data requires checkout permission"""
        config = Orderconfiguration.objects.get(
            key='usernames_allowed_to_checkout'
        )
        config.string_value = ''
        config.save()

        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/confirm-payment-data')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertFalse(data['checkout_allowed'])

    def test_confirm_payment_data_returns_stripe_key(self):
        """Test that confirm_payment_data returns Stripe publishable key"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/confirm-payment-data')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertTrue(data['checkout_allowed'])
        self.assertIn('stripe_publishable_key', data)
        self.assertEqual(data['stripe_publishable_key'],
                        settings.STRIPE_PUBLISHABLE_SECRET_KEY)

    def test_confirm_payment_data_returns_user_email(self):
        """Test that confirm_payment_data returns authenticated user email"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/confirm-payment-data')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['email'], 'test@test.com')

    def test_confirm_payment_data_for_anonymous_user(self):
        """Test that confirm_payment_data works for anonymous users"""
        # Set anonymous checkout allowed
        config = Orderconfiguration.objects.get(
            key='an_ct_values_allowed_to_checkout'
        )
        config.string_value = '*'  # Allow all anonymous checkouts
        config.save()

        # For anonymous users without proper signed cookie,
        # checkout_allowed will be True (due to *) but email will be None
        response = self.client.get('/order/confirm-payment-data')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        # When checkout is allowed for anonymous, email should be None
        if 'email' in data:
            self.assertIsNone(data['email'])

    def test_confirm_payment_data_loads_default_shipping(self):
        """Test that confirm_payment_data loads member's default shipping"""
        # Set up member with default shipping
        default_shipping = Defaultshippingaddress.objects.create(
            name='Test User',
            address_line1='123 Main St',
            city='Anytown',
            state='CA',
            zip='12345',
            country='United States',
            country_code='US'
        )

        self.member.default_shipping_address = default_shipping
        self.member.use_default_shipping_and_payment_info = True
        self.member.save()

        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/confirm-payment-data')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        # Verify cart shipping address was created
        self.cart.refresh_from_db()
        self.assertIsNotNone(self.cart.shipping_address)
        self.assertEqual(self.cart.shipping_address.name, 'Test User')
        self.assertEqual(self.cart.shipping_address.address_line1, '123 Main St')

    def test_confirm_payment_data_retrieves_existing_stripe_customer(self):
        """Test that confirm_payment_data retrieves existing Stripe customer data"""
        from unittest.mock import patch, MagicMock

        # Set up cart with payment and shipping address
        cart_payment = Cartpayment.objects.create(
            stripe_customer_token='cus_existing123',
            stripe_card_id='card_existing456',
            email='test@test.com'
        )
        cart_shipping = Cartshippingaddress.objects.create(
            name='Test User',
            address_line1='123 Main St',
            city='Anytown',
            state='CA',
            zip='12345',
            country='United States',
            country_code='US'
        )
        self.cart.payment = cart_payment
        self.cart.shipping_address = cart_shipping
        self.cart.save()

        with patch('stripe.Customer.retrieve') as mock_stripe_retrieve, \
             patch('order.utilities.order_utils.get_stripe_customer_payment_data') as mock_get_customer_data:

            # Mock Stripe customer object
            mock_customer = MagicMock()
            mock_customer.id = 'cus_existing123'
            mock_customer.sources.data = []
            mock_stripe_retrieve.return_value = mock_customer

            # Mock customer data dictionary
            expected_customer_data = {
                'stripe_customer_token': 'cus_existing123',
                'stripe_card_id': 'card_existing456',
                'last4': '4242',
                'brand': 'Visa',
                'exp_month': 12,
                'exp_year': 2025
            }
            mock_get_customer_data.return_value = expected_customer_data

            self.client.login(username='testuser', password='testpass123')

            response = self.client.get('/order/confirm-payment-data')

            unittest_utilities.validate_response_is_OK_and_JSON(self, response)

            data = json.loads(response.content.decode('utf8'))
            self.assertTrue(data['checkout_allowed'])

            # Verify Stripe customer was retrieved
            mock_stripe_retrieve.assert_called_once_with('cus_existing123')

            # Verify get_stripe_customer_payment_data was called with correct args
            self.assertEqual(mock_get_customer_data.call_count, 1)
            call_args = mock_get_customer_data.call_args[0]
            self.assertEqual(call_args[0], mock_customer)  # customer object
            # call_args[1] is shipping_address_dict - verify it has expected structure
            self.assertIn('name', call_args[1])
            self.assertEqual(call_args[1]['name'], 'Test User')
            self.assertEqual(call_args[2], 'card_existing456')  # stripe_card_id

            # Verify customer data is returned in response
            self.assertIn('customer_data', data)
            self.assertEqual(data['customer_data'], expected_customer_data)

    def test_confirm_payment_data_creates_payment_from_member_default(self):
        """Test that confirm_payment_data creates cart payment from member's default token"""
        # Set member to use default payment info with saved stripe token
        self.member.use_default_shipping_and_payment_info = True
        self.member.stripe_customer_token = 'cus_member_default_123'
        self.member.save()

        # Ensure cart has no payment
        self.assertIsNone(self.cart.payment)

        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/confirm-payment-data')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertTrue(data['checkout_allowed'])

        # Verify cart payment was created from member's default token
        self.cart.refresh_from_db()
        self.assertIsNotNone(self.cart.payment)
        self.assertEqual(self.cart.payment.stripe_customer_token, 'cus_member_default_123')
        self.assertEqual(self.cart.payment.email, 'test@test.com')

    def test_confirm_payment_data_stripe_invalid_request_error_handled(self):
        """Test that Stripe InvalidRequestError is handled gracefully in confirm_payment_data"""
        from unittest.mock import patch
        import stripe

        # Set up cart with payment and shipping address
        cart_payment = Cartpayment.objects.create(
            stripe_customer_token='cus_invalid_token_999',
            stripe_card_id='card_test_999',
            email='test@test.com'
        )
        cart_shipping = Cartshippingaddress.objects.create(
            name='Test User',
            address_line1='123 Test St',
            city='Testtown',
            state='CA',
            zip='12345',
            country='United States',
            country_code='US'
        )
        self.cart.payment = cart_payment
        self.cart.shipping_address = cart_shipping
        self.cart.save()

        # Mock Stripe to raise InvalidRequestError
        with patch('stripe.Customer.retrieve') as mock_stripe_retrieve:
            mock_stripe_retrieve.side_effect = stripe.error.InvalidRequestError(
                message='No such customer: cus_invalid_token_999',
                param='id'
            )

            self.client.login(username='testuser', password='testpass123')

            # Call should NOT crash with 500 error
            response = self.client.get('/order/confirm-payment-data')
            unittest_utilities.validate_response_is_OK_and_JSON(self, response)

            data = json.loads(response.content.decode('utf8'))
            self.assertTrue(data['checkout_allowed'])

            # Verify customer_data is None (graceful degradation)
            self.assertIsNone(data['customer_data'])

    def test_confirm_payment_data_stripe_authentication_error_handled(self):
        """Test that Stripe AuthenticationError is handled gracefully in confirm_payment_data"""
        from unittest.mock import patch
        import stripe

        # Set up cart with payment and shipping address
        cart_payment = Cartpayment.objects.create(
            stripe_customer_token='cus_test_auth_888',
            stripe_card_id='card_test_888',
            email='test@test.com'
        )
        cart_shipping = Cartshippingaddress.objects.create(
            name='Test User',
            address_line1='456 Auth St',
            city='Authtown',
            state='NY',
            zip='54321',
            country='United States',
            country_code='US'
        )
        self.cart.payment = cart_payment
        self.cart.shipping_address = cart_shipping
        self.cart.save()

        # Mock Stripe to raise AuthenticationError
        with patch('stripe.Customer.retrieve') as mock_stripe_retrieve:
            mock_stripe_retrieve.side_effect = stripe.error.AuthenticationError(
                message='Invalid API Key provided'
            )

            self.client.login(username='testuser', password='testpass123')

            # Call should NOT crash with 500 error
            response = self.client.get('/order/confirm-payment-data')
            unittest_utilities.validate_response_is_OK_and_JSON(self, response)

            data = json.loads(response.content.decode('utf8'))
            self.assertTrue(data['checkout_allowed'])

            # Verify customer_data is None (graceful degradation)
            self.assertIsNone(data['customer_data'])

    def test_confirm_payment_data_stripe_api_connection_error_handled(self):
        """Test that Stripe APIConnectionError is handled gracefully in confirm_payment_data"""
        from unittest.mock import patch
        import stripe

        # Set up cart with payment and shipping address
        cart_payment = Cartpayment.objects.create(
            stripe_customer_token='cus_test_conn_777',
            stripe_card_id='card_test_777',
            email='test@test.com'
        )
        cart_shipping = Cartshippingaddress.objects.create(
            name='Test User',
            address_line1='789 Network St',
            city='Conntown',
            state='TX',
            zip='67890',
            country='United States',
            country_code='US'
        )
        self.cart.payment = cart_payment
        self.cart.shipping_address = cart_shipping
        self.cart.save()

        # Mock Stripe to raise APIConnectionError
        with patch('stripe.Customer.retrieve') as mock_stripe_retrieve:
            mock_stripe_retrieve.side_effect = stripe.error.APIConnectionError(
                message='Network communication with Stripe failed'
            )

            self.client.login(username='testuser', password='testpass123')

            # Call should NOT crash with 500 error
            response = self.client.get('/order/confirm-payment-data')
            unittest_utilities.validate_response_is_OK_and_JSON(self, response)

            data = json.loads(response.content.decode('utf8'))
            self.assertTrue(data['checkout_allowed'])

            # Verify customer_data is None (graceful degradation)
            self.assertIsNone(data['customer_data'])
