# Unit tests for logout endpoint

import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from clientevent.models import Configuration as ClientEventConfiguration
from order.models import Cart, Cartsku, Skutype, Skuinventory, Product, Sku, Skuprice, Productsku
from user.models import Member, Termsofuse

from StartupWebApp.utilities import unittest_utilities


class LogoutAPITest(TestCase):

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

        # Create a test user
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

    def test_successful_logout(self):
        """Test successful logout for authenticated user"""
        # Verify user is logged in
        response = self.client.get('/user/logged-in')
        response_data = json.loads(response.content.decode('utf8'))
        self.assertTrue(response_data['logged_in'], 'User should be logged in initially')

        # Logout
        response = self.client.post('/user/logout')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                            '{"logout": "true", "user-api-version": "0.0.1"}',
                            'Logout should succeed')

        # Verify user is logged out
        response = self.client.get('/user/logged-in')
        response_data = json.loads(response.content.decode('utf8'))
        self.assertFalse(response_data['logged_in'], 'User should be logged out after logout')

    def test_logout_clears_session(self):
        """Test that logout clears the session"""
        # Login
        self.client.post('/user/login', data={
            'username': 'testuser',
            'password': 'ValidPass1!',
            'remember_me': 'false'
        })

        # Store session key
        session_key_before = self.client.session.session_key

        # Logout
        response = self.client.post('/user/logout')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        # Session should be cleared/changed
        session_key_after = self.client.session.session_key
        self.assertNotEqual(session_key_before, session_key_after, 'Session should be cleared after logout')

    def test_logout_when_not_authenticated(self):
        """Test logout when user is not authenticated"""
        # First logout to ensure we're anonymous
        self.client.post('/user/logout')

        # Try to logout again as anonymous user
        response = self.client.post('/user/logout')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                            '{"logout": "user_not_authenticated", "user-api-version": "0.0.1"}',
                            'Logout for anonymous user should return user_not_authenticated')

    def test_logout_sets_anonymous_client_event_cookie(self):
        """Test that logout sets anonymousclientevent cookie"""
        # Logout
        response = self.client.post('/user/logout')

        # Check that anonymousclientevent cookie is set
        self.assertIn('anonymousclientevent', response.cookies, 'anonymousclientevent cookie should be set on logout')

        # Verify cookie properties
        cookie = response.cookies['anonymousclientevent']
        self.assertEqual(cookie['domain'], '.startupwebapp.com', 'Cookie domain should be .startupwebapp.com')
        self.assertEqual(cookie['path'], '/', 'Cookie path should be /')
        self.assertEqual(int(cookie['max-age']), 31536000, 'Cookie should have 1 year max-age')

    def test_multiple_logouts(self):
        """Test that multiple logout calls don't cause errors"""
        # First logout
        response = self.client.post('/user/logout')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                            '{"logout": "true", "user-api-version": "0.0.1"}',
                            'First logout should succeed')

        # Second logout
        response = self.client.post('/user/logout')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                            '{"logout": "user_not_authenticated", "user-api-version": "0.0.1"}',
                            'Second logout should return user_not_authenticated')

    def test_logout_with_cart_items(self):
        """Test logout when user has items in cart"""
        # Add items to cart while logged in
        self.client.post('/order/cart-add-product-sku', data={'sku_id': '1', 'quantity': '2'})

        # Verify cart has items
        response = self.client.get('/user/logged-in')
        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['cart_item_count'], 1, 'Cart should have 1 item before logout')

        # Logout
        response = self.client.post('/user/logout')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        # Verify logout succeeded
        self.assertJSONEqual(response.content.decode('utf8'),
                            '{"logout": "true", "user-api-version": "0.0.1"}',
                            'Logout with cart items should succeed')

        # Verify user is logged out but cart is preserved
        response = self.client.get('/user/logged-in')
        response_data = json.loads(response.content.decode('utf8'))
        self.assertFalse(response_data['logged_in'], 'User should be logged out')
        # Note: Cart items should still be in member's cart in database, not converted to anonymous

    def test_login_logout_login_cycle(self):
        """Test that user can login, logout, and login again successfully"""
        # First login
        response = self.client.post('/user/login', data={
            'username': 'testuser',
            'password': 'ValidPass1!',
            'remember_me': 'false'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        # Logout
        response = self.client.post('/user/logout')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        # Login again
        response = self.client.post('/user/login', data={
            'username': 'testuser',
            'password': 'ValidPass1!',
            'remember_me': 'false'
        })
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'),
                            '{"login": "true", "user-api-version": "0.0.1"}',
                            'Second login should succeed')

        # Verify user is logged in
        response = self.client.get('/user/logged-in')
        response_data = json.loads(response.content.decode('utf8'))
        self.assertTrue(response_data['logged_in'], 'User should be logged in after second login')
