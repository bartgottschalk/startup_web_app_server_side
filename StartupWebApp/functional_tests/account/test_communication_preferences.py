# Selenium Functional Tests (from the perspective of the user)

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities

from unittest import skip

class EditMyCommunicationPreferencesPageFunctionalTests(BaseFunctionalTest):

	def test_edit_my_communication_preferences_page_load(self):
		self.browser.get(self.static_home_page_url + 'account/edit-communication-preferences')
		functional_testing_utilities.wait_for_page_title(self, 'Edit My Communication Preferences')
		self.assertEqual('Edit My Communication Preferences', self.browser.title)

		# Verify Unsubscribed selection
		# Verify Subscribe to Newsletter selection
		# Cancel - Back to My Account link

	'''
	def test_success_unsubscribe_with_reason(self):
		self.browser.get(self.static_home_page_url + 'account/edit-communication-preferences')
		pass

	def test_success_unsubscribe_without_reason(self):
		self.browser.get(self.static_home_page_url + 'account/edit-communication-preferences')
		pass

	def test_success_subscribe_to_newsletter(self):
		self.browser.get(self.static_home_page_url + 'account/edit-communication-preferences')
		pass

	'''			
