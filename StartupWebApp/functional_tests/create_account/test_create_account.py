# Selenium Functional Tests (from the perspective of the user)

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities

from unittest import skip

class CreateAccountPageFunctionalTests(BaseFunctionalTest):

	def test_create_account_page_load(self):
		self.browser.get(self.static_home_page_url + 'create-account')
		functional_testing_utilities.wait_for_page_title(self, 'Create Account')
		self.assertEqual('Create Account', self.browser.title)

		# agree Terms of Use link
		# agree Privacy Policy link

	'''
	def test_first_name_field(self):
		self.browser.get(self.static_home_page_url + 'create-account')
		# placeholder
		# required
		pass

	def test_last_name_field(self):
		self.browser.get(self.static_home_page_url + 'create-account')
		# placeholder
		# required
		pass

	def test_email_address_field(self):
		self.browser.get(self.static_home_page_url + 'create-account')
		# placeholder
		# required
		# invalid
		pass

	def test_username_field(self):
		self.browser.get(self.static_home_page_url + 'create-account')
		# placeholder
		# required
		# duplicate
		pass

	def test_password_field(self):
		self.browser.get(self.static_home_page_url + 'create-account')
		# placeholder
		# required
		# invalid
		pass

	def test_verify_password_field(self):
		self.browser.get(self.static_home_page_url + 'create-account')
		# placeholder
		# required
		# invalid
		# don't match
		pass

	def test_not_checking_tou_box(self):
		self.browser.get(self.static_home_page_url + 'create-account')
		pass

	def test_success_sign_up_for_newsletter_selected(self):
		self.browser.get(self.static_home_page_url + 'create-account')
		pass

	def test_success_sign_up_for_newsletter_not_selected(self):
		self.browser.get(self.static_home_page_url + 'create-account')
		pass

	def test_success_keep_me_logged_in_selected(self):
		self.browser.get(self.static_home_page_url + 'create-account')
		pass

	def test_success_keep_me_logged_in_not_selected(self):
		self.browser.get(self.static_home_page_url + 'create-account')
		pass

	def test_verify_email_address(self):
		self.browser.get(self.static_home_page_url + 'create-account')
		pass


	'''			
