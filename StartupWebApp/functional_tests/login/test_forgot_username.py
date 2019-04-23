# Selenium Functional Tests (from the perspective of the user)

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities

from unittest import skip

class ForgotUsernamePageFunctionalTests(BaseFunctionalTest):

	def test_forgot_username_page_load(self):
		self.browser.get(self.static_home_page_url + 'forgot-username')
		functional_testing_utilities.wait_for_page_title(self, 'Forgot Username')
		self.assertEqual('Forgot Username', self.browser.title)

		# Page Subtitle
		# Page instructions text
		# Textbox placeholder 
		# Send Username Button
		# Back to Login link

	'''
	def test_submit_form(self):
		self.browser.get(self.static_home_page_url + 'forgot-username')
		# invalid email
		# valid email address
		# confirmation text on screen
		pass


	'''			
