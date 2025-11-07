# Selenium Functional Tests (from the perspective of the user)

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities

import time
from unittest import skip

from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import NoSuchElementException

class AnonymousGlobalNavigationTests(BaseFunctionalTest):

	def test_footer(self):
		self.browser.get(self.static_home_page_url)

		# clear fixed footer
		functional_testing_utilities.wait_click_by_class_name(self, 'footer-fixed-action-link')
		functional_testing_utilities.wait_click_by_id(self, 'footer-terms-of-use')
		self.assertEqual('Terms of Use', self.browser.title)
		functional_testing_utilities.wait_click_by_id(self, 'footer-privacy-policy')
		self.assertEqual('Privacy Policy', self.browser.title)
		functional_testing_utilities.wait_click_by_id(self, 'footer-terms-of-sale')
		self.assertEqual('Terms of Sale', self.browser.title)

	def test_header(self):
		# she notices the menu icon and clicks on it
		self.browser.get(self.static_home_page_url)
		main_window = self.browser.current_window_handle

		functional_testing_utilities.wait_click_by_id(self, 'header-hamburger-menu')

		# she reads each item in the expanded menu
		menu_expanded = self.browser.find_element_by_id('hamburger-menu-open')
		expected_menu_values = ['Login', 'PythonABot', 'Products', 'About', 'Contact', 'Terms of Use', 'Privacy Policy']
		for num, item in enumerate(menu_expanded.find_elements_by_tag_name("a"), start=0):
			for element in item.find_elements_by_tag_name("menu-item-expanded"):
				self.assertEqual(element.text, expected_menu_values[num])
		
		# she notices the shopping cart icon, that it's empty and clicks on it
		functional_testing_utilities.wait_for_shopping_cart_count(self, '0', 'You have no items in your cart.')		
		functional_testing_utilities.wait_click_by_id(self, 'header-shopping-cart')
		self.assertEqual('Shopping Cart', self.browser.title)		
		functional_testing_utilities.wait_for_element_to_load_by_id(self, 'menu-home-link')

		# she clicks the back button to go back to the previous page
		self.browser.back()

		# she notices the account icon and clicks on it
		functional_testing_utilities.wait_click_by_id(self, 'header-account')
		self.assertEqual('My Account', self.browser.title)
		## There is a javascript window.location redirect from My Account to Log In due to the user being anonymous at this point
		functional_testing_utilities.wait_for_page_title(self, 'Log In')
		self.assertEqual('Log In', self.browser.title)
		# she clicks the home image button to go back to the previous page
		functional_testing_utilities.wait_for_element_to_load_by_id(self, 'menu-home-link')
		functional_testing_utilities.wait_click_by_id(self, 'header-logo-image')
		self.assertEqual('Home Page', self.browser.title)

		# NOTE: Removed Twitter and Facebook external link checks - external sites are outside our control
		# and their page titles can change, making tests brittle and unreliable

		# she clicks the home image button to see what it does
		functional_testing_utilities.wait_click_by_id(self, 'header-logo-image')
		self.assertIn('Home Page', self.browser.title)
		functional_testing_utilities.wait_for_element_to_load_by_id(self, 'menu-login-link')

		# she notices the Call Us link and clicks on it
		self.assertEqual('tel:+1-800-800-8000', self.browser.find_element_by_id('header-phone-number').find_element_by_tag_name('a').get_attribute('href'))
		call_us_element = self.browser.find_element_by_id('header-phone-number').find_element_by_tag_name('a')
		try:
			call_us_element.click()
		except (WebDriverException) as e:  
			print('clicking on the call us phone number raised exception as expected!', e)
			pass

class AnonymousGlobalFunctionalTests(BaseFunctionalTest):

	#@skip
	def test_review_and_accept_terms_of_service(self):
		self.browser.get(self.static_home_page_url)

		main_window = self.browser.current_window_handle

		# she notices the terms and conditions warning overlay and reads it and accepts
		previous_window_handles = self.browser.window_handles

		functional_testing_utilities.wait_for_element_to_load_by_class_name(self, 'footer-fixed-content')
		#self.browser.save_screenshot('/tmp/1.png')
		#s3_file_url = functional_testing_utilities.putPDFOnS3('/tmp/', '1.png')

		functional_testing_utilities.wait_click_by_id(self, 'terms_and_conditions_agree_terms_of_use_link')

		new_window_handle = functional_testing_utilities.wait_for_new_window_handle(self, previous_window_handles)
		self.browser.switch_to_window(new_window_handle)

		#self.assertEqual('Terms of Use', self.browser.title)
		#self.browser.find_element_by_tag_name('body').send_keys(Keys.COMMAND + 'w')
		self.browser.switch_to_window(main_window)

		previous_window_handles = self.browser.window_handles
		functional_testing_utilities.wait_click_by_id(self, 'terms_and_conditions_agree_privacy_policy_link')

		new_window_handle = functional_testing_utilities.wait_for_new_window_handle(self, previous_window_handles)

		self.browser.switch_to_window(new_window_handle)

		# Wait for the Privacy Policy page to load
		functional_testing_utilities.wait_for_page_title(self, 'Privacy Policy')
		self.assertEqual('Privacy Policy', self.browser.title)
		#self.browser.find_element_by_tag_name('body').send_keys(Keys.COMMAND + 'w')
		self.browser.switch_to_window(main_window)

		functional_testing_utilities.wait_click_by_class_name(self, 'footer-fixed-action-link')

		# verify that the terms-and-conditions-agree-div is hidden
		self.assertIn('hide', self.browser.find_element_by_id('terms-and-conditions-agree-div').get_attribute('class'))

	def test_chat(self):
		self.browser.get(self.static_home_page_url)

		# clear fixed footer
		functional_testing_utilities.wait_click_by_class_name(self, 'footer-fixed-action-link')

		# ensure that the div is currently hidden
		self.assertIn('hide', self.browser.find_element_by_id('chat-dialogue-wrapper').get_attribute('class'))
		# ensure that the open chat icon is visible
		self.assertNotIn('hide', self.browser.find_element_by_id('chat-icon').get_attribute('class'))
		# ensure that the close chat icon is NOT visible
		self.assertIn('hide', self.browser.find_element_by_id('chat-icon-close').get_attribute('class'))

		# she clicks on the chat icon
		functional_testing_utilities.wait_click_by_id(self, 'chat-icon-wrapper')

		# ensure that the div is currently visible
		self.assertNotIn('hide', self.browser.find_element_by_id('chat-dialogue-wrapper').get_attribute('class'))
		# ensure that the open chat icon is NOT visible
		self.assertIn('hide', self.browser.find_element_by_id('chat-icon').get_attribute('class'))
		# ensure that the close chat icon is visible
		self.assertNotIn('hide', self.browser.find_element_by_id('chat-icon-close').get_attribute('class'))

		# ensure that the div has the correct contents
		self.assertEqual(self.browser.find_element_by_class_name('chat-dialogue-header-intro').text, 'So sorry, but we\'re unavailable to chat at this time.')
		self.assertEqual(self.browser.find_element_by_class_name('chat-dialogue-header-message').text, 'Please submit your message and we\'ll get back to you as soon as possible!')
		name_input_box = self.browser.find_element_by_id('chat-dialogue-name')
		self.assertEqual(name_input_box.get_attribute('placeholder'), 'Name *')
		email_address_input_box = self.browser.find_element_by_id('chat-dialogue-email-address')
		self.assertEqual(email_address_input_box.get_attribute('placeholder'), 'Email Address *')
		message_input_box = self.browser.find_element_by_id('chat-dialogue-message')
		self.assertEqual(message_input_box.get_attribute('placeholder'), 'Message *')
		chat_go_button = self.browser.find_element_by_id('submit-message-go')
		self.assertEqual(chat_go_button.get_attribute('value'), 'SUBMIT MESSAGE')

		# she submits a chat message
		name_input_box.send_keys('Test Name')
		email_address_input_box.send_keys('test@test.com')
		message_input_box.send_keys('Hi! I have a questions...?')
		functional_testing_utilities.wait_click_by_id(self, 'submit-message-go')

		## wait for ajax response to process
		functional_testing_utilities.wait_for_element_by_class_name_text_value(self, 'chat-dialogue-header-intro', 'Thank you. We got your message.')

		# she gets a confirmation response
		self.assertEqual(self.browser.find_element_by_class_name('chat-dialogue-header-intro').text, 'Thank you. We got your message.')
		self.assertEqual(self.browser.find_element_by_class_name('chat-dialogue-header-message').text, 'We\'ll get back to you ASAP!')
		self.assertEqual(self.browser.find_element_by_id('chat-dialogue-go-button-wrapper').text, 'Name: Test Name\nEmail Address: test@test.com\nMessage:\nHi! I have a questions...?')

		# she clicks on the close chat icon
		functional_testing_utilities.wait_click_by_id(self, 'chat-icon-wrapper')
		# ensure that the div is currently hidden
		self.assertIn('hide', self.browser.find_element_by_id('chat-dialogue-wrapper').get_attribute('class'))
		# ensure that the open chat icon is visible
		self.assertNotIn('hide', self.browser.find_element_by_id('chat-icon').get_attribute('class'))
		# ensure that the close chat icon is NOT visible
		self.assertIn('hide', self.browser.find_element_by_id('chat-icon-close').get_attribute('class'))
