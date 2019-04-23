# Selenium Functional Tests (from the perspective of the user)

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities

from unittest import skip

class EmailUnsubscribeFromLinkPageFunctionalTests(BaseFunctionalTest):

	def test_email_unsubscribe_from_link_page_load(self):
		self.browser.get(self.static_home_page_url + 'account/email-unsubscribe')
		functional_testing_utilities.wait_for_page_title(self, 'Email Unsubscribe')
		self.assertEqual('Email Unsubscribe', self.browser.title)

		# ?

	'''
	def test_(self):
		self.browser.get(self.static_home_page_url + 'account/email-unsubscribe')
		pass

	'''			
