# Selenium Functional Tests (from the perspective of the user)

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities

from unittest import skip

class ProductsPageFunctionalTests(BaseFunctionalTest):

	def test_products_page_load(self):
		self.browser.get(self.static_home_page_url + 'products')
		functional_testing_utilities.wait_for_page_title(self, 'Products')
		self.assertEqual('Products', self.browser.title)

		# intro text and link
		# grid layout
		# Product links (5/product)
		# Image
		# Title
		# Description
		# Price
		# View Details button
