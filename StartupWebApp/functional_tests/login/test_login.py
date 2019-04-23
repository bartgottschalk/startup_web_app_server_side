# Selenium Functional Tests (from the perspective of the user)

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities

from unittest import skip

class LogInPageFunctionalTests(BaseFunctionalTest):

	def test_login_page_load(self):
		self.browser.get(self.static_home_page_url + 'login')
		functional_testing_utilities.wait_for_page_title(self, 'Log In')
		self.assertEqual('Log In', self.browser.title)

		# Create Account link
		# Reset Your Password link
		# Forgot Your Username? link

	'''
	def test_user_name_bad(self):
		self.browser.get(self.static_home_page_url + 'login')
		pass

	def test_password_bad(self):
		self.browser.get(self.static_home_page_url + 'login')
		pass

	def test_username_and_password_bad(self):
		self.browser.get(self.static_home_page_url + 'login')
		pass

	def test_success_keep_me_logged_in_selected(self):
		self.browser.get(self.static_home_page_url + 'login')
		pass

	def test_success_keep_me_logged_in_not_selected(self):
		self.browser.get(self.static_home_page_url + 'login')
		pass


	'''			
