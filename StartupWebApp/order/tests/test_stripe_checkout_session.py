# Unit tests for Stripe Checkout Session endpoint

import json
from unittest.mock import patch, MagicMock

from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from order.models import (
    Cart, Cartsku,
    Product, Productsku, Productimage,
    Sku, Skuprice, Skutype, Skuinventory,
    Orderconfiguration
)
from user.models import Member, Termsofuse

from StartupWebApp.utilities import unittest_utilities


class CreateCheckoutSessionEndpointTest(PostgreSQLTestCase):
    """Test the create_checkout_session endpoint"""

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
            identifier='PROD001',
            headline='A great test product',
            description_part_1='This is a test product'
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
            price=29.99,
            created_date_time=timezone.now()
        )

        Productsku.objects.create(product=product, sku=self.sku)

        # Create cart with items for member
        self.cart = Cart.objects.create(member=self.member)
        Cartsku.objects.create(cart=self.cart, sku=self.sku, quantity=2)

    def test_create_checkout_session_when_checkout_not_allowed(self):
        """Test that endpoint requires checkout permission"""
        # Update config to disallow checkout
        config = Orderconfiguration.objects.get(
            key='usernames_allowed_to_checkout'
        )
        config.string_value = ''
        config.save()

        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/create-checkout-session', {})

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['create_checkout_session'], 'error')
        self.assertEqual(data['errors']['error'], 'checkout-not-allowed')

    def test_create_checkout_session_when_no_cart(self):
        """Test error when user has no cart"""
        # Create user without cart
        user2 = User.objects.create_user(
            username='nocartuser',
            email='nocart@test.com',
            password='testpass123'
        )
        Member.objects.create(user=user2, mb_cd='MEMBER456')

        self.client.login(username='nocartuser', password='testpass123')

        response = self.client.post('/order/create-checkout-session', {})

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['create_checkout_session'], 'error')
        self.assertEqual(data['errors']['error'], 'cart-not-found')

    def test_create_checkout_session_when_cart_is_empty(self):
        """Test error when cart has no items"""
        # Create empty cart
        user2 = User.objects.create_user(
            username='emptycartuser',
            email='emptycart@test.com',
            password='testpass123'
        )
        member2 = Member.objects.create(user=user2, mb_cd='MEMBER789')
        Cart.objects.create(member=member2)

        self.client.login(username='emptycartuser', password='testpass123')

        response = self.client.post('/order/create-checkout-session', {})

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['create_checkout_session'], 'error')
        self.assertEqual(data['errors']['error'], 'cart-is-empty')

    @patch('stripe.checkout.Session.create')
    def test_create_checkout_session_success_for_member(self, mock_stripe_session):
        """Test successful checkout session creation for authenticated member"""
        # Mock Stripe response
        mock_session = MagicMock()
        mock_session.id = 'cs_test_123456'
        mock_session.url = 'https://checkout.stripe.com/c/pay/cs_test_123456'
        mock_stripe_session.return_value = mock_session

        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/create-checkout-session', {})

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['create_checkout_session'], 'success')
        self.assertEqual(data['session_id'], 'cs_test_123456')
        self.assertEqual(data['checkout_url'], 'https://checkout.stripe.com/c/pay/cs_test_123456')

        # Verify Stripe was called with correct parameters
        mock_stripe_session.assert_called_once()
        call_args = mock_stripe_session.call_args

        # Verify mode
        self.assertEqual(call_args.kwargs['mode'], 'payment')

        # Verify line_items
        line_items = call_args.kwargs['line_items']
        self.assertEqual(len(line_items), 1)
        self.assertEqual(line_items[0]['quantity'], 2)
        self.assertEqual(line_items[0]['price_data']['currency'], 'usd')
        self.assertEqual(line_items[0]['price_data']['unit_amount'], 2999)  # $29.99 in cents
        self.assertEqual(line_items[0]['price_data']['product_data']['name'], 'Test Product')

        # Verify product images are absolute URLs (not relative paths)
        images = line_items[0]['price_data']['product_data']['images']
        self.assertEqual(len(images), 1)
        image_url = images[0]
        self.assertTrue(image_url.startswith('http://') or image_url.startswith('https://'),
                        f"Image URL should be absolute, got: {image_url}")
        # Verify it's a valid URL (has protocol and domain)
        self.assertIn('://', image_url, "Image URL should be a complete URL with protocol")

        # Verify customer_email
        self.assertEqual(call_args.kwargs['customer_email'], 'test@test.com')

        # Verify success_url and cancel_url
        self.assertIn('success_url', call_args.kwargs)
        self.assertIn('cancel_url', call_args.kwargs)
        self.assertIn('session_id={CHECKOUT_SESSION_ID}', call_args.kwargs['success_url'])

    @patch('order.utilities.order_utils.look_up_cart')
    @patch('stripe.checkout.Session.create')
    def test_create_checkout_session_success_without_email(self, mock_stripe_session, mock_look_up_cart):
        """Test successful checkout session creation when no email provided (truly anonymous)"""
        # Mock Stripe response
        mock_session = MagicMock()
        mock_session.id = 'cs_test_789'
        mock_session.url = 'https://checkout.stripe.com/c/pay/cs_test_789'
        mock_stripe_session.return_value = mock_session

        # Create anonymous cart (no member)
        anon_cart = Cart.objects.create()
        Cartsku.objects.create(cart=anon_cart, sku=self.sku, quantity=1)

        # Mock cart lookup to return anonymous cart
        mock_look_up_cart.return_value = anon_cart

        # Don't log in - anonymous request with NO email
        response = self.client.post('/order/create-checkout-session', {})

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['create_checkout_session'], 'success')
        self.assertEqual(data['session_id'], 'cs_test_789')

        # Verify Stripe was called
        mock_stripe_session.assert_called_once()
        call_args = mock_stripe_session.call_args

        # When no email provided, customer_email should not be in params
        # (Stripe will collect it during checkout)
        self.assertNotIn('customer_email', call_args.kwargs)

    @patch('order.utilities.order_utils.look_up_cart')
    @patch('stripe.checkout.Session.create')
    def test_create_checkout_session_with_anonymous_email(self, mock_stripe_session, mock_look_up_cart):
        """Test checkout session pre-fills email for anonymous users who entered email"""
        # Mock Stripe response
        mock_session = MagicMock()
        mock_session.id = 'cs_test_anonymous'
        mock_session.url = 'https://checkout.stripe.com/c/pay/cs_test_anonymous'
        mock_stripe_session.return_value = mock_session

        # Create anonymous cart (no member)
        anon_cart = Cart.objects.create()
        Cartsku.objects.create(cart=anon_cart, sku=self.sku, quantity=1)

        # Mock cart lookup to return anonymous cart
        mock_look_up_cart.return_value = anon_cart

        # Anonymous request WITH email (from checkout form)
        response = self.client.post('/order/create-checkout-session', {
            'anonymous_email_address': 'anon@test.com'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['create_checkout_session'], 'success')

        # Verify Stripe was called with the anonymous email
        mock_stripe_session.assert_called_once()
        call_args = mock_stripe_session.call_args

        # Email should be pre-filled for Stripe checkout
        self.assertIn('customer_email', call_args.kwargs)
        self.assertEqual(call_args.kwargs['customer_email'], 'anon@test.com')

    @patch('stripe.checkout.Session.create')
    def test_create_checkout_session_handles_stripe_error(self, mock_stripe_session):
        """Test error handling when Stripe API fails"""
        # Mock Stripe error
        import stripe
        mock_stripe_session.side_effect = stripe.error.StripeError('API Error')

        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/create-checkout-session', {})

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['create_checkout_session'], 'error')
        self.assertEqual(data['errors']['error'], 'stripe-error')
        self.assertIn('description', data['errors'])

    @patch('stripe.checkout.Session.create')
    def test_create_checkout_session_calculates_total_correctly(self, mock_stripe_session):
        """Test that line items total is calculated correctly with multiple items"""
        # Mock Stripe response
        mock_session = MagicMock()
        mock_session.id = 'cs_test_multi'
        mock_session.url = 'https://checkout.stripe.com/c/pay/cs_test_multi'
        mock_stripe_session.return_value = mock_session

        # Add another SKU to cart
        skutype = Skutype.objects.get(title='product')
        skuinventory = Skuinventory.objects.get(identifier='in-stock')

        product2 = Product.objects.create(
            title='Second Product',
            title_url='SecondProduct',
            identifier='PROD002'
        )

        sku2 = Sku.objects.create(
            color='Red',
            size='Large',
            sku_type=skutype,
            sku_inventory=skuinventory,
            description='Second SKU'
        )

        Skuprice.objects.create(
            sku=sku2,
            price=49.99,
            created_date_time=timezone.now()
        )

        Productsku.objects.create(product=product2, sku=sku2)
        Productimage.objects.create(
            product=product2,
            image_url='https://example.com/product2.jpg',
            main_image=True
        )

        # Add to cart
        Cartsku.objects.create(cart=self.cart, sku=sku2, quantity=1)

        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/create-checkout-session', {})

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['create_checkout_session'], 'success')

        # Verify two product line items (no shipping in this test)
        call_args = mock_stripe_session.call_args
        line_items = call_args.kwargs['line_items']
        self.assertEqual(len(line_items), 2, "Should have 2 products")

        # Verify prices
        prices = {item['price_data']['unit_amount'] for item in line_items}
        self.assertIn(2999, prices)  # $29.99
        self.assertIn(4999, prices)  # $49.99

    @patch('stripe.checkout.Session.create')
    def test_create_checkout_session_includes_shipping_line_item(self, mock_stripe_session):
        """Test that shipping cost is included as a separate line item"""
        from order.models import Shippingmethod, Cartshippingmethod

        # Create and assign shipping method to cart
        shipping_method = Shippingmethod.objects.create(
            identifier='test-shipping',
            carrier='Test Carrier',
            shipping_cost=9.99
        )
        Cartshippingmethod.objects.create(
            cart=self.cart,
            shippingmethod=shipping_method
        )

        # Mock Stripe response
        mock_session = MagicMock()
        mock_session.id = 'cs_test_shipping'
        mock_session.url = 'https://checkout.stripe.com/c/pay/cs_test_shipping'
        mock_stripe_session.return_value = mock_session

        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/create-checkout-session', {})

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['create_checkout_session'], 'success')

        # Verify Stripe was called
        call_args = mock_stripe_session.call_args
        line_items = call_args.kwargs['line_items']

        # Should have 2 line items: 1 product + 1 shipping
        self.assertEqual(len(line_items), 2, "Should have product + shipping")

        # Find shipping line item
        shipping_items = [item for item in line_items if item['price_data']['product_data']['name'] == 'Shipping']
        self.assertEqual(len(shipping_items), 1, "Should have exactly 1 shipping line item")

        shipping_item = shipping_items[0]
        self.assertEqual(shipping_item['price_data']['product_data']['name'], 'Shipping')
        self.assertIn('description', shipping_item['price_data']['product_data'])
        self.assertEqual(shipping_item['quantity'], 1)
        self.assertGreater(shipping_item['price_data']['unit_amount'], 0, "Shipping cost should be positive")
        self.assertEqual(shipping_item['price_data']['currency'], 'usd')
