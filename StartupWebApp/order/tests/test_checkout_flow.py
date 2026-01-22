# Unit tests for checkout flow endpoints

import json

from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from order.models import (
    Cart, Cartsku, Cartshippingmethod,
    Product, Productsku, Productimage,
    Sku, Skuprice, Skutype, Skuinventory,
    Shippingmethod, Orderconfiguration
)
from user.models import Member, Termsofuse

from StartupWebApp.utilities import unittest_utilities


class CheckoutAllowedEndpointTest(PostgreSQLTestCase):
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


class ConfirmItemsEndpointTest(PostgreSQLTestCase):
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


class ConfirmShippingMethodEndpointTest(PostgreSQLTestCase):
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
        self.assertEqual(shipping_method['shipping_cost'], '5.00')


class ConfirmTotalsEndpointTest(PostgreSQLTestCase):
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
        self.assertIn('shipping_subtotal', totals)
        self.assertIn('cart_total', totals)
