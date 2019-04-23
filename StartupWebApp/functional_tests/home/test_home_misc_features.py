# Selenium Functional Tests (from the perspective of the user)

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities

import time
from unittest import skip

class HomePageMiscFeatureTests(BaseFunctionalTest):

	def test_page_title(self):
		self.browser.get(self.static_home_page_url)
		functional_testing_utilities.wait_for_page_title(self, 'Home Page')
		self.assertEqual('Home Page', self.browser.title)
