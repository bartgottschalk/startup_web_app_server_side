# Selenium Functional Tests (from the perspective of the user)

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities

from unittest import skip

class ProductPageFunctionalTests(BaseFunctionalTest):

	'''
	def test_product_page_load(self):
		self.browser.get(self.static_home_page_url + 'product?name=CountertopOrganizer&id=mqHfBUlwp0')
		functional_testing_utilities.wait_for_page_title(self, 'Countertop Organizer')
		self.assertEqual('Countertop Organizer', self.browser.title)

		# Title
		# ← Return to Browse Products link
		# price
		# Inventory Indicator text and link
		# Inventory detail text
		# Description 1
		# Description 2
		# Sku options
		# Quantity
		# Add to Cart button
		# Image Grid
		# Image Selection
		# Image Overlay
		# Image video

	def test_add_to_cart_fail(self):
		self.browser.get(self.static_home_page_url + 'product?name=CountertopOrganizer&id=mqHfBUlwp0')
		# non-numeric quantity
		pass

	def test_dd_to_cart_success(self):
		self.browser.get(self.static_home_page_url + 'product?name=CountertopOrganizer&id=mqHfBUlwp0')
		# qty > 1
		# qty = 1
		pass

	'''			
