# Selenium Functional Tests (from the perspective of the user)

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities

from unittest import skip

class ShippingBillingPaymentLinkFunctionalTests(BaseFunctionalTest):

	def test_shipping_billing_payment_link_overlay_load(self):
		self.browser.get(self.static_home_page_url + 'account')
		functional_testing_utilities.wait_for_page_title(self, 'My Account')
		self.assertEqual('My Account', self.browser.title)

		# email address displayed in overlay

	'''
	def test_with_validation_code(self):
		self.browser.get(self.static_home_page_url + 'account')
		pass

	def test_without_validation_code(self):
		self.browser.get(self.static_home_page_url + 'account')
		pass

	def test_starting_from_no_values(self):
		self.browser.get(self.static_home_page_url + 'account')
		pass


	'''			
