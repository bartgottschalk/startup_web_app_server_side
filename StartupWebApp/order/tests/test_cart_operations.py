# Unit tests for cart operations endpoints

import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from order.models import (
    Cart, Cartsku, Product, Productsku,
    Productimage, Sku, Skuprice,
    Skutype, Skuinventory
)
from user.models import Member, Termsofuse

from StartupWebApp.utilities import unittest_utilities


class CartItemsEndpointTest(TestCase):
    """Test the cart_items endpoint"""

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

        # Create SKU and product
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

    def test_cart_items_when_no_cart_exists(self):
        """Test cart_items returns empty when no cart exists"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/cart-items')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertFalse(data['cart_found'])
        self.assertEqual(data['item_data'], {})

    def test_cart_items_returns_items_in_cart(self):
        """Test cart_items returns all items in member's cart"""
        self.client.login(username='testuser', password='testpass123')

        # Create cart with items
        cart = Cart.objects.create(member=self.member)
        Cartsku.objects.create(cart=cart, sku=self.sku, quantity=2)

        response = self.client.get('/order/cart-items')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertTrue(data['cart_found'])
        self.assertIn('item_data', data)
        self.assertIn('product_sku_data', data['item_data'])

        product_sku_data = data['item_data']['product_sku_data']
        self.assertEqual(len(product_sku_data), 1)

        item = list(product_sku_data.values())[0]
        self.assertEqual(item['sku_id'], self.sku.id)
        self.assertEqual(item['quantity'], 2)
        self.assertEqual(item['price'], 10.00)
        self.assertEqual(item['parent_product__title'], 'Test Product')

    def test_cart_items_anonymous_with_no_cart(self):
        """Test cart_items for anonymous user with no cart"""
        response = self.client.get('/order/cart-items')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertFalse(data['cart_found'])


class CartAddProductSkuEndpointTest(TestCase):
    """Test the cart_add_product_sku endpoint"""

    def setUp(self):
        # Create SKU and product
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
            sku_inventory=skuinventory
        )

        Skuprice.objects.create(
            sku=self.sku,
            price=10.00,
            created_date_time=timezone.now()
        )

        Productsku.objects.create(product=product, sku=self.sku)

    def test_cart_add_product_sku_without_sku_id_returns_error(self):
        """Test that missing sku_id returns error"""
        response = self.client.post('/order/cart-add-product-sku', {
            'quantity': '1'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_add_product_sku'], 'error')
        self.assertEqual(data['errors']['error'], 'sku-id-required')

    def test_cart_add_product_sku_with_invalid_sku_returns_error(self):
        """Test that invalid sku_id returns error"""
        response = self.client.post('/order/cart-add-product-sku', {
            'sku_id': '999',
            'quantity': '1'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_add_product_sku'], 'error')
        self.assertEqual(data['errors']['error'], 'sku-not-found')

    def test_cart_add_product_sku_with_invalid_quantity_returns_error(self):
        """Test that invalid quantity returns validation error"""
        # Quantity out of range (>99)
        response = self.client.post('/order/cart-add-product-sku', {
            'sku_id': str(self.sku.id),
            'quantity': '100'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_add_product_sku'], 'error')
        self.assertIn('quantity', data['errors'])

        # Quantity not an int
        response = self.client.post('/order/cart-add-product-sku', {
            'sku_id': str(self.sku.id),
            'quantity': 'x'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_add_product_sku'], 'error')
        self.assertIn('quantity', data['errors'])

    def test_cart_add_product_sku_creates_new_cart_if_none_exists(self):
        """Test that cart is created if it doesn't exist"""
        self.assertEqual(Cart.objects.count(), 0)

        response = self.client.post('/order/cart-add-product-sku', {
            'sku_id': str(self.sku.id),
            'quantity': '1'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_add_product_sku'], 'success')
        self.assertEqual(Cart.objects.count(), 1)

    def test_cart_add_product_sku_adds_new_item_to_cart(self):
        """Test that new item is added to cart"""
        response = self.client.post('/order/cart-add-product-sku', {
            'sku_id': str(self.sku.id),
            'quantity': '2'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_add_product_sku'], 'success')
        self.assertEqual(data['cart_item_count'], 1)

        # Verify cartsku was created
        self.assertEqual(Cartsku.objects.count(), 1)
        cartsku = Cartsku.objects.first()
        self.assertEqual(cartsku.sku, self.sku)
        self.assertEqual(cartsku.quantity, 2)

    def test_cart_add_product_sku_increments_existing_item_quantity(self):
        """Test that adding same SKU increments quantity"""
        # Add item first time
        self.client.post('/order/cart-add-product-sku', {
            'sku_id': str(self.sku.id),
            'quantity': '2'
        })

        # Add same item again
        response = self.client.post('/order/cart-add-product-sku', {
            'sku_id': str(self.sku.id),
            'quantity': '3'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_add_product_sku'], 'success')

        # Should still be only 1 cartsku, but quantity should be 5
        self.assertEqual(Cartsku.objects.count(), 1)
        cartsku = Cartsku.objects.first()
        self.assertEqual(cartsku.quantity, 5)

    def test_cart_add_product_sku_for_authenticated_member(self):
        """Test adding product to cart for authenticated member"""
        Group.objects.create(name='Members')
        Termsofuse.objects.create(
            version='1',
            version_note='Test',
            publication_date_time=timezone.now()
        )

        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        member = Member.objects.create(user=user, mb_cd='MEMBER123')

        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-add-product-sku', {
            'sku_id': str(self.sku.id),
            'quantity': '1'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_add_product_sku'], 'success')

        # Verify cart is associated with member
        cart = Cart.objects.first()
        self.assertEqual(cart.member, member)


class CartUpdateSkuQuantityEndpointTest(TestCase):
    """Test the cart_update_sku_quantity endpoint"""

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

        # Create SKU and product
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

        # Create cart with item
        self.cart = Cart.objects.create(member=self.member)
        self.cartsku = Cartsku.objects.create(
            cart=self.cart,
            sku=self.sku,
            quantity=2
        )

    def test_cart_update_sku_quantity_when_no_cart_exists(self):
        """Test that error is returned when cart doesn't exist"""
        # Delete the cart
        self.cart.delete()

        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-update-sku-quantity', {
            'sku_id': str(self.sku.id),
            'quantity': '5'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_update_sku_quantity'], 'error')
        self.assertEqual(data['errors']['error'], 'cart-not-found')

    def test_cart_update_sku_quantity_without_sku_id(self):
        """Test that missing sku_id returns error"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-update-sku-quantity', {
            'quantity': '5'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_update_sku_quantity'], 'error')
        self.assertEqual(data['errors']['error'], 'sku-id-required')

    def test_cart_update_sku_quantity_with_invalid_sku(self):
        """Test that invalid sku_id returns error"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-update-sku-quantity', {
            'sku_id': '999',
            'quantity': '5'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_update_sku_quantity'], 'error')
        self.assertEqual(data['errors']['error'], 'cart-sku-not-found')

    def test_cart_update_sku_quantity_success(self):
        """Test successful quantity update"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-update-sku-quantity', {
            'sku_id': str(self.sku.id),
            'quantity': '5'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_update_sku_quantity'], 'success')
        self.assertTrue(data['cart_found'])
        self.assertIn('sku_subtotal', data)
        self.assertEqual(data['sku_subtotal'], 50.00)  # 5 * 10.00

        # Verify quantity was updated
        self.cartsku.refresh_from_db()
        self.assertEqual(self.cartsku.quantity, 5)

    def test_cart_update_sku_quantity_returns_updated_totals(self):
        """Test that response includes updated cart totals"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-update-sku-quantity', {
            'sku_id': str(self.sku.id),
            'quantity': '3'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertIn('cart_totals_data', data)
        self.assertIn('discount_code_data', data)


class CartRemoveSkuEndpointTest(TestCase):
    """Test the cart_remove_sku endpoint"""

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

        # Create SKU and product
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

        # Create cart with item
        self.cart = Cart.objects.create(member=self.member)
        self.cartsku = Cartsku.objects.create(
            cart=self.cart,
            sku=self.sku,
            quantity=2
        )

    def test_cart_remove_sku_when_no_cart_exists(self):
        """Test that error is returned when cart doesn't exist"""
        self.cart.delete()

        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-remove-sku', {
            'sku_id': str(self.sku.id)
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_remove_sku'], 'error')
        self.assertEqual(data['errors']['error'], 'cart-not-found')

    def test_cart_remove_sku_without_sku_id(self):
        """Test that missing sku_id returns error"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-remove-sku', {})

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_remove_sku'], 'error')
        self.assertEqual(data['errors']['error'], 'sku-id-required')

    def test_cart_remove_sku_with_invalid_sku(self):
        """Test that invalid sku_id returns error"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-remove-sku', {
            'sku_id': '999'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_remove_sku'], 'error')
        self.assertEqual(data['errors']['error'], 'cart-sku-not-found')

    def test_cart_remove_sku_success(self):
        """Test successful SKU removal from cart"""
        self.client.login(username='testuser', password='testpass123')

        self.assertEqual(Cartsku.objects.count(), 1)

        response = self.client.post('/order/cart-remove-sku', {
            'sku_id': str(self.sku.id)
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_remove_sku'], 'success')
        self.assertEqual(data['cart_item_count'], 0)

        # Verify cartsku was deleted
        self.assertEqual(Cartsku.objects.count(), 0)

    def test_cart_remove_sku_returns_updated_data(self):
        """Test that response includes updated cart data"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-remove-sku', {
            'sku_id': str(self.sku.id)
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertIn('cart_shipping_methods', data)
        self.assertIn('cart_totals_data', data)
        self.assertIn('discount_code_data', data)

    def test_cart_remove_sku_deletes_existing_shipping_method(self):
        """Test that removing SKU also deletes cart's selected shipping method"""
        from order.models import Shippingmethod, Cartshippingmethod

        # Create a shipping method and assign it to cart
        shipping_method = Shippingmethod.objects.create(
            identifier='standard',
            carrier='USPS',
            shipping_cost=5.00,
            active=True
        )
        cart_shipping_method = Cartshippingmethod.objects.create(
            cart=self.cart,
            shippingmethod=shipping_method
        )

        self.client.login(username='testuser', password='testpass123')

        # Verify shipping method is assigned to cart
        self.assertTrue(Cartshippingmethod.objects.filter(cart=self.cart).exists())

        response = self.client.post('/order/cart-remove-sku', {
            'sku_id': str(self.sku.id)
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_remove_sku'], 'success')

        # Verify shipping method was deleted from cart
        self.assertFalse(Cartshippingmethod.objects.filter(cart=self.cart).exists())

    def test_cart_remove_sku_returns_available_shipping_methods(self):
        """Test that response includes available shipping methods when they exist"""
        from order.models import Shippingmethod

        # Create active shipping methods
        shipping_method_1 = Shippingmethod.objects.create(
            identifier='express',
            carrier='FedEx',
            shipping_cost=15.00,
            tracking_code_base_url='https://www.fedex.com/track',
            active=True
        )
        shipping_method_2 = Shippingmethod.objects.create(
            identifier='standard',
            carrier='USPS',
            shipping_cost=5.00,
            tracking_code_base_url='https://tools.usps.com/track',
            active=True
        )

        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-remove-sku', {
            'sku_id': str(self.sku.id)
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_remove_sku'], 'success')

        # Verify shipping methods are in response (ordered by shipping_cost descending)
        cart_shipping_methods = data['cart_shipping_methods']
        self.assertEqual(len(cart_shipping_methods), 2)

        # Shipping methods are returned as dict with numeric keys: {0: {...}, 1: {...}}
        # First method should be express (higher cost)
        self.assertIn('0', cart_shipping_methods)
        self.assertEqual(cart_shipping_methods['0']['identifier'], 'express')
        self.assertEqual(cart_shipping_methods['0']['carrier'], 'FedEx')
        self.assertEqual(cart_shipping_methods['0']['shipping_cost'], 15.00)
        self.assertEqual(cart_shipping_methods['0']['tracking_code_base_url'], 'https://www.fedex.com/track')

        # Second method should be standard (lower cost)
        self.assertIn('1', cart_shipping_methods)
        self.assertEqual(cart_shipping_methods['1']['identifier'], 'standard')
        self.assertEqual(cart_shipping_methods['1']['carrier'], 'USPS')
        self.assertEqual(cart_shipping_methods['1']['shipping_cost'], 5.00)


class CartDeleteCartEndpointTest(TestCase):
    """Test the cart_delete_cart endpoint"""

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

        # Create cart
        self.cart = Cart.objects.create(member=self.member)

    def test_cart_delete_cart_when_no_cart_exists(self):
        """Test that error is returned when cart doesn't exist"""
        self.cart.delete()

        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/cart-delete-cart', {})

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_delete_cart'], 'error')
        self.assertEqual(data['errors']['error'], 'cart-not-found')

    def test_cart_delete_cart_success(self):
        """Test successful cart deletion"""
        self.client.login(username='testuser', password='testpass123')

        self.assertEqual(Cart.objects.count(), 1)

        response = self.client.post('/order/cart-delete-cart', {})

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['cart_delete_cart'], 'success')

        # Verify cart was deleted
        self.assertEqual(Cart.objects.count(), 0)

    def test_cart_delete_cart_cascades_to_cartsku(self):
        """Test that deleting cart also deletes related cartskus"""
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

        sku = Sku.objects.create(
            color='Blue',
            size='Medium',
            sku_type=skutype,
            sku_inventory=skuinventory
        )

        Skuprice.objects.create(
            sku=sku,
            price=10.00,
            created_date_time=timezone.now()
        )

        Productsku.objects.create(product=product, sku=sku)

        Cartsku.objects.create(cart=self.cart, sku=sku, quantity=2)

        self.client.login(username='testuser', password='testpass123')

        self.assertEqual(Cartsku.objects.count(), 1)

        self.client.post('/order/cart-delete-cart', {})

        # Verify cartsku was also deleted via CASCADE
        self.assertEqual(Cartsku.objects.count(), 0)


class CartTotalsEndpointTest(TestCase):
    """Test the cart_totals endpoint"""

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

        # Create SKU and product
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
            sku_inventory=skuinventory
        )

        Skuprice.objects.create(
            sku=self.sku,
            price=10.00,
            created_date_time=timezone.now()
        )

        Productsku.objects.create(product=product, sku=self.sku)

        # Create cart with item
        self.cart = Cart.objects.create(member=self.member)
        Cartsku.objects.create(cart=self.cart, sku=self.sku, quantity=3)

    def test_cart_totals_when_no_cart_exists(self):
        """Test cart_totals returns empty when no cart exists"""
        self.cart.delete()

        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/cart-totals')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertFalse(data['cart_found'])

    def test_cart_totals_calculates_item_subtotal(self):
        """Test that cart_totals correctly calculates item subtotal"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/cart-totals')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertTrue(data['cart_found'])

        cart_totals = data['cart_totals_data']
        self.assertEqual(cart_totals['item_subtotal'], 30.00)  # 3 * 10.00

    def test_cart_totals_includes_all_fields(self):
        """Test that cart_totals includes all required fields"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/cart-totals')

        data = json.loads(response.content.decode('utf8'))
        cart_totals = data['cart_totals_data']

        self.assertIn('item_subtotal', cart_totals)
        self.assertIn('item_discount', cart_totals)
        self.assertIn('shipping_subtotal', cart_totals)
        self.assertIn('shipping_discount', cart_totals)
        self.assertIn('cart_total', cart_totals)
