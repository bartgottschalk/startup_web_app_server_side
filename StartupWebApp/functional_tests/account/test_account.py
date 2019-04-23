# Selenium Functional Tests (from the perspective of the user)

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities

from unittest import skip

class AccountPageFunctionalTests(BaseFunctionalTest):

	def test_account_page_load(self):
		self.browser.get(self.static_home_page_url + 'account')
		functional_testing_utilities.wait_for_page_title(self, 'My Account')
		self.assertEqual('My Account', self.browser.title)

		# Edit My Information link
		# Edit Shipping & Billing Addresses and Payment Information link
		# Edit Communication Preferences link
		# Change Password link
		# View Order Details link

	'''
	def test_my_information(self):
		self.browser.get(self.static_home_page_url + 'account')
		# Username value
		# Name value
		# Email Address value
		# Email Verified value
		# Joined Date/Time value
		# Last Login Date/Time value
		# Terms of Use and Privacy Policy Agreed Date/Time value
		pass

	def test_shipping_and_billing(self):
		self.browser.get(self.static_home_page_url + 'account')
		# Shipping Address value
		# Billing Address value
		# Payment Information value
		# None
		pass

	def test_communication_preferences(self):
		self.browser.get(self.static_home_page_url + 'account')
		# Unsucscribed value
		# Newsletter value
		pass

	def test_my_orders(self):
		self.browser.get(self.static_home_page_url + 'account')
		# Order Total value
		# Order Date value
		# None
		pass

	'''			
