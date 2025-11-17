# Unit tests for shipping methods and discount code endpoints

import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from order.models import (
    Cart, Cartdiscount, Cartshippingmethod, Shippingmethod,
    Discountcode, Discounttype, Orderconfiguration
)
from user.models import Member, Termsofuse

from StartupWebApp.utilities import unittest_utilities


class CartShippingMethodsEndpointTest(TestCase):
    """Test the cart_shipping_methods endpoint"""

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

        # Create shipping methods
        self.shipping_standard = Shippingmethod.objects.create(
            identifier='standard',
            carrier='USPS',
            shipping_cost=5.00,
            tracking_code_base_url='https://tools.usps.com/track',
            active=True
        )

        self.shipping_express = Shippingmethod.objects.create(
            identifier='express',
            carrier='FedEx',
            shipping_cost=15.00,
            tracking_code_base_url='https://www.fedex.com/track',
            active=True
        )

        self.shipping_inactive = Shippingmethod.objects.create(
            identifier='overnight',
            carrier='UPS',
            shipping_cost=25.00,
            tracking_code_base_url='https://www.ups.com/track',
            active=False
        )

        # Create order configuration for default shipping
        Orderconfiguration.objects.create(
            key='default_shipping_method',
            string_value='standard'
        )

        # Create cart
        self.cart = Cart.objects.create(member=self.member)

    def test_cart_shipping_methods_when_no_cart_exists(self):
        """Test that endpoint returns cart_found=False when no cart"""
        self.cart.delete()

        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/cart-shipping-methods')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertFalse(data['cart_found'])

    def test_cart_shipping_methods_returns_all_active_methods(self):
        """Test that endpoint returns all active shipping methods"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/cart-shipping-methods')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertTrue(data['cart_found'])

        shipping_methods = data['cart_shipping_methods']
        self.assertEqual(len(shipping_methods), 2)  # Only active methods

        # Verify methods are ordered by shipping_cost descending
        methods_list = list(shipping_methods.values())
        self.assertEqual(methods_list[0]['identifier'], 'express')  # $15
        self.assertEqual(methods_list[1]['identifier'], 'standard')  # $5

    def test_cart_shipping_methods_auto_selects_default(self):
        """Test that default shipping method is auto-selected"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/cart-shipping-methods')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['shipping_method_selected'], 'standard')

        # Verify Cartshippingmethod was created
        self.assertTrue(
            Cartshippingmethod.objects.filter(cart=self.cart).exists()
        )

    def test_cart_shipping_methods_returns_selected_method(self):
        """Test that previously selected method is returned"""
        # Manually set shipping method to express
        Cartshippingmethod.objects.create(
            cart=self.cart,
            shippingmethod=self.shipping_express
        )

        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/cart-shipping-methods')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['shipping_method_selected'], 'express')

    def test_cart_shipping_methods_includes_method_details(self):
        """Test that shipping methods include all necessary details"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/cart-shipping-methods')

        data = json.loads(response.content.decode('utf8'))
        shipping_methods = data['cart_shipping_methods']

        # Check standard method details
        standard_method = next(
            m for m in shipping_methods.values()
            if m['identifier'] == 'standard'
        )

        self.assertEqual(standard_method['carrier'], 'USPS')
        self.assertEqual(standard_method['shipping_cost'], '5.00')
        self.assertEqual(standard_method['tracking_code_base_url'],
                         'https://tools.usps.com/track')


class CartUpdateShippingMethodEndpointTest(TestCase):
    """Test the cart_update_shipping_method endpoint"""

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

        # Create shipping methods
        self.shipping_standard = Shippingmethod.objects.create(
            identifier='standard',
            carrier='USPS',
            shipping_cost=5.00,
            tracking_code_base_url='https://tools.usps.com/track'
        )

        self.shipping_express = Shippingmethod.objects.create(
            identifier='express',
            carrier='FedEx',
            shipping_cost=15.00,
            tracking_code_base_url='https://www.fedex.com/track'
        )

        # Create cart
        self.cart = Cart.objects.create(member=self.member)

    def test_cart_update_shipping_method_when_no_cart(self):
        """Test error when cart doesn't exist"""
        self.cart.delete()

        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-update-shipping-method', {
            'shipping_method_identifier': 'standard'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_update_shipping_method'], 'error')
        self.assertEqual(data['errors']['error'], 'cart-not-found')

    def test_cart_update_shipping_method_without_identifier(self):
        """Test error when shipping_method_identifier missing"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-update-shipping-method', {})

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_update_shipping_method'], 'error')
        self.assertEqual(data['errors']['error'],
                         'shipping-method-identifier-required')

    def test_cart_update_shipping_method_with_invalid_identifier(self):
        """Test error with invalid shipping method identifier"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-update-shipping-method', {
            'shipping_method_identifier': 'invalid'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_update_shipping_method'], 'error')
        self.assertEqual(data['errors']['error'],
                         'error-setting-cart-shipping-method')

    def test_cart_update_shipping_method_creates_new_association(self):
        """Test creating new cart shipping method"""
        self.client.login(username='testuser', password='testpass123')

        self.assertEqual(Cartshippingmethod.objects.count(), 0)

        response = self.client.post('/order/cart-update-shipping-method', {
            'shipping_method_identifier': 'standard'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_update_shipping_method'], 'success')

        # Verify Cartshippingmethod was created
        self.assertEqual(Cartshippingmethod.objects.count(), 1)
        cart_shipping = Cartshippingmethod.objects.first()
        self.assertEqual(cart_shipping.shippingmethod, self.shipping_standard)

    def test_cart_update_shipping_method_updates_existing(self):
        """Test updating existing cart shipping method"""
        # Create initial shipping method
        Cartshippingmethod.objects.create(
            cart=self.cart,
            shippingmethod=self.shipping_standard
        )

        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-update-shipping-method', {
            'shipping_method_identifier': 'express'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_update_shipping_method'], 'success')

        # Should still be only 1 record, but updated
        self.assertEqual(Cartshippingmethod.objects.count(), 1)
        cart_shipping = Cartshippingmethod.objects.first()
        self.assertEqual(cart_shipping.shippingmethod, self.shipping_express)

    def test_cart_update_shipping_method_returns_updated_totals(self):
        """Test that response includes updated cart totals"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-update-shipping-method', {
            'shipping_method_identifier': 'express'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertIn('cart_totals_data', data)
        self.assertIn('discount_code_data', data)


class CartDiscountCodesEndpointTest(TestCase):
    """Test the cart_discount_codes endpoint"""

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

        # Create discount type
        self.discount_type = Discounttype.objects.create(
            title='Percentage Off',
            description='Percentage off entire order',
            applies_to='order',
            action='percentage_off'
        )

        # Create discount code
        now = timezone.now()
        self.discount_code = Discountcode.objects.create(
            code='SAVE10',
            description='10% off',
            start_date_time=now,
            end_date_time=now + timezone.timedelta(days=30),
            combinable=True,
            discounttype=self.discount_type,
            discount_amount=10.0,
            order_minimum=20.0
        )

        # Create cart
        self.cart = Cart.objects.create(member=self.member)

    def test_cart_discount_codes_when_no_cart(self):
        """Test endpoint when cart doesn't exist"""
        self.cart.delete()

        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/cart-discount-codes')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertFalse(data['cart_found'])

    def test_cart_discount_codes_with_no_discounts(self):
        """Test endpoint returns empty when no discounts applied"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/cart-discount-codes')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertTrue(data['cart_found'])
        self.assertEqual(data['discount_code_data'], {})

    def test_cart_discount_codes_returns_applied_discounts(self):
        """Test endpoint returns applied discount codes"""
        # Apply discount to cart
        Cartdiscount.objects.create(
            cart=self.cart,
            discountcode=self.discount_code
        )

        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/cart-discount-codes')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        discount_codes = data['discount_code_data']

        self.assertEqual(len(discount_codes), 1)

        discount_data = discount_codes[str(self.discount_code.id)]
        self.assertEqual(discount_data['code'], 'SAVE10')
        self.assertEqual(discount_data['description'], '10% off')
        self.assertEqual(discount_data['discount_amount'], '10.00')


class CartApplyDiscountCodeEndpointTest(TestCase):
    """Test the cart_apply_discount_code endpoint"""

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

        # Create discount type
        self.discount_type = Discounttype.objects.create(
            title='Percentage Off',
            description='Percentage off entire order',
            applies_to='order',
            action='percentage_off'
        )

        # Create active discount code
        now = timezone.now()
        self.discount_active = Discountcode.objects.create(
            code='SAVE10',
            description='10% off',
            start_date_time=now - timezone.timedelta(days=1),
            end_date_time=now + timezone.timedelta(days=30),
            combinable=True,
            discounttype=self.discount_type,
            discount_amount=10.0,
            order_minimum=0
        )

        # Create inactive (future) discount code
        self.discount_future = Discountcode.objects.create(
            code='FUTURE20',
            description='20% off',
            start_date_time=now + timezone.timedelta(days=10),
            end_date_time=now + timezone.timedelta(days=40),
            combinable=True,
            discounttype=self.discount_type,
            discount_amount=20.0,
            order_minimum=0
        )

        # Create expired discount code
        self.discount_expired = Discountcode.objects.create(
            code='EXPIRED',
            description='Expired discount',
            start_date_time=now - timezone.timedelta(days=30),
            end_date_time=now - timezone.timedelta(days=1),
            combinable=True,
            discounttype=self.discount_type,
            discount_amount=15.0,
            order_minimum=0
        )

        # Create cart
        self.cart = Cart.objects.create(member=self.member)

    def test_cart_apply_discount_code_when_no_cart(self):
        """Test error when cart doesn't exist"""
        self.cart.delete()

        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-apply-discount-code', {
            'discount_code_id': 'SAVE10'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_apply_discount_code'], 'error')
        self.assertEqual(data['errors']['error'], 'cart-not-found')

    def test_cart_apply_discount_code_without_code(self):
        """Test error when discount_code_id missing"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-apply-discount-code', {})

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_apply_discount_code'], 'error')
        self.assertEqual(data['errors']['error'], 'discount-code-required')

    def test_cart_apply_discount_code_with_invalid_code(self):
        """Test error with non-existent discount code"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-apply-discount-code', {
            'discount_code_id': 'INVALID'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_apply_discount_code'], 'error')
        self.assertEqual(data['errors']['error'], 'cart-discount-code-not-found')

    def test_cart_apply_discount_code_not_yet_active(self):
        """Test error when discount code not yet active"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-apply-discount-code', {
            'discount_code_id': 'FUTURE20'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_apply_discount_code'], 'error')
        self.assertEqual(data['errors']['error'], 'cart-discount-code-not-active')

    def test_cart_apply_discount_code_expired(self):
        """Test error when discount code has expired"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-apply-discount-code', {
            'discount_code_id': 'EXPIRED'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_apply_discount_code'], 'error')
        self.assertEqual(data['errors']['error'], 'cart-discount-code-not-active')

    def test_cart_apply_discount_code_already_applied(self):
        """Test error when discount code already applied"""
        # Apply discount first time
        Cartdiscount.objects.create(
            cart=self.cart,
            discountcode=self.discount_active
        )

        self.client.login(username='testuser', password='testpass123')

        # Try to apply again
        response = self.client.post('/order/cart-apply-discount-code', {
            'discount_code_id': 'SAVE10'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_apply_discount_code'], 'error')
        self.assertEqual(data['errors']['error'],
                         'cart-discount-code-already-applied')

    def test_cart_apply_discount_code_success(self):
        """Test successful discount code application"""
        self.client.login(username='testuser', password='testpass123')

        self.assertEqual(Cartdiscount.objects.count(), 0)

        response = self.client.post('/order/cart-apply-discount-code', {
            'discount_code_id': 'SAVE10'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_apply_discount_code'], 'success')

        # Verify Cartdiscount was created
        self.assertEqual(Cartdiscount.objects.count(), 1)
        cart_discount = Cartdiscount.objects.first()
        self.assertEqual(cart_discount.discountcode, self.discount_active)

    def test_cart_apply_discount_code_returns_updated_data(self):
        """Test that response includes updated discount and totals"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-apply-discount-code', {
            'discount_code_id': 'SAVE10'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertIn('discount_code_data', data)
        self.assertIn('cart_totals_data', data)


class CartRemoveDiscountCodeEndpointTest(TestCase):
    """Test the cart_remove_discount_code endpoint"""

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

        # Create discount type
        discount_type = Discounttype.objects.create(
            title='Percentage Off',
            description='Percentage off entire order',
            applies_to='order',
            action='percentage_off'
        )

        # Create discount code
        now = timezone.now()
        self.discount_code = Discountcode.objects.create(
            code='SAVE10',
            description='10% off',
            start_date_time=now,
            end_date_time=now + timezone.timedelta(days=30),
            combinable=True,
            discounttype=discount_type,
            discount_amount=10.0,
            order_minimum=0
        )

        # Create cart with discount applied
        self.cart = Cart.objects.create(member=self.member)
        self.cart_discount = Cartdiscount.objects.create(
            cart=self.cart,
            discountcode=self.discount_code
        )

    def test_cart_remove_discount_code_when_no_cart(self):
        """Test error when cart doesn't exist"""
        self.cart.delete()

        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-remove-discount-code', {
            'discount_code_id': str(self.discount_code.id)
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_remove_discount_code'], 'error')
        self.assertEqual(data['errors']['error'], 'cart-not-found')

    def test_cart_remove_discount_code_without_id(self):
        """Test error when discount_code_id missing"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-remove-discount-code', {})

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_remove_discount_code'], 'error')
        self.assertEqual(data['errors']['error'], 'discount-code-required')

    def test_cart_remove_discount_code_with_invalid_id(self):
        """Test error with non-existent discount code ID"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-remove-discount-code', {
            'discount_code_id': '999'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_remove_discount_code'], 'error')
        self.assertEqual(data['errors']['error'], 'cart-discount-code-not-found')

    def test_cart_remove_discount_code_success(self):
        """Test successful discount code removal"""
        self.client.login(username='testuser', password='testpass123')

        self.assertEqual(Cartdiscount.objects.count(), 1)

        response = self.client.post('/order/cart-remove-discount-code', {
            'discount_code_id': str(self.discount_code.id)
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_remove_discount_code'], 'success')

        # Verify Cartdiscount was deleted
        self.assertEqual(Cartdiscount.objects.count(), 0)

    def test_cart_remove_discount_code_returns_updated_data(self):
        """Test that response includes updated discount and totals"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-remove-discount-code', {
            'discount_code_id': str(self.discount_code.id)
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertIn('discount_code_data', data)
        self.assertIn('cart_totals_data', data)
