# Unit tests for login endpoint

import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from clientevent.models import Configuration as ClientEventConfiguration
from order.models import Cart, Cartsku, Skutype, Skuinventory, Product, Sku, Skuprice, Productsku
from user.models import Member, Termsofuse

from StartupWebApp.utilities import unittest_utilities


class LoginAPITest(TestCase):

    def setUp(self):
        # Setup necessary DB Objects
        ClientEventConfiguration.objects.create(id=1, log_client_events=True)

        Skutype.objects.create(id=1, title='product')
        Skuinventory.objects.create(id=1, title='In Stock', identifier='in-stock', description='In Stock items are available to purchase.')
        Product.objects.create(id=1, title='Paper Clips', title_url='PaperClips', identifier='bSusp6dBHm', headline='Paper clips can hold up to 20 pieces of paper together!', description_part_1='Made out of high quality metal and folded to exact specifications.', description_part_2='Use paperclips for all your paper binding needs!')
        Sku.objects.create(id=1, color='Silver', size='Medium', sku_type_id=1, description='Left Sided Paperclip', sku_inventory_id=1)
        Skuprice.objects.create(id=1, price=3.5, created_date_time=timezone.now(), sku_id=1)
        Productsku.objects.create(id=1, product_id=1, sku_id=1)
        Group.objects.create(name='Members')
        Termsofuse.objects.create(version='1', version_note='Test Terms', publication_date_time=timezone.now())

        # Create a test user for login tests
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
        # Logout after creating user so we can test login
        self.client.post('/user/logout')

    def test_valid_login(self):
        """Test successful login with valid credentials"""
        response = self.client.post('/user/login', data={
            'username': 'testuser',
            'password': 'ValidPass1!',
            'remember_me': 'false'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                            '{"login": "true", "user-api-version": "0.0.1"}',
                            'Valid login failed')

        # Verify user is actually logged in
        response = self.client.get('/user/logged-in')
        response_data = json.loads(response.content.decode('utf8'))
        self.assertTrue(response_data['logged_in'], 'User should be logged in after successful login')

    def test_invalid_password(self):
        """Test login with correct username but wrong password"""
        response = self.client.post('/user/login', data={
            'username': 'testuser',
            'password': 'WrongPassword1!',
            'remember_me': 'false'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                            '{"login": "false", "user-api-version": "0.0.1"}',
                            'Login with invalid password should fail')

        # Verify user is NOT logged in
        response = self.client.get('/user/logged-in')
        response_data = json.loads(response.content.decode('utf8'))
        self.assertFalse(response_data['logged_in'], 'User should not be logged in after failed login')

    def test_nonexistent_username(self):
        """Test login with username that doesn't exist"""
        response = self.client.post('/user/login', data={
            'username': 'nonexistentuser',
            'password': 'ValidPass1!',
            'remember_me': 'false'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                            '{"login": "false", "user-api-version": "0.0.1"}',
                            'Login with nonexistent username should fail')

    def test_remember_me_true(self):
        """Test login with remember_me=true (session should persist)"""
        response = self.client.post('/user/login', data={
            'username': 'testuser',
            'password': 'ValidPass1!',
            'remember_me': 'true'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                            '{"login": "true", "user-api-version": "0.0.1"}',
                            'Login with remember_me=true failed')

        # Check session expiry (should NOT expire at browser close)
        expire_at_browser_close = self.client.session.get_expire_at_browser_close()
        self.assertFalse(expire_at_browser_close, 'Remember me session should not expire at browser close')

    def test_remember_me_false(self):
        """Test login with remember_me=false (session expires at browser close)"""
        response = self.client.post('/user/login', data={
            'username': 'testuser',
            'password': 'ValidPass1!',
            'remember_me': 'false'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                            '{"login": "true", "user-api-version": "0.0.1"}',
                            'Login with remember_me=false failed')

        # Check session expiry (should expire at browser close)
        expire_at_browser_close = self.client.session.get_expire_at_browser_close()
        self.assertTrue(expire_at_browser_close, 'Session should expire at browser close when remember_me=false')

    def test_cart_merge_on_login(self):
        """Test that anonymous cart items are merged into member cart on login"""
        # Add item to anonymous cart
        self.client.post('/order/cart-add-product-sku', data={'sku_id': '1', 'quantity': '2'})

        # Verify anonymous cart has item
        response = self.client.get('/user/logged-in')
        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['cart_item_count'], 1, 'Anonymous cart should have 1 item')

        # Login
        self.client.post('/user/login', data={
            'username': 'testuser',
            'password': 'ValidPass1!',
            'remember_me': 'false'
        })

        # Verify member cart now has the item
        response = self.client.get('/user/logged-in')
        response_data = json.loads(response.content.decode('utf8'))
        self.assertTrue(response_data['logged_in'], 'User should be logged in')
        self.assertEqual(response_data['cart_item_count'], 1, 'Member cart should have merged anonymous cart item')

        # Verify anonymous cart was deleted
        anonymous_carts = Cart.objects.filter(member__isnull=True, anonymous_cart_id__isnull=False)
        self.assertEqual(anonymous_carts.count(), 0, 'Anonymous cart should be deleted after merge')

    def test_login_with_existing_member_cart(self):
        """Test login when member already has items in cart - should merge without duplicates"""
        # First login and add item to member cart
        self.client.post('/user/login', data={
            'username': 'testuser',
            'password': 'ValidPass1!',
            'remember_me': 'false'
        })
        self.client.post('/order/cart-add-product-sku', data={'sku_id': '1', 'quantity': '3'})

        # Verify member cart has item
        response = self.client.get('/user/logged-in')
        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['cart_item_count'], 1, 'Member cart should have 1 item')

        # Logout
        self.client.post('/user/logout')

        # Add same item to anonymous cart
        self.client.post('/order/cart-add-product-sku', data={'sku_id': '1', 'quantity': '1'})

        # Login again (should not duplicate the SKU)
        self.client.post('/user/login', data={
            'username': 'testuser',
            'password': 'ValidPass1!',
            'remember_me': 'false'
        })

        # Verify cart still has only 1 unique item (not duplicated)
        response = self.client.get('/user/logged-in')
        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['cart_item_count'], 1, 'Member cart should still have 1 item (no duplicates)')

        # Verify the original quantity is preserved (not merged)
        user = User.objects.get(username='testuser')
        member_cart = Cart.objects.get(member=user.member)
        cart_sku = Cartsku.objects.get(cart=member_cart, sku_id=1)
        self.assertEqual(cart_sku.quantity, 3, 'Original member cart quantity should be preserved')

    def test_case_sensitive_username(self):
        """Test that username is case-sensitive"""
        # Django usernames are case-sensitive by default
        response = self.client.post('/user/login', data={
            'username': 'TESTUSER',  # Wrong case
            'password': 'ValidPass1!',
            'remember_me': 'false'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                            '{"login": "false", "user-api-version": "0.0.1"}',
                            'Login with wrong case username should fail')
