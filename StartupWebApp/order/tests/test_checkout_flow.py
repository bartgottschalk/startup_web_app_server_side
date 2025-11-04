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
