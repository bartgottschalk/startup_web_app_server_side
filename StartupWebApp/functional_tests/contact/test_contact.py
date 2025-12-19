# Selenium Functional Tests (from the perspective of the user)

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities

from unittest import skip

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By

class ContactPageTests(BaseFunctionalTest):

	def test_contact_page(self):
		self.browser.get(self.static_home_page_url + 'contact')
		functional_testing_utilities.wait_for_page_title(self, 'Contact')
		self.assertEqual('Contact', self.browser.title)

		email_us_link = self.browser.find_element(By.ID, 'email-us-link')
		self.assertEqual(email_us_link.get_attribute('href'), 'mailto:contact@startupwebapp.com?Subject=Contact%20Request')

		call_us_link = self.browser.find_element(By.ID, 'call-us-link')
		self.assertEqual(call_us_link.get_attribute('href'), 'tel:+1-800-800-8000')

		#with self.assertRaises(WebDriverException):
		#	call_us_link.click()
		try:
			call_us_link.click()
		except (WebDriverException) as e:  
			print('clicking on the call us phone number raised exception as expected!', e)
			pass


