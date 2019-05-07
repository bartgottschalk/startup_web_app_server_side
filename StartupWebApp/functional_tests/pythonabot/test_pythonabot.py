# Selenium Functional Tests (from the perspective of the user)

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities

from selenium.webdriver.common.keys import Keys

from unittest import skip

class PythonABotPageFunctionalTests(BaseFunctionalTest):

	def test_pythonabot_page_load(self):
		self.browser.get(self.static_home_page_url + 'pythonabot')
		functional_testing_utilities.wait_for_page_title(self, 'PythonABot')
		self.assertEqual('PythonABot', self.browser.title)	
		
		functional_testing_utilities.wait_click_by_id(self, 'header-hamburger-menu')

		# she reads each item in the expanded menu and sees that the current page is not in the list
		menu_expanded = self.browser.find_element_by_id('hamburger-menu-open')
		expected_menu_values = ['Login', 'Home', 'Products', 'About', 'Contact', 'Terms of Use', 'Privacy Policy']
		for num, item in enumerate(menu_expanded.find_elements_by_tag_name("a"), start=0):
			for element in item.find_elements_by_tag_name("menu-item-expanded"):
				self.assertEqual(element.text, expected_menu_values[num])

		# she reads the coming soon text
		coming_soon_text = self.browser.find_element_by_id('coming_soon_text')
		self.assertEqual('Hi, and thanks for coming to learn more about me! As you might already know my name is PythonABot. I\'m a personal assistant robot and you can interact with me by writing in your favorite language - Python! I also write back to you in Python as I assume you prefer to think like a Python interpreter as well! Belive me, it\'s fun to communicate this way!', coming_soon_text.text)

		# she reads the how excited text
		coming_soon_status = self.browser.find_element_by_id('coming_soon_status')
		self.assertEqual('My creators aren\'t quite ready to let you use me, but I should be ready soon! If you want me to notify you when they\'re ready just give me your email address and I\'ll let you know!', coming_soon_status.text)

		# she reads the how excited text
		coming_soon_features = self.browser.find_element_by_id('coming_soon_features')
		self.assertEqual('Here are a few of the things they\'re teaching me to do:', coming_soon_features.text)

		# she reads the how excited text
		how_excited_text = self.browser.find_element_by_id('how_excited_text')
		self.assertEqual('I\'m also curious to know how excited you are to meet me. Knowing that helps my creators work faster!', how_excited_text.text)

		# ensure that the success div is present but hidden
		functional_testing_utilities.wait_for_element_to_load_by_id(self, 'coming_soon_success_message')
		self.assertIn('hide', self.browser.find_element_by_id('coming_soon_success_message').get_attribute('class'))

	def test_pythonabot_page_function_success(self):
		self.browser.get(self.static_home_page_url + 'pythonabot')

		functional_testing_utilities.wait_for_element_to_load_by_id(self, 'notify_me_email_address')

		# she types her email address in the email text box
		notify_me_email_address = self.browser.find_element_by_id('notify_me_email_address')
		notify_me_email_address.send_keys('tellme@more.com')

		# she selects how excited she is about PythonABot
		functional_testing_utilities.wait_click_by_id(self, 'how_excited_option_4')

		# She clicks the submit button
		functional_testing_utilities.wait_click_by_id(self, 'coming_soon_submit_button')

		# she sees the "success" message that her email was submitted
		self.assertNotIn('hide', self.browser.find_element_by_id('coming_soon_success_message').get_attribute('class'))
		# verify the success text
		coming_soon_success_text = self.browser.find_element_by_id('coming_soon_success_text')
		self.assertEqual('Thanks for sharing your emaill address with me. I\'ll let you know when I\'m ready!', coming_soon_success_text.text)

	def test_pythonabot_page_function_duplicate_error(self):
		self.browser.get(self.static_home_page_url + 'pythonabot')

		functional_testing_utilities.wait_for_element_to_load_by_id(self, 'notify_me_email_address')

		# she types her email address in the email text box
		notify_me_email_address = self.browser.find_element_by_id('notify_me_email_address')
		notify_me_email_address.send_keys('tellme@more.com')

		# she selects how excited she is about PythonABot
		functional_testing_utilities.wait_click_by_id(self, 'how_excited_option_5')

		# She clicks the submit button
		functional_testing_utilities.wait_click_by_id(self, 'coming_soon_submit_button')

		# Do it again
		self.browser.get(self.static_home_page_url + 'pythonabot')

		functional_testing_utilities.wait_for_element_to_load_by_id(self, 'notify_me_email_address')

		# she types her email address in the email text box
		notify_me_email_address = self.browser.find_element_by_id('notify_me_email_address')
		notify_me_email_address.send_keys('tellme@more.com')

		# she selects how excited she is about PythonABot
		functional_testing_utilities.wait_click_by_id(self, 'how_excited_option_5')

		# She clicks the submit button
		functional_testing_utilities.wait_click_by_id(self, 'coming_soon_submit_button')

		functional_testing_utilities.wait_for_element_to_display_by_id(self, 'notify_me_email_address_error')

		# she sees the "error" message that this email already exists
		self.assertNotIn('login-form-error-text-hidden', self.browser.find_element_by_id('notify_me_email_address_error').get_attribute('class'))
		self.assertIn('login-form-error-text', self.browser.find_element_by_id('notify_me_email_address_error').get_attribute('class'))
		self.assertEqual('I already know about this email address. Please enter a different email address.', self.browser.find_element_by_id('notify_me_email_address_error').text)

	def test_pythonabot_page_function_empty_email(self):
		self.browser.get(self.static_home_page_url + 'pythonabot')

		functional_testing_utilities.wait_for_element_to_load_by_id(self, 'notify_me_email_address')

		# she selects how excited she is about PythonABot
		functional_testing_utilities.wait_click_by_id(self, 'how_excited_option_1')

		# She clicks the submit button
		functional_testing_utilities.wait_click_by_id(self, 'coming_soon_submit_button')

		# she sees the "error" message that email address is required
		self.assertNotIn('login-form-error-text-hidden', self.browser.find_element_by_id('notify_me_email_address_error').get_attribute('class'))
		self.assertIn('login-form-error-text', self.browser.find_element_by_id('notify_me_email_address_error').get_attribute('class'))
		self.assertEqual('This is a required field.', self.browser.find_element_by_id('notify_me_email_address_error').text)


	def test_pythonabot_page_function_invalid_email(self):
		self.browser.get(self.static_home_page_url + 'pythonabot')

		functional_testing_utilities.wait_for_element_to_load_by_id(self, 'notify_me_email_address')

		# she types her email address in the email text box
		notify_me_email_address = self.browser.find_element_by_id('notify_me_email_address')
		notify_me_email_address.send_keys('tellme@more')

		# she selects how excited she is about PythonABot
		functional_testing_utilities.wait_click_by_id(self, 'how_excited_option_2')

		# She clicks the submit button
		functional_testing_utilities.wait_click_by_id(self, 'coming_soon_submit_button')

		# she sees the "error" message that email address is invalid
		self.assertNotIn('login-form-error-text-hidden', self.browser.find_element_by_id('notify_me_email_address_error').get_attribute('class'))
		self.assertIn('login-form-error-text', self.browser.find_element_by_id('notify_me_email_address_error').get_attribute('class'))
		self.assertEqual('Please enter a valid email address. For example johndoe@domain.com.', self.browser.find_element_by_id('notify_me_email_address_error').text)

	def test_pythonabot_page_function_missing_how_excited(self):
		self.browser.get(self.static_home_page_url + 'pythonabot')

		functional_testing_utilities.wait_for_element_to_load_by_id(self, 'notify_me_email_address')

		# she types her email address in the email text box
		notify_me_email_address = self.browser.find_element_by_id('notify_me_email_address')
		notify_me_email_address.send_keys('tellme@more.com')

		# She clicks the submit button
		functional_testing_utilities.wait_click_by_id(self, 'coming_soon_submit_button')

		# she sees the "error" message that how excited is required
		self.assertNotIn('login-form-error-text-hidden', self.browser.find_element_by_id('how_excited_error').get_attribute('class'))
		self.assertIn('login-form-error-text', self.browser.find_element_by_id('how_excited_error').get_attribute('class'))
		self.assertEqual('Please select one of the options for how excited you are to meet PythonABot.', self.browser.find_element_by_id('how_excited_error').text)






