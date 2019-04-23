# Selenium Functional Tests (from the perspective of the user)

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities

from unittest import skip

class CheckoutConfirmPageFunctionalTests(BaseFunctionalTest):

	def test_checkout_confirm_page_load(self):
		self.browser.get(self.static_home_page_url + 'checkout/confirm')
		functional_testing_utilities.wait_for_page_title(self, 'Confirm Order')
		self.assertEqual('Confirm Order', self.browser.title)

		# Products Grid
		# Shipping Method
		# Discount Codes
		# Item and Shipping Total Cost
		# Shipping Address
		# Billing Address
		# Payment Information
		# Confirmation Email Address

	def test_checkout_confirm_cart_empty_page_load(self):
		self.browser.get(self.static_home_page_url + 'checkout/confirm')
		functional_testing_utilities.wait_for_page_title(self, 'Confirm Order')
		self.assertEqual('Confirm Order', self.browser.title)

		# Empty Message text and links

	'''
	def test_anonymous_login_no_shipping_billing_info_in_account(self):
		self.browser.get(self.static_home_page_url + 'checkout/confirm')
		# select login option
		# login
		# confirm that redirects back to checkout/confirm in login mode
		# enter payment and shipping info - billing and shipping addr different
		# Verify shipping and billing addresses
		# Verify Payment information
		# Check box to Save shipping and payment information in my account
		# Check Terms of Sale Checkbox
		# Click Place Order
		# Verify order details page
		# Verify that the shipping and payment information is saved on the account
		pass

	def test_anonymous_login_shipping_billing_info_already_in_account(self):
		self.browser.get(self.static_home_page_url + 'checkout/confirm')
		# select login option
		# login
		# confirm that redirects back to checkout/confirm in login mode
		# Verify shipping and billing addresses
		# Verify Payment information
		# Check Terms of Sale Checkbox
		# Click Place Order
		# Verify order details page
		pass

	def test_anonymous_login_skus_already_in_member_cart(self):
		self.browser.get(self.static_home_page_url + 'checkout/confirm')
		# log in
		# add items to cart
		# log out
		# add different items to cart
		# view cart and verify just different items are in the cart
		# checkout
		# select login option
		# login
		# confirm that redirects back to checkout/confirm in login mode
		# Verify that items are combined on confirm page
		# Verify shipping and billing addresses
		# Verify Payment information
		# Check Terms of Sale Checkbox
		# Click Place Order
		# Verify order details page
		pass

	def test_anonymous_create_account(self):
		self.browser.get(self.static_home_page_url + 'checkout/confirm')
		# select create account option
		# create account
		# confirm that redirects back to checkout/confirm in login mode
		# enter payment and shipping info - billing and shipping addr same
		# Verify shipping and billing addresses
		# Verify Payment information
		# Don't check box to Save shipping and payment information in my account
		# Check Terms of Sale Checkbox
		# Click Place Order
		# Verify order details page
		# Verify that the shipping and payment information is NOT saved on the account
		pass

	def test_anonymous_anonymous_no_marketing_email_sign_up(self):
		self.browser.get(self.static_home_page_url + 'checkout/confirm')
		# select "Checkout Anonymous" option
		# enter email address that already exists and confirm error
		# enter email address that doesn't exist 
		# confirm Email Confirmation Address
		# Select Change Email Address link
		# select "Checkout Anonymous" option
		# enter email address that doesn't exist 
		# enter payment and shipping info
		# Verify shipping and billing addresses
		# Verify Payment information
		# Check Terms of Sale Checkbox
		# DON'T select Sign up to receive marketing emails
		# Click Place Order
		# Verify order details page
		pass

	def test_anonymous_anonymous_yes_marketing_email_sign_up(self):
		self.browser.get(self.static_home_page_url + 'checkout/confirm')
		# select "Checkout Anonymous" option
		# enter email address that doesn't exist 
		# enter payment and shipping info
		# Check Terms of Sale Checkbox
		# Select Sign up to receive marketing emails
		# Click Place Order
		# Verify order details page
		pass


	'''			
