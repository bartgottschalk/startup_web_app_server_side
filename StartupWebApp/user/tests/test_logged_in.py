# Unit tests for logged in endpoint

import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from clientevent.models import Configuration as ClientEventConfiguration
from order.models import Cart, Cartsku, Skutype, Skuinventory, Product, Sku, Skuprice, Productsku
from user.models import Termsofuse

from StartupWebApp.utilities import unittest_utilities


class LoggedInAPITest(TestCase):

    def setUp(self):
        # Setup necessary DB Objects
        ClientEventConfiguration.objects.create(id=1, log_client_events=True)

        Skutype.objects.create(id=1, title='product')
        Skuinventory.objects.create(id=1, title='In Stock', identifier='in-stock', description='In Stock items are available to purchase.')
        Product.objects.create(id=1, title='Paper Clips', title_url='PaperClips', identifier='bSusp6dBHm', headline='Paper clips can hold up to 20 pieces of paper together!', description_part_1='Made out of high quality metal and folded to exact specifications.', description_part_2='Use paperclips for all your paper binding needs!')
        Sku.objects.create(id=1, color='Silver', size='Medium', sku_type_id=1, description='Left Sided Paperclip', sku_inventory_id=1)
        Sku.objects.create(id=2, color='Gold', size='Large', sku_type_id=1, description='Right Sided Paperclip', sku_inventory_id=1)
        Sku.objects.create(id=3, color='Bronze', size='Small', sku_type_id=1, description='Center Paperclip', sku_inventory_id=1)
        Skuprice.objects.create(id=1, price=3.5, created_date_time=timezone.now(), sku_id=1)
        Skuprice.objects.create(id=2, price=4.5, created_date_time=timezone.now(), sku_id=2)
        Skuprice.objects.create(id=3, price=2.5, created_date_time=timezone.now(), sku_id=3)
        Productsku.objects.create(id=1, product_id=1, sku_id=1)
        Productsku.objects.create(id=2, product_id=1, sku_id=2)
        Productsku.objects.create(id=3, product_id=1, sku_id=3)
        Group.objects.create(name='Members')
        Termsofuse.objects.create(version='1', version_note='Test Terms', publication_date_time=timezone.now())

    def test_authenticated_user_returns_logged_in_true(self):
        """Test that authenticated user receives logged_in=True with user info"""
        # Create and login a user
        self.client.post('/user/create-account', data={
            'firstname': 'John',
            'lastname': 'Doe',
            'username': 'testuser',
            'email_address': 'testuser@test.com',
            'password': 'ValidPass1!',
            'confirm_password': 'ValidPass1!',
            'newsletter': 'false',
            'remember_me': 'false'
        })

        response = self.client.get('/user/logged-in')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertTrue(response_data['logged_in'],
                       'Authenticated user should have logged_in=True')
        self.assertEqual(response_data['first_name'], 'John',
                        'Should return first name')
        self.assertEqual(response_data['last_name'], 'Doe',
                        'Should return last name')
        self.assertEqual(response_data['email_address'], 'testuser@test.com',
                        'Should return email address')
        self.assertIn('client_event_id', response_data,
                     'Should return client_event_id')

    def test_authenticated_user_returns_correct_member_initials(self):
        """Test that authenticated user receives correct member_initials (first+last initial)"""
        # Create and login a user
        self.client.post('/user/create-account', data={
            'firstname': 'Jane',
            'lastname': 'Smith',
            'username': 'janesmith',
            'email_address': 'jane@test.com',
            'password': 'ValidPass1!',
            'confirm_password': 'ValidPass1!',
            'newsletter': 'false',
            'remember_me': 'false'
        })

        response = self.client.get('/user/logged-in')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['member_initials'], 'JS',
                        'Should return correct member initials (first+last)')

    def test_authenticated_user_with_cart_returns_cart_count(self):
        """Test that authenticated user with cart items receives correct cart_item_count"""
        # Create and login a user
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
        user = User.objects.get(username='testuser')

        # Create a cart with items (different SKUs due to unique constraint)
        cart = Cart.objects.create(member=user.member)
        Cartsku.objects.create(cart=cart, sku_id=1, quantity=2)
        Cartsku.objects.create(cart=cart, sku_id=2, quantity=1)

        response = self.client.get('/user/logged-in')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['cart_item_count'], 2,
                        'Should return count of 2 cart items (not quantity)')

    def test_anonymous_user_returns_logged_in_false(self):
        """Test that anonymous user receives logged_in=False"""
        response = self.client.get('/user/logged-in')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertFalse(response_data['logged_in'],
                        'Anonymous user should have logged_in=False')
        self.assertEqual(response_data['client_event_id'], 'null',
                        'Anonymous user should have client_event_id=null')
        self.assertNotIn('first_name', response_data,
                        'Anonymous user should not have first_name in response')
        self.assertNotIn('last_name', response_data,
                        'Anonymous user should not have last_name in response')
        self.assertNotIn('email_address', response_data,
                        'Anonymous user should not have email_address in response')

    def test_anonymous_user_without_cart_returns_zero_cart_count(self):
        """Test that anonymous user without cart receives cart_item_count=0"""
        # Note: Testing anonymous cart lookup is complex and belongs in order app tests
        # This test verifies the endpoint handles anonymous users without carts gracefully
        response = self.client.get('/user/logged-in')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['cart_item_count'], 0,
                        'Anonymous user without cart should have cart_item_count=0')
        self.assertFalse(response_data['logged_in'],
                        'Should show logged_in=False')

    def test_response_includes_log_client_events_configuration(self):
        """Test that response includes log_client_events configuration value"""
        response = self.client.get('/user/logged-in')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        response_data = json.loads(response.content.decode('utf8'))
        self.assertIn('log_client_events', response_data,
                     'Response should include log_client_events')
        self.assertTrue(response_data['log_client_events'],
                       'log_client_events should be True (set in setUp)')
