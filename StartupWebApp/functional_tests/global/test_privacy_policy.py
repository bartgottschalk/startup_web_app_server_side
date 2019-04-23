# Selenium Functional Tests (from the perspective of the user)

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities

from unittest import skip

class PrivacyPolicyPageFunctionalTests(BaseFunctionalTest):

	def test_privacy_policy_page_load(self):
		self.browser.get(self.static_home_page_url + 'privacy-policy')
		functional_testing_utilities.wait_for_page_title(self, 'Privacy Policy')
		self.assertEqual('Privacy Policy', self.browser.title)

		# Terms of Use link
		# Privacy Policy link
		# Terms of Sale link
		# Medical Disclaimer link		