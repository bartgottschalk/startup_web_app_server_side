# Selenium Functional Tests (from the perspective of the user)

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities

from unittest import skip

class EditMyInformationPageFunctionalTests(BaseFunctionalTest):

	def test_edit_my_information_page_load(self):
		self.browser.get(self.static_home_page_url + 'account/edit-my-information')
		functional_testing_utilities.wait_for_page_title(self, 'Edit My Information')
		self.assertEqual('Edit My Information', self.browser.title)

		# Verify displayed username
		# Cancel - Back to My Account link

	'''
	def test_first_name_field(self):
		self.browser.get(self.static_home_page_url + 'account/edit-my-information')
		# placeholder
		# required
		pass

	def test_last_name_field(self):
		self.browser.get(self.static_home_page_url + 'account/edit-my-information')
		# placeholder
		# required
		pass

	def test_email_address_field(self):
		self.browser.get(self.static_home_page_url + 'account/edit-my-information')
		# placeholder
		# required
		# invalid
		pass

	def test_success(self):
		self.browser.get(self.static_home_page_url + 'account/edit-my-information')
		pass

	'''			
