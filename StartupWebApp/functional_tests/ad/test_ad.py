# Selenium Functional Tests (from the perspective of the user)

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities
from selenium.webdriver.common.by import By

from unittest import skip

class AdPageTests(BaseFunctionalTest):

    def test_about_page(self):
        self.browser.get(self.static_home_page_url + 'ad')
        functional_testing_utilities.wait_for_page_title(self, 'Ad Example')
        self.assertEqual('Ad Example', self.browser.title)

        functional_testing_utilities.wait_for_element_to_load_by_id(self, 'pythonabot-google-ad-example')
        # ensure the ad link is correct
        self.assertIn('/pythonabot?ad_cd=E0y04nClr68pywMIyUxn', self.browser.find_element(By.ID, 'pythonabot-google-ad-example').get_attribute('href'))
        # ensure that the add image is visible
        self.assertNotIn('hide', self.browser.find_element(By.ID, 'pythonabot-google-ad-example-img').get_attribute('class'))

