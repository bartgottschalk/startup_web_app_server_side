# Selenium Functional Tests (from the perspective of the user)

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities

from unittest import skip

class ShoppingCartPageFunctionalTests(BaseFunctionalTest):

	def test_shopping_cart_page_load(self):
		self.browser.get(self.static_home_page_url + 'cart')
		functional_testing_utilities.wait_for_page_title(self, 'Shopping Cart')
		self.assertEqual('Shopping Cart', self.browser.title)

		# Checkout link top
		# Checkout link Bottom
		# Products Grid
		# Select Shipping Method Grid
		# Discount Codes Grid
		# Item and Shipping Total Cost







	'''
	def test_change_quantity(self):
		self.browser.get(self.static_home_page_url + 'cart')
		# non-numeric
		# blank
		# 100
		# 0
		# 5
		pass

	def test_remove_sku(self):
		self.browser.get(self.static_home_page_url + 'cart')
		# other skus in cart
		# Last sku in cart
		pass

	def test_change_shipping_method(self):
		self.browser.get(self.static_home_page_url + 'cart')
		# other products
		# with "FREESHIPPING" discount applied
		pass

	def test_discount_code(self):
		self.browser.get(self.static_home_page_url + 'cart')
		# WELCOME50 Discount Code
		# SEPTSAVER Discount Code
		# Remove Discount Codes
		# Non-combinable discount codes
		pass


	'''			
