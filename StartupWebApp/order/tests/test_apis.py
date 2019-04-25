# Unit tests from the perspective of the programmer

import json

from django.test import TestCase
from django.http import HttpRequest
from django.utils import timezone

from order.models import Orderconfiguration, Cart, Cartsku, Skutype, Skuinventory, Product, Sku, Skuprice, Productsku, Orderstatus, Shippingmethod

from StartupWebApp.utilities import unittest_utilities

class OrderAPITest(TestCase):

	def setUp(self):
		# Setup necessary DB Objects
		Skutype.objects.create(id=1, title='product')
		Skuinventory.objects.create(id=1, title='In Stock', identifier='in-stock', description='In Stock items are available to purchase.')
		Skuinventory.objects.create(id=2, title='Back Ordered', identifier='back-ordered', description='Back Ordered items are not available to purchase at this time.')
		Skuinventory.objects.create(id=3, title='Out of Stock', identifier='out-of-stock', description='Out of Stock items are not available to purchase.')
		
		Product.objects.create(id=1, title='Paper Clips', title_url='PaperClips', identifier='bSusp6dBHm', headline='Paper clips can hold up to 20 pieces of paper together!', description_part_1='Made out of high quality metal and folded to exact specifications.', description_part_2='Use paperclips for all your paper binding needs!')
		Sku.objects.create(id=1, color='Silver', size='Medium', sku_type_id=1, description='Left Sided Paperclip', sku_inventory_id=1)
		Skuprice.objects.create(id=1, price=3.5, created_date_time=timezone.now(), sku_id=1)
		Productsku.objects.create(id=1, product_id=1, sku_id=1)

	def test_cart_add_product_sku(self):

		####################
		# quantity-invalid # must be 0-99 and an Int
		####################
		response = self.client.post('/order/cart-add-product-sku', data={'sku_id': '1', 'quantity': '100'})
		unittest_utilities.validate_response_is_OK_and_JSON(self, response)
		self.assertJSONEqual(response.content.decode('utf8'), '{"cart_add_product_sku": "error", "errors": {"quantity": [[{"type": "out_of_range", "description": "The value provided is out of range."}]]}, "sku_id": "1", "order-api-version": "0.0.1"}', '/order/cart-add-product-sku for quantity-invalid not in range failed json validation')

		response = self.client.post('/order/cart-add-product-sku', data={'sku_id': '1', 'quantity': 'x'})
		unittest_utilities.validate_response_is_OK_and_JSON(self, response)
		self.assertJSONEqual(response.content.decode('utf8'), '{"cart_add_product_sku": "error", "errors": {"quantity": [[{"type": "not_an_int", "description": "The value provided is not an integer."}]]}, "sku_id": "1", "order-api-version": "0.0.1"}', '/order/cart-add-product-sku for quantity-invalid not an int failed json validation')

		###################
		# sku-id-required #
		###################
		response = self.client.post('/order/cart-add-product-sku', data={'quantity': '1'})
		unittest_utilities.validate_response_is_OK_and_JSON(self, response)
		self.assertJSONEqual(response.content.decode('utf8'), '{"cart_add_product_sku": "error", "errors": {"error": "sku-id-required"}, "sku_id": null, "order-api-version": "0.0.1"}', '/order/cart-add-product-sku for sku-id-required failed json validation')

		#################
		# Sku not found #
		#################
		response = self.client.post('/order/cart-add-product-sku', data={'sku_id': '2', 'quantity': '1'})
		unittest_utilities.validate_response_is_OK_and_JSON(self, response)
		self.assertJSONEqual(response.content.decode('utf8'), '{"cart_add_product_sku": "error", "errors": {"error": "sku-not-found"}, "sku_id": "2", "order-api-version": "0.0.1"}', '/order/cart-add-product-sku for Sku not found failed json validation')

		#####################################
		# sku doesn't exist in cart success #
		#####################################
		response = self.client.post('/order/cart-add-product-sku', data={'sku_id': '1', 'quantity': '1'})
		unittest_utilities.validate_response_is_OK_and_JSON(self, response)
		self.assertJSONEqual(response.content.decode('utf8'), '{"cart_add_product_sku": "success", "sku_id": "1", "cart_item_count": 1, "order-api-version": "0.0.1"}', '/order/cart-add-product-sku for sku doesn\'t exist in cart success failed json validation')

		######################################
		# sku already exists in cart success #
		######################################
		response = self.client.post('/order/cart-add-product-sku', data={'sku_id': '1', 'quantity': '1'})
		unittest_utilities.validate_response_is_OK_and_JSON(self, response)
		self.assertJSONEqual(response.content.decode('utf8'), '{"cart_add_product_sku": "success", "sku_id": "1", "cart_item_count": 1, "order-api-version": "0.0.1"}', '/order/cart-add-product-sku for sku already exists in cart success failed json validation')
