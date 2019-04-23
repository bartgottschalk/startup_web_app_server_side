# Selenium Functional Tests (from the perspective of the user)

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities

from unittest import skip

class AboutPageTests(BaseFunctionalTest):

	def test_about_page(self):
		self.browser.get(self.static_home_page_url + 'about')
		functional_testing_utilities.wait_for_page_title(self, 'About')
		self.assertEqual('About', self.browser.title)
