# Selenium Functional Tests (from the perspective of the user)

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities

from unittest import skip

class SetNewPasswordPageFunctionalTests(BaseFunctionalTest):

	def test_set_new_password_page_load(self):
		self.browser.get(self.static_home_page_url + 'set-new-password?password_reset_code=13mhbG8CyjuCt5LmvENo:1hEdJH:l6t45a8vkcychh3cQ5deIezcY1s')
		functional_testing_utilities.wait_for_page_title(self, 'Set Password')
		self.assertEqual('Set Password', self.browser.title)

		# Page Subtitle
		# Username textbox placeholder 
		# New Password textbox placeholder 
		# Confirm New Password textbox placeholder 
		# Save New Password Button
		# Back to Login link

	'''
	def test_submit_form_invalid_token(self):
		self.browser.get(self.static_home_page_url + 'forgot-username')
		# valid username
		# valid password
		# confirm password does match
		# error confirmation text on screen
		pass

	def test_submit_form_valid_token(self):
		self.browser.get(self.static_home_page_url + 'forgot-username')
		# invalid username
		# non-existing username
		# valid username
		# invalid password
		# valid password
		# confirm password doesn't match
		# confirm password does match
		# confirmation text and link on screen
		pass

	'''			
