# Selenium Functional Tests (from the perspective of the user)

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities

from unittest import skip

class ChangePasswordPageFunctionalTests(BaseFunctionalTest):

	def test_change_password_page_load(self):
		self.browser.get(self.static_home_page_url + 'account/change-password')
		functional_testing_utilities.wait_for_page_title(self, 'Change My Password')
		self.assertEqual('Change My Password', self.browser.title)

		# Cancel - Back to My Account link

	'''
	def test_current_password_bad(self):
		self.browser.get(self.static_home_page_url + 'account/change-password')
		pass

	def test_new_passwords_dont_match(self):
		self.browser.get(self.static_home_page_url + 'account/change-password')
		pass

	def test_password_invalid(self):
		self.browser.get(self.static_home_page_url + 'account/change-password')
		pass

	def test_success(self):
		self.browser.get(self.static_home_page_url + 'account/change-password')
		pass

	'''			
