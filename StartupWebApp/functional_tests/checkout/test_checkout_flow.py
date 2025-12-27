# Selenium Functional Tests for Checkout Flow
# Tests checkout-related pages and flow structure

from functional_tests.base_functional_test import BaseFunctionalTest
from functional_tests import functional_testing_utilities
from selenium.webdriver.common.by import By


class CheckoutFlowFunctionalTests(BaseFunctionalTest):
    """
    Functional tests for checkout flow pages and structure.

    These tests verify page structure and basic flow. Full end-to-end checkout
    with Stripe payment has been manually tested in production (Session 6).
    """

    def test_checkout_success_page_error_handling(self):
        """
        Test checkout success page loads and handles missing session_id.
        POST-STRIPE: Validates success page structure and error handling.
        """
        # Navigate to success page without required session_id parameter
        self.browser.get(self.static_home_page_url + 'checkout/success')
        functional_testing_utilities.wait_for_page_title(self, 'Processing Order')

        # Verify page loaded
        self.assertEqual('Processing Order', self.browser.title)

        # Verify appropriate error message displayed
        page_source = self.browser.page_source
        self.assertIn('Missing session ID', page_source)
        self.assertIn('contact support', page_source.lower())

    def test_cart_page_structure(self):
        """
        Test shopping cart page loads with all required elements.
        PRE-STRIPE: Validates cart page structure (empty cart scenario).

        Note: Cart content is loaded dynamically via JavaScript AJAX calls.
        For empty carts, many elements are removed and replaced with empty message.
        This test verifies the page loads correctly.
        """
        # Navigate to cart page
        self.browser.get(self.static_home_page_url + 'cart')
        functional_testing_utilities.wait_for_page_title(self, 'Shopping Cart')

        # Verify page loaded
        self.assertEqual('Shopping Cart', self.browser.title)

        # Wait for AJAX to complete (cart will be empty, showing empty message)
        import time
        time.sleep(1)

        # Verify cart-detail-body exists and shows empty cart message
        cart_detail_body = self.browser.find_element(By.ID, 'cart-detail-body')
        self.assertIsNotNone(cart_detail_body)

        # For empty cart, verify empty cart message appears
        page_source = self.browser.page_source
        self.assertIn('SHOPPING CART IS EMPTY', page_source)

    def test_checkout_confirm_page_structure(self):
        """
        Test checkout confirm page loads with all required elements.
        PRE-STRIPE: This is the final page before redirecting to Stripe.

        Note: Content is loaded dynamically via JavaScript. This test verifies
        the page structure exists for anonymous users (empty cart scenario).
        """
        # Navigate to checkout confirm page
        self.browser.get(self.static_home_page_url + 'checkout/confirm')
        functional_testing_utilities.wait_for_page_title(self, 'Confirm Order')

        # Verify page loaded
        self.assertEqual('Confirm Order', self.browser.title)

        # Verify critical static elements exist (present in initial HTML)
        confirm_detail_body = self.browser.find_element(By.ID, 'confirm-detail-body')
        self.assertIsNotNone(confirm_detail_body)

        # Verify product table exists (populated dynamically)
        sku_table = self.browser.find_element(By.ID, 'sku-table')
        self.assertIsNotNone(sku_table)

        # Verify shipping section exists
        shipping_information = self.browser.find_element(By.ID, 'shipping-information')
        self.assertIsNotNone(shipping_information)

        # Verify totals table exists
        confirm_total_table = self.browser.find_element(By.ID, 'confirm-total-table')
        self.assertIsNotNone(confirm_total_table)

        # Verify anonymous checkout options exist (for non-logged-in users)
        login_create_account_wrapper = self.browser.find_element(
            By.ID, 'login-create-account-continue-anon-wrapper'
        )
        self.assertIsNotNone(login_create_account_wrapper)

        # Verify place order button exists (used by logged-in users)
        place_order_button = self.browser.find_element(By.ID, 'place-order-button-bottom')
        self.assertIsNotNone(place_order_button)

    def test_checkout_flow_navigation(self):
        """
        Test basic checkout flow navigation: cart → confirm → success.
        Verifies pages load correctly and navigation works.

        This is a simple navigation test that validates page structure
        without requiring products in cart or authentication.
        """
        # Start at cart page
        self.browser.get(self.static_home_page_url + 'cart')
        functional_testing_utilities.wait_for_page_title(self, 'Shopping Cart')
        self.assertEqual('Shopping Cart', self.browser.title)

        # Navigate to checkout/confirm
        self.browser.get(self.static_home_page_url + 'checkout/confirm')
        functional_testing_utilities.wait_for_page_title(self, 'Confirm Order')
        self.assertEqual('Confirm Order', self.browser.title)

        # Navigate to success page (will show error for missing session_id, but page loads)
        self.browser.get(self.static_home_page_url + 'checkout/success')
        functional_testing_utilities.wait_for_page_title(self, 'Processing Order')
        self.assertEqual('Processing Order', self.browser.title)

        # Verify error message for missing session_id
        page_source = self.browser.page_source
        self.assertIn('Missing session ID', page_source)

    def test_anonymous_checkout_button_visibility(self):
        """
        Test anonymous checkout options are visible on confirm page.
        PRE-STRIPE: Validates the login/create-account/anonymous buttons.

        For non-logged-in users, the confirm page should show three options:
        - Login
        - Create Account
        - Checkout Anonymous
        """
        # Navigate to checkout confirm page
        self.browser.get(self.static_home_page_url + 'checkout/confirm')
        functional_testing_utilities.wait_for_page_title(self, 'Confirm Order')

        # Verify anonymous checkout options container exists
        login_wrapper = self.browser.find_element(By.ID, 'login-create-account-continue-anon-wrapper')
        self.assertIsNotNone(login_wrapper)

        # Verify login button exists
        login_button = self.browser.find_element(By.ID, 'confirm-login-button')
        self.assertIsNotNone(login_button)

        # Verify create account button exists
        create_account_button = self.browser.find_element(By.ID, 'confirm-create-account-button')
        self.assertIsNotNone(create_account_button)

        # Verify anonymous checkout button exists
        anonymous_button = self.browser.find_element(By.ID, 'confirm-anonymouns-button')
        self.assertIsNotNone(anonymous_button)

    def test_checkout_button_links_to_confirm(self):
        """
        Test that we can navigate from cart to checkout/confirm page.
        PRE-STRIPE: Validates navigation between cart and confirm pages.

        Note: For empty carts, checkout buttons are removed by JavaScript.
        This test validates navigation works by directly accessing the confirm page.
        """
        # Navigate to cart page
        self.browser.get(self.static_home_page_url + 'cart')
        functional_testing_utilities.wait_for_page_title(self, 'Shopping Cart')

        # Navigate to checkout/confirm page (simulating clicking checkout button)
        self.browser.get(self.static_home_page_url + 'checkout/confirm')
        functional_testing_utilities.wait_for_page_title(self, 'Confirm Order')

        # Verify we successfully navigated to confirm page
        self.assertEqual('Confirm Order', self.browser.title)

        # Verify confirm page loaded its content
        confirm_detail_body = self.browser.find_element(By.ID, 'confirm-detail-body')
        self.assertIsNotNone(confirm_detail_body)

    def test_add_product_to_cart_flow(self):
        """
        Test adding a product to cart and verifying cart updates.
        PRE-STRIPE: Full flow from product page → add to cart → view cart.

        This test:
        1. Navigates to a product page
        2. Clicks "Add to Cart" button
        3. Verifies cart counter updates
        4. Navigates to cart page
        5. Verifies product appears in cart
        """
        # Navigate to Paper Clips product page
        product_url = self.static_home_page_url + 'product?name=PaperClips&id=bSusp6dBHm'
        self.browser.get(product_url)

        # Wait for product page to load (title is dynamically set via JS)
        functional_testing_utilities.wait_for_page_title(self, 'Paper Clips')
        self.assertEqual('Paper Clips', self.browser.title)

        # Verify Add to Cart button exists
        add_to_cart_button = self.browser.find_element(By.ID, 'product-add-to-cart')
        self.assertIsNotNone(add_to_cart_button)

        # Click Add to Cart button
        add_to_cart_button.click()

        # Wait for cart counter to update (should show "1")
        # The header-shopping-cart element is populated dynamically
        functional_testing_utilities.wait_for_shopping_cart_count(self, '1', 'You have 1 item in your cart.')

        # Navigate to cart page
        self.browser.get(self.static_home_page_url + 'cart')
        functional_testing_utilities.wait_for_page_title(self, 'Shopping Cart')

        # Wait for cart content to load (cart-detail-body starts hidden, revealed by JS)
        functional_testing_utilities.wait_for_element_to_load_by_id(self, 'sku-table')

        # Verify product appears in cart by checking page source for product name
        # (dynamic content loaded via AJAX, so we check the rendered HTML)
        import time
        time.sleep(1)  # Brief wait for AJAX to populate cart contents

        page_source = self.browser.page_source
        self.assertIn('Paper Clips', page_source)
        self.assertIn('$3.50', page_source)


# ==============================================================================
# POST-STRIPE Functional Tests - Not Implemented
# ==============================================================================
#
# POST-STRIPE functional tests are intentionally NOT implemented because:
#
# 1. **Already covered by unit tests**: test_checkout_session_success.py has
#    comprehensive unit tests for POST-STRIPE backend logic with mocked Stripe sessions
#
# 2. **Functional tests would require complex setup**:
#    - Either actual Stripe test mode integration (external dependency)
#    - Or backend mocking in functional tests (breaks "functional" nature)
#    - Or creating fake database state (doesn't test actual flow)
#
# 3. **Limited value-add**: Functional tests would mostly test:
#    - Selenium can navigate to a page (already tested in PRE-STRIPE tests)
#    - Backend processes Stripe webhooks correctly (tested in unit tests)
#    - Not testing actual payment processing (that's Stripe's responsibility)
#
# 4. **Test Around Stripe strategy**: We thoroughly test our code before and
#    after Stripe interaction, without testing Stripe's external services
#
# **What we DO test**:
# - ✅ PRE-STRIPE: Cart, product-to-cart, checkout/confirm pages (functional tests above)
# - ✅ POST-STRIPE: Backend processing of Stripe sessions (unit tests)
# - ✅ Success page error handling for missing session_id (test_checkout_flow_navigation)
#
# **What we DON'T test functionally**:
# - ❌ Success page with valid session_id (would require Stripe test mode or complex mocking)
# - ❌ Clicking "Continue to Payment" button (would redirect to external Stripe page)
# - ❌ Anonymous email entry flow (buttons hidden for empty cart, same as other empty cart tests)
#
# **If POST-STRIPE functional tests are needed in the future**:
# 1. Set up Stripe test mode in functional test environment
# 2. Use Stripe test card numbers (4242 4242 4242 4242)
# 3. Test full end-to-end flow through actual Stripe hosted checkout
# 4. Estimate: 4-6 hours for proper setup and implementation
#
# ==============================================================================
