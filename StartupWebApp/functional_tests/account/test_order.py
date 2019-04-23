# Selenium Functional Tests (from the perspective of the user)

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities

from unittest import skip

class OrderPageFunctionalTests(BaseFunctionalTest):

	def test_order_page_load(self):
		self.browser.get(self.static_home_page_url + 'account/order?identifier=???')
		functional_testing_utilities.wait_for_page_title(self, 'My Order')
		self.assertEqual('My Order', self.browser.title)

		# Back to My Account link top
		# Back to My Account link bottom
		# Order Identifier value
		# Order Status
		# Products
		# Shipping Method
		# ITEM AND SHIPPING TOTAL COST
		# SHIPPING ADDRESS
		# BILLING ADDRESS
		# PAYMENT INFORMATION
		# CONFIRMATION EMAIL ADDRESS
		# Terms of Sale text at bottom of order
		# Terms of Sale link at bottom of order

	'''
	def test_first_name_field(self):
		self.browser.get(self.static_home_page_url + 'account/edit-my-information')
		# placeholder
		# required
		pass

	def test_last_name_field(self):
		self.browser.get(self.static_home_page_url + 'account/edit-my-information')
		# placeholder
		# required
		pass

	def test_email_address_field(self):
		self.browser.get(self.static_home_page_url + 'account/edit-my-information')
		# placeholder
		# required
		# invalid
		pass

	def test_success(self):
		self.browser.get(self.static_home_page_url + 'account/edit-my-information')
		pass

	'''			
