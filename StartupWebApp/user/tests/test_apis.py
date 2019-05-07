# Unit tests from the perspective of the programmer

import json

from django.http.cookie import SimpleCookie

from django.test import TestCase
from django.http import HttpRequest
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.models import User, Group

from clientevent.models import Configuration as ClientEventConfiguration

from order.models import Cart, Cartsku, Skutype, Skuinventory, Product, Sku, Skuprice, Productsku
from user.models import Member, Termsofuse, Prospect

from order.utilities import order_utils
from StartupWebApp.utilities import random, unittest_utilities

class UserAPITest(TestCase):

	def setUp(self):
		# Setup necessary DB Objects
		ClientEventConfiguration.objects.create(id=1, log_client_events=True)

		Skutype.objects.create(id=1, title='product')
		Skuinventory.objects.create(id=1, title='In Stock', identifier='in-stock', description='In Stock items are available to purchase.')
		Skuinventory.objects.create(id=2, title='Back Ordered', identifier='back-ordered', description='Back Ordered items are not available to purchase at this time.')
		Skuinventory.objects.create(id=3, title='Out of Stock', identifier='out-of-stock', description='Out of Stock items are not available to purchase.')
		Product.objects.create(id=1, title='Paper Clips', title_url='PaperClips', identifier='bSusp6dBHm', headline='Paper clips can hold up to 20 pieces of paper together!', description_part_1='Made out of high quality metal and folded to exact specifications.', description_part_2='Use paperclips for all your paper binding needs!')
		Sku.objects.create(id=1, color='Silver', size='Medium', sku_type_id=1, description='Left Sided Paperclip', sku_inventory_id=1)
		Skuprice.objects.create(id=1, price=3.5, created_date_time=timezone.now(), sku_id=1)
		Productsku.objects.create(id=1, product_id=1, sku_id=1)
		Group.objects.create(name='Members')
		Termsofuse.objects.create(version='1', version_note='Specifically, we\'ve modified our <a class=\"raw-link\" href=\"/privacy-policy\">Privacy Policy</a> and <a class=\"raw-link\" href=\"/terms-of-sale\">Terms of Sale</a>. Modifications include...', publication_date_time=timezone.now())

	def test_logged_in_for_anonymous_user(self):

		##############
		# Empty Cart #
		##############
		response = self.client.get('/user/logged-in')
		unittest_utilities.validate_response_is_OK_and_JSON(self, response)
		self.assertJSONEqual(response.content.decode('utf8'), '{"logged_in": false, "log_client_events": true, "client_event_id": "null", "cart_item_count": 0, "user-api-version": "0.0.1"}', '/user/logged-in for anonymous user with empty cart failed json validation')

		##################
		# NOT Empty Cart #
		##################
		self.client.post('/order/cart-add-product-sku', data={'sku_id': '1', 'quantity': '1'})
		response = self.client.get('/user/logged-in')
		unittest_utilities.validate_response_is_OK_and_JSON(self, response)
		self.assertJSONEqual(response.content.decode('utf8'), '{"logged_in": false, "log_client_events": true, "client_event_id": "null", "cart_item_count": 1, "user-api-version": "0.0.1"}', '/user/logged-in for anonymous user with 1 item in cart failed json validation')

	def test_logged_in_for_authenticated_user(self):

		# create user and login
		response = self.client.post('/user/create-account', data={'firstname': 'jest', 'lastname': 'lser', 'username': 'testuser_logged_in', 'email_address': 'jestlser@test.com', 'password': 'ThisIsValid1!', 'confirm_password': 'ThisIsValid1!', 'newsletter': 'true', 'remember_me': 'false'})
		
		##############
		# Empty Cart #
		##############
		response = self.client.get('/user/logged-in')
		unittest_utilities.validate_response_is_OK_and_JSON(self, response)
		self.assertJSONEqual(response.content.decode('utf8'), '{"logged_in": true, "log_client_events": true, "client_event_id": ' + str(User.objects.latest('id').id) + ', "member_initials": "' + User.objects.latest('id').first_name[:1] + User.objects.latest('id').last_name[:1] + '", "first_name": "' + User.objects.latest('id').first_name + '", "last_name": "' + User.objects.latest('id').last_name + '", "email_address": "' + User.objects.latest('id').email + '", "cart_item_count": 0, "user-api-version": "0.0.1"}', '/user/logged-in for authenticated user with empty cart failed json validation')

		##################
		# NOT Empty Cart #
		##################
		self.client.post('/order/cart-add-product-sku', data={'sku_id': '1', 'quantity': '1'})
		response = self.client.get('/user/logged-in')
		unittest_utilities.validate_response_is_OK_and_JSON(self, response)
		self.assertJSONEqual(response.content.decode('utf8'), '{"logged_in": true, "log_client_events": true, "client_event_id": ' + str(User.objects.latest('id').id) + ', "member_initials": "' + User.objects.latest('id').first_name[:1] + User.objects.latest('id').last_name[:1] + '", "first_name": "' + User.objects.latest('id').first_name + '", "last_name": "' + User.objects.latest('id').last_name + '", "email_address": "' + User.objects.latest('id').email + '", "cart_item_count": 1, "user-api-version": "0.0.1"}', '/user/logged-in for authenticated user with 1 item in cart failed json validation')

	def test_create_account(self):

		response = self.client.post('/user/create-account', data={'firstname': 'test', 'lastname': 'user', 'username': 'testuser', 'email_address': 'testuser@test.com', 'password': 'ThisIsValid1!', 'confirm_password': 'ThisIsValid1', 'newsletter': 'true', 'remember_me': 'false'})
		unittest_utilities.validate_response_is_OK_and_JSON(self, response)
		self.assertJSONEqual(response.content.decode('utf8'), '{"create_account": "false", "errors": {"firstname": true, "lastname": true, "username": true, "email-address": true, "password": [{"type": "confirm_password_doesnt_match", "description": "Please make sure your passwords match."}]}, "user-api-version": "0.0.1"}', '/user/create-account passwords don\' match failed json validation')

		response = self.client.post('/user/create-account', data={'firstname': 'test', 'lastname': 'user', 'username': 'testuser', 'email_address': 'testuser@test.com', 'password': 'ThisIsValid1!', 'confirm_password': 'ThisIsValid1!', 'newsletter': 'true', 'remember_me': 'false'})
		unittest_utilities.validate_response_is_OK_and_JSON(self, response)
		self.assertJSONEqual(response.content.decode('utf8'), '{"create_account": "true", "user-api-version": "0.0.1"}', '/user/create-account successful registration failed json validation')
		self.assertEqual(Member.objects.count(), 1)
		new_member = Member.objects.first()
		self.assertEqual(new_member.user.first_name, 'test')

		#self.assertEqual(1, 2)

		print('FINISH THE TEST!!! - other error conditions that need to be tested')

	def test_pythonabot_notify_me(self):

		response = self.client.post('/user/pythonabot-notify-me', data={'email_address': '', 'how_excited': '1'})
		unittest_utilities.validate_response_is_OK_and_JSON(self, response)
		#print(response.content.decode('utf8'))
		self.assertJSONEqual(response.content.decode('utf8'), '{"pythonabot_notify_me": "validation_error", "errors": {"email_address": [{"type": "required", "description": "This is a required field."}], "how_excited": true}, "user-api-version": "0.0.1"}', '/user/pythonabot-notify-me email required failed validation')

		response = self.client.post('/user/pythonabot-notify-me', data={'email_address': 'asdf', 'how_excited': '2'})
		unittest_utilities.validate_response_is_OK_and_JSON(self, response)
		#print(response.content.decode('utf8'))
		self.assertJSONEqual(response.content.decode('utf8'), '{"pythonabot_notify_me": "validation_error", "errors": {"email_address": [{"type": "not_valid", "description": "Please enter a valid email address. For example johndoe@domain.com."}], "how_excited": true}, "user-api-version": "0.0.1"}', '/user/pythonabot-notify-me email valid failed validation')

		response = self.client.post('/user/pythonabot-notify-me', data={'email_address': 'asdf@asdf.com', 'how_excited': ''})
		unittest_utilities.validate_response_is_OK_and_JSON(self, response)
		#print(response.content.decode('utf8'))
		self.assertJSONEqual(response.content.decode('utf8'), '{"pythonabot_notify_me": "validation_error", "errors": {"email_address": true, "how_excited": [{"type": "required", "description": "This is a required field."}]}, "user-api-version": "0.0.1"}', '/user/pythonabot-notify-me how_excited valid failed validation')

		response = self.client.post('/user/pythonabot-notify-me', data={'email_address': 'asdf@asdf.com', 'how_excited': '6'})
		unittest_utilities.validate_response_is_OK_and_JSON(self, response)
		#print(response.content.decode('utf8'))
		self.assertJSONEqual(response.content.decode('utf8'), '{"pythonabot_notify_me": "validation_error", "errors": {"email_address": true, "how_excited": [{"type": "out_of_range", "description": "The value provided is out of range."}]}, "user-api-version": "0.0.1"}', '/user/pythonabot-notify-me how_excited valid failed validation')

		response = self.client.post('/user/pythonabot-notify-me', data={'email_address': 'asdf@asdf.com', 'how_excited': '3'})
		unittest_utilities.validate_response_is_OK_and_JSON(self, response)
		#print(response.content.decode('utf8'))
		self.assertJSONEqual(response.content.decode('utf8'), '{"pythonabot_notify_me": "success", "user-api-version": "0.0.1"}', '/user/create-account successful registration failed json validation')
		self.assertEqual(Prospect.objects.count(), 1)
		new_prospect = Prospect.objects.first()
		self.assertEqual(new_prospect.swa_comment, 'This prospect would like to be notified when PythonABot is ready to be purchased.')

		response = self.client.post('/user/pythonabot-notify-me', data={'email_address': 'asdf@asdf.com', 'how_excited': '4'})
		unittest_utilities.validate_response_is_OK_and_JSON(self, response)
		#print(response.content.decode('utf8'))
		self.assertJSONEqual(response.content.decode('utf8'), '{"pythonabot_notify_me": "duplicate_prospect", "errors": {"email_address": [{"type": "duplicate", "description": "I already know about this email address. Please enter a different email address."}], "how_excited": true}, "user-api-version": "0.0.1"}', '/user/pythonabot-notify-me duplicate prospect failed validation')
