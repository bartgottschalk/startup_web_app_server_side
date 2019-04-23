# Selenium Functional Tests (from the perspective of the user)

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities

from unittest import skip

class ResetPasswordFunctionalTests(BaseFunctionalTest):

	def test_reset_password_page_load(self):
		self.browser.get(self.static_home_page_url + 'reset-password')
		functional_testing_utilities.wait_for_page_title(self, 'Reset Password')
		self.assertEqual('Reset Password', self.browser.title)

		# Page Subtitle
		# Username textbox placeholder 
		# Email Address textbox placeholder 
		# Request Password Reset Button
		# Back to Login link

	'''
	def test_submit_form(self):
		self.browser.get(self.static_home_page_url + 'forgot-username')
		# invalid username
		# valid username
		# invalid email
		# valid email address
		# confirmation text on screen
		pass

	'''			
