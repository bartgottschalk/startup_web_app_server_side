# Selenium Functional Tests (from the perspective of the user)

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities

from unittest import skip

class ErrorPageTests(BaseFunctionalTest):

	def test_error_page(self):
		self.browser.get(self.static_home_page_url + 'asdf')		
		functional_testing_utilities.wait_for_page_title(self, 'Error')
		self.assertEqual('Error', self.browser.title)		
		functional_testing_utilities.wait_for_element_by_class_name_text_value(self, 'section-title', 'Sorry,')
		functional_testing_utilities.wait_for_element_by_class_name_text_value(self, 'section-text', 'We didn\'t find the page you requested.')