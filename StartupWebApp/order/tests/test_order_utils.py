# Unit tests for order utility functions


from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User, Group

from order.models import (
    Cart, Cartdiscount, Cartshippingmethod, Shippingmethod,
    Discountcode, Discounttype, Order,
    Orderdiscount
)
from user.models import Member, Termsofuse

from order.utilities import order_utils


class CalculateCartItemDiscountTest(PostgreSQLTestCase):
    """Test the calculate_cart_item_discount utility function"""

    def setUp(self):
        # Create user and member
        Group.objects.create(name='Members')
        Termsofuse.objects.create(
            version='1',
            version_note='Test',
            publication_date_time=timezone.now()
        )

        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.member = Member.objects.create(user=self.user, mb_cd='MEMBER123')

        # Create discount types
        self.percent_off_type = Discounttype.objects.create(
            title='Percent Off Items',
            applies_to='item_total',
            action='percent-off'
        )

        self.dollar_off_type = Discounttype.objects.create(
            title='Dollar Amount Off Items',
            applies_to='item_total',
            action='dollar-amt-off'
        )

        # Create cart
        self.cart = Cart.objects.create(member=self.member)

    def _create_discount_code(
            self,
            code,
            discounttype,
            discount_amount,
            order_minimum=0.0,
            combinable=True):
        """Helper method to create discount codes with all required fields"""
        return Discountcode.objects.create(
            code=code,
            description=f'{code} discount',
            discounttype=discounttype,
            discount_amount=discount_amount,
            order_minimum=order_minimum,
            combinable=combinable,
            start_date_time=timezone.now(),
            end_date_time=timezone.now() + timedelta(days=30)
        )

    def test_no_discounts_returns_zero(self):
        """Test that function returns 0 when no discount codes applied"""
        item_subtotal = 100.00
        discount = order_utils.calculate_cart_item_discount(self.cart, item_subtotal)
        self.assertEqual(discount, 0)

    def test_percent_off_discount_combinable(self):
        """Test percent-off discount that is combinable"""
        # NOTE: The current implementation does not apply combinable discounts
        # (see order_utils.py lines 279-281 - just has 'pass')
        discount_code = self._create_discount_code(
            'SAVE10', self.percent_off_type, 10.0, combinable=True
        )
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount_code)

        item_subtotal = 100.00
        discount = order_utils.calculate_cart_item_discount(self.cart, item_subtotal)
        # Combinable discounts are not implemented, so discount is 0
        self.assertEqual(discount, 0)

    def test_percent_off_discount_non_combinable(self):
        """Test percent-off discount that is non-combinable"""
        discount_code = self._create_discount_code(
            'SAVE20', self.percent_off_type, 20.0, combinable=False
        )
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount_code)

        item_subtotal = 100.00
        discount = order_utils.calculate_cart_item_discount(self.cart, item_subtotal)
        self.assertEqual(discount, 20.0)  # 20% of 100

    def test_dollar_off_discount_non_combinable(self):
        """Test dollar-amount-off discount that is non-combinable"""
        discount_code = self._create_discount_code(
            'SAVE15', self.dollar_off_type, 15.0, combinable=False
        )
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount_code)

        item_subtotal = 100.00
        discount = order_utils.calculate_cart_item_discount(self.cart, item_subtotal)
        self.assertEqual(discount, 15.0)

    def test_discount_below_order_minimum_not_applied(self):
        """Test that discount is not applied if order minimum not met"""
        discount_code = self._create_discount_code(
            'SAVE10MIN50', self.percent_off_type, 10.0, order_minimum=50.0, combinable=False
        )
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount_code)

        item_subtotal = 40.00  # Below minimum
        discount = order_utils.calculate_cart_item_discount(self.cart, item_subtotal)
        self.assertEqual(discount, 0)

    def test_discount_meets_order_minimum_applied(self):
        """Test that discount is applied when order minimum is met"""
        discount_code = self._create_discount_code(
            'SAVE10MIN50', self.percent_off_type, 10.0, order_minimum=50.0, combinable=False
        )
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount_code)

        item_subtotal = 100.00  # Above minimum
        discount = order_utils.calculate_cart_item_discount(self.cart, item_subtotal)
        self.assertEqual(discount, 10.0)

    def test_multiple_non_combinable_only_first_applied(self):
        """Test that when multiple non-combinable discounts exist, only first is applied"""
        discount_code1 = self._create_discount_code(
            'FIRST20', self.percent_off_type, 20.0, combinable=False
        )
        discount_code2 = self._create_discount_code(
            'SECOND30', self.percent_off_type, 30.0, combinable=False
        )

        # Add first discount
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount_code1)
        # Add second discount
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount_code2)

        item_subtotal = 100.00
        discount = order_utils.calculate_cart_item_discount(self.cart, item_subtotal)
        # Should only apply first non-combinable discount (20%)
        self.assertEqual(discount, 20.0)


class CalculateShippingDiscountTest(PostgreSQLTestCase):
    """Test the calculate_shipping_discount utility function"""

    def setUp(self):
        # Create user and member
        Group.objects.create(name='Members')
        Termsofuse.objects.create(
            version='1',
            version_note='Test',
            publication_date_time=timezone.now()
        )

        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.member = Member.objects.create(user=self.user, mb_cd='MEMBER123')

        # Create shipping discount type
        self.shipping_discount_type = Discounttype.objects.create(
            title='Free Shipping',
            applies_to='shipping',
            action='percent-off'
        )

        # Create shipping method
        # NOTE: Implementation only applies discount for 'USPSRetailGround' identifier
        self.shipping_method = Shippingmethod.objects.create(
            identifier='USPSRetailGround',
            carrier='USPS',
            shipping_cost=10.00,
            tracking_code_base_url='https://tools.usps.com/track',
            active=True
        )

        # Create cart
        self.cart = Cart.objects.create(member=self.member)

    def _create_discount_code(
            self,
            code,
            discounttype,
            discount_amount,
            order_minimum=0.0,
            combinable=True):
        """Helper method to create discount codes with all required fields"""
        return Discountcode.objects.create(
            code=code,
            description=f'{code} discount',
            discounttype=discounttype,
            discount_amount=discount_amount,
            order_minimum=order_minimum,
            combinable=combinable,
            start_date_time=timezone.now(),
            end_date_time=timezone.now() + timedelta(days=30)
        )

    def test_no_shipping_discounts_returns_zero(self):
        """Test that function returns 0 when no shipping discount codes applied"""
        item_subtotal = 100.00
        discount = order_utils.calculate_shipping_discount(self.cart, item_subtotal)
        self.assertEqual(discount, 0)

    def test_shipping_discount_without_shipping_method(self):
        """Test that shipping discount is not applied if no shipping method selected"""
        discount_code = self._create_discount_code(
            'FREESHIP', self.shipping_discount_type, 100.0  # 100% off
        )
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount_code)

        item_subtotal = 100.00
        discount = order_utils.calculate_shipping_discount(self.cart, item_subtotal)
        # No shipping method selected, so no discount applied
        self.assertEqual(discount, 0)

    def test_shipping_discount_with_shipping_method(self):
        """Test that shipping discount is applied when shipping method exists"""
        discount_code = self._create_discount_code(
            'FREESHIP', self.shipping_discount_type, 100.0  # 100% off
        )
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount_code)

        # Add shipping method to cart
        Cartshippingmethod.objects.create(
            cart=self.cart,
            shippingmethod=self.shipping_method
        )

        item_subtotal = 100.00
        discount = order_utils.calculate_shipping_discount(self.cart, item_subtotal)
        # Should get 100% of shipping cost (10.00)
        self.assertEqual(discount, 10.0)

    def test_shipping_discount_below_order_minimum(self):
        """Test that shipping discount is not applied if order minimum not met"""
        discount_code = self._create_discount_code(
            'FREESHIPMIN50', self.shipping_discount_type, 100.0, order_minimum=50.0
        )
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount_code)

        # Add shipping method to cart
        Cartshippingmethod.objects.create(
            cart=self.cart,
            shippingmethod=self.shipping_method
        )

        item_subtotal = 40.00  # Below minimum
        discount = order_utils.calculate_shipping_discount(self.cart, item_subtotal)
        self.assertEqual(discount, 0)

    def test_shipping_discount_meets_order_minimum(self):
        """Test that shipping discount is applied when order minimum is met"""
        discount_code = self._create_discount_code(
            'FREESHIPMIN50', self.shipping_discount_type, 100.0, order_minimum=50.0
        )
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount_code)

        # Add shipping method to cart
        Cartshippingmethod.objects.create(
            cart=self.cart,
            shippingmethod=self.shipping_method
        )

        item_subtotal = 100.00  # Above minimum
        discount = order_utils.calculate_shipping_discount(self.cart, item_subtotal)
        self.assertEqual(discount, 10.0)

    def test_partial_shipping_discount(self):
        """Test partial shipping discount (e.g., 50% off)"""
        # NOTE: The implementation doesn't use discount_amount - always gives 100% off
        discount_code = self._create_discount_code(
            'HALFSHIP', self.shipping_discount_type, 50.0  # 50% off
        )
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount_code)

        # Add shipping method to cart
        Cartshippingmethod.objects.create(
            cart=self.cart,
            shippingmethod=self.shipping_method
        )

        item_subtotal = 100.00
        discount = order_utils.calculate_shipping_discount(self.cart, item_subtotal)
        # Implementation always gives 100% off (full shipping_cost), not the discount_amount
        self.assertEqual(discount, 10.0)


class GetOrderDiscountCodesTest(PostgreSQLTestCase):
    """Test the get_order_discount_codes utility function"""

    def setUp(self):
        # Create user and member
        Group.objects.create(name='Members')
        Termsofuse.objects.create(
            version='1',
            version_note='Test',
            publication_date_time=timezone.now()
        )

        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.member = Member.objects.create(user=self.user, mb_cd='MEMBER123')

        # Create discount type
        self.discount_type = Discounttype.objects.create(
            title='Percent Off',
            applies_to='item_total',
            action='percent-off'
        )

        # Create shipping method for order
        self.shipping_method = Shippingmethod.objects.create(
            identifier='standard',
            carrier='USPS',
            shipping_cost=10.00,
            tracking_code_base_url='https://test.com',
            active=True
        )

        # Create order
        self.order = Order.objects.create(
            member=self.member,
            identifier='TEST-ORDER-123',
            item_subtotal=100.00,
            item_discount_amt=10.00,
            shipping_amt=10.00,
            shipping_discount_amt=0.00,
            order_total=100.00,
            agreed_with_terms_of_sale=True,
            order_date_time=timezone.now()
        )

    def _create_discount_code(
            self,
            code,
            discounttype,
            discount_amount,
            order_minimum=0.0,
            combinable=True):
        """Helper method to create discount codes"""
        return Discountcode.objects.create(
            code=code,
            description=f'{code} - {{}}% off',
            discounttype=discounttype,
            discount_amount=discount_amount,
            order_minimum=order_minimum,
            combinable=combinable,
            start_date_time=timezone.now(),
            end_date_time=timezone.now() + timedelta(days=30)
        )

    def test_no_discount_codes_returns_empty_dict(self):
        """Test that function returns empty dict when no discount codes"""
        discount_dict = order_utils.get_order_discount_codes(self.order)
        self.assertEqual(discount_dict, {})

    def test_single_discount_code_returns_complete_data(self):
        """Test that function returns complete discount code data"""
        discount_code = self._create_discount_code(
            'SAVE20', self.discount_type, 20.0, combinable=False
        )
        Orderdiscount.objects.create(
            order=self.order,
            discountcode=discount_code,
            applied=True
        )

        discount_dict = order_utils.get_order_discount_codes(self.order)

        self.assertEqual(len(discount_dict), 1)
        self.assertIn(discount_code.id, discount_dict)

        data = discount_dict[discount_code.id]
        self.assertEqual(data['discount_code_id'], discount_code.id)
        self.assertEqual(data['code'], 'SAVE20')
        self.assertEqual(data['discount_amount'], 20.0)
        self.assertEqual(data['combinable'], False)
        self.assertEqual(data['discount_applied'], True)
        self.assertEqual(data['discounttype__title'], 'Percent Off')
        self.assertEqual(data['discounttype__action'], 'percent-off')

    def test_multiple_discount_codes_returns_all(self):
        """Test that function returns all discount codes"""
        discount_code1 = self._create_discount_code(
            'FIRST10', self.discount_type, 10.0
        )
        discount_code2 = self._create_discount_code(
            'SECOND15', self.discount_type, 15.0
        )

        Orderdiscount.objects.create(
            order=self.order,
            discountcode=discount_code1,
            applied=True
        )
        Orderdiscount.objects.create(
            order=self.order,
            discountcode=discount_code2,
            applied=False
        )

        discount_dict = order_utils.get_order_discount_codes(self.order)

        self.assertEqual(len(discount_dict), 2)
        self.assertIn(discount_code1.id, discount_dict)
        self.assertIn(discount_code2.id, discount_dict)
        self.assertEqual(discount_dict[discount_code1.id]['discount_applied'], True)
        self.assertEqual(discount_dict[discount_code2.id]['discount_applied'], False)


class GetConfirmationEmailDiscountCodeTextFormatTest(PostgreSQLTestCase):
    """Test the get_confirmation_email_discount_code_text_format utility function"""

    def test_empty_dict_returns_none(self):
        """Test that empty discount dict returns 'None'"""
        result = order_utils.get_confirmation_email_discount_code_text_format({})
        self.assertEqual(result, 'None')

    def test_single_applied_discount_formats_correctly(self):
        """Test that a single applied discount formats correctly"""
        discount_dict = {
            1: {
                'code': 'SAVE20',
                'description': '{}% off items',
                'discount_amount': 20.0,
                'combinable': True,
                'discount_applied': True
            }
        }

        result = order_utils.get_confirmation_email_discount_code_text_format(discount_dict)

        self.assertIn('Code: SAVE20', result)
        self.assertIn('20.0% off items', result)
        self.assertIn('Combinable: Yes', result)
        self.assertNotIn('[This code cannot be combined', result)

    def test_unapplied_discount_shows_warning(self):
        """Test that unapplied discount shows warning message"""
        discount_dict = {
            1: {
                'code': 'INVALID',
                'description': '{}% off items',
                'discount_amount': 10.0,
                'combinable': False,
                'discount_applied': False
            }
        }

        result = order_utils.get_confirmation_email_discount_code_text_format(discount_dict)

        self.assertIn('Code: INVALID', result)
        self.assertIn('[This code cannot be combined or does not qualify for your order.]', result)
        self.assertIn('Combinable: No', result)

    def test_multiple_discounts_format_with_line_breaks(self):
        """Test that multiple discounts are separated by line breaks"""
        discount_dict = {
            1: {
                'code': 'FIRST',
                'description': '{}% off',
                'discount_amount': 10.0,
                'combinable': True,
                'discount_applied': True
            },
            2: {
                'code': 'SECOND',
                'description': '{}% off',
                'discount_amount': 15.0,
                'combinable': True,
                'discount_applied': True
            }
        }

        result = order_utils.get_confirmation_email_discount_code_text_format(discount_dict)

        self.assertIn('Code: FIRST', result)
        self.assertIn('Code: SECOND', result)
        self.assertIn('\r\n', result)  # Line breaks between codes


class GetStripeCustomerPaymentDataTest(PostgreSQLTestCase):
    """Test the get_stripe_customer_payment_data utility function"""

    def test_with_shipping_address_provided(self):
        """Test formatting customer payment data with shipping address provided"""
        from unittest.mock import MagicMock

        # Mock Stripe customer object
        mock_customer = MagicMock()
        mock_customer.email = 'test@test.com'
        mock_customer.default_source = 'card_123'

        # Mock card/source object
        mock_source = MagicMock()
        mock_source.id = 'card_123'
        mock_source.name = 'Test Cardholder'
        mock_source.brand = 'Visa'
        mock_source.last4 = '4242'
        mock_source.exp_month = 12
        mock_source.exp_year = 2025
        mock_source.address_line1 = '999 Card Address'
        mock_source.address_city = 'Cardtown'
        mock_source.address_state = 'CA'
        mock_source.address_zip = '99999'
        mock_source.address_country = 'United States'
        mock_source.country = 'US'
        mock_source.object = 'card'

        mock_customer.sources.data = [mock_source]

        # Shipping address that overrides card address
        shipping_address = {
            'name': 'Shipping Name',
            'address_line1': '123 Shipping St',
            'city': 'Shiptown',
            'state': 'NY',
            'zip': '12345',
            'country': 'United States',
            'country_code': 'US'
        }

        result = order_utils.get_stripe_customer_payment_data(
            mock_customer,
            shipping_address,
            'card_123'
        )

        # Verify shipping address from parameter is used
        self.assertEqual(result['args']['shipping_name'], 'Shipping Name')
        self.assertEqual(result['args']['shipping_address_line1'], '123 Shipping St')
        self.assertEqual(result['args']['shipping_address_city'], 'Shiptown')
        self.assertEqual(result['args']['shipping_address_state'], 'NY')
        self.assertEqual(result['args']['shipping_address_zip'], '12345')

        # Verify billing address from card
        self.assertEqual(result['args']['billing_name'], 'Test Cardholder')
        self.assertEqual(result['args']['billing_address_line1'], '999 Card Address')

        # Verify card data in token
        self.assertEqual(result['token']['card']['brand'], 'Visa')
        self.assertEqual(result['token']['card']['last4'], '4242')
        self.assertEqual(result['token']['email'], 'test@test.com')

    def test_without_shipping_address(self):
        """Test formatting customer payment data without shipping address (uses card address)"""
        from unittest.mock import MagicMock

        # Mock Stripe customer object
        mock_customer = MagicMock()
        mock_customer.email = 'test@test.com'
        mock_customer.default_source = 'card_456'

        # Mock card/source object
        mock_source = MagicMock()
        mock_source.id = 'card_456'
        mock_source.name = 'Card Owner'
        mock_source.brand = 'Mastercard'
        mock_source.last4 = '5555'
        mock_source.exp_month = 6
        mock_source.exp_year = 2026
        mock_source.address_line1 = '456 Card St'
        mock_source.address_city = 'Cardcity'
        mock_source.address_state = 'TX'
        mock_source.address_zip = '54321'
        mock_source.address_country = 'United States'
        mock_source.country = 'US'
        mock_source.object = 'card'

        mock_customer.sources.data = [mock_source]

        result = order_utils.get_stripe_customer_payment_data(
            mock_customer,
            None,  # No shipping address provided
            'card_456'
        )

        # Verify shipping address comes from card when not provided
        self.assertEqual(result['args']['shipping_name'], 'Card Owner')
        self.assertEqual(result['args']['shipping_address_line1'], '456 Card St')
        self.assertEqual(result['args']['shipping_address_city'], 'Cardcity')
        self.assertEqual(result['args']['shipping_address_state'], 'TX')
        self.assertEqual(result['args']['shipping_address_zip'], '54321')

    def test_with_no_card_id_uses_default(self):
        """Test that None card_id uses customer's default_source"""
        from unittest.mock import MagicMock

        # Mock Stripe customer object
        mock_customer = MagicMock()
        mock_customer.email = 'test@test.com'
        mock_customer.default_source = 'card_default'

        # Mock card/source object
        mock_source = MagicMock()
        mock_source.id = 'card_default'
        mock_source.name = 'Default Card'
        mock_source.brand = 'Amex'
        mock_source.last4 = '1234'
        mock_source.exp_month = 3
        mock_source.exp_year = 2027
        mock_source.address_line1 = '789 Default Ave'
        mock_source.address_city = 'Defcity'
        mock_source.address_state = 'FL'
        mock_source.address_zip = '78901'
        mock_source.address_country = 'United States'
        mock_source.country = 'US'
        mock_source.object = 'card'

        mock_customer.sources.data = [mock_source]

        result = order_utils.get_stripe_customer_payment_data(
            mock_customer,
            None,
            None  # No card_id provided, should use default_source
        )

        # Verify default card was found and used
        self.assertEqual(result['token']['card']['brand'], 'Amex')
        self.assertEqual(result['token']['card']['last4'], '1234')
        self.assertEqual(result['args']['shipping_name'], 'Default Card')


class LookUpMemberCartTest(PostgreSQLTestCase):
    """Test the look_up_member_cart utility function"""

    def setUp(self):
        from django.contrib.auth.models import User, Group
        from user.models import Member, Termsofuse
        from django.utils import timezone

        Group.objects.create(name='Members')
        Termsofuse.objects.create(
            version='1',
            version_note='Test',
            publication_date_time=timezone.now()
        )

        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.member = Member.objects.create(user=self.user, mb_cd='MEMBER123')

    def test_returns_member_cart_when_exists(self):
        """Test that member's cart is returned when it exists"""
        from django.test import RequestFactory
        from order.models import Cart

        # Create cart for member
        cart = Cart.objects.create(member=self.member)

        # Create request with authenticated user
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user

        result = order_utils.look_up_member_cart(request)

        self.assertIsNotNone(result)
        self.assertEqual(result.id, cart.id)
        self.assertEqual(result.member, self.member)

    def test_returns_none_when_no_cart_exists(self):
        """Test that None is returned when member has no cart"""
        from django.test import RequestFactory

        # Don't create any cart for member

        # Create request with authenticated user
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user

        result = order_utils.look_up_member_cart(request)

        self.assertIsNone(result)


class LookUpAnonymousCartTest(PostgreSQLTestCase):
    """Test the look_up_anonymous_cart utility function"""

    def test_returns_anonymous_cart_when_exists(self):
        """Test that anonymous cart is returned when cookie and cart exist"""
        from django.test import RequestFactory
        from order.models import Cart

        # Create anonymous cart
        anonymous_cart_id = 'anon_cart_123'
        cart = Cart.objects.create(anonymous_cart_id=anonymous_cart_id)

        # Create request with signed cookie
        factory = RequestFactory()
        request = factory.get('/')
        request.user = type('AnonymousUser', (), {'is_authenticated': False})()

        # Mock get_signed_cookie to return our anonymous cart ID
        request.get_signed_cookie = lambda key, default=None, salt=None: anonymous_cart_id

        result = order_utils.look_up_anonymous_cart(request)

        self.assertIsNotNone(result)
        self.assertEqual(result.id, cart.id)
        self.assertEqual(result.anonymous_cart_id, anonymous_cart_id)

    def test_returns_none_when_no_cart_exists(self):
        """Test that None is returned when cookie exists but no cart"""
        from django.test import RequestFactory

        # Don't create any cart

        # Create request with signed cookie
        factory = RequestFactory()
        request = factory.get('/')
        request.user = type('AnonymousUser', (), {'is_authenticated': False})()

        # Mock get_signed_cookie to return a cart ID that doesn't exist
        request.get_signed_cookie = lambda key, default=None, salt=None: 'nonexistent_cart'

        result = order_utils.look_up_anonymous_cart(request)

        self.assertIsNone(result)

    def test_returns_none_when_cookie_is_false(self):
        """Test that None is returned when cookie is False (default)"""
        from django.test import RequestFactory

        # Create request without signed cookie (returns False)
        factory = RequestFactory()
        request = factory.get('/')
        request.user = type('AnonymousUser', (), {'is_authenticated': False})()

        # Mock get_signed_cookie to return False (default when cookie doesn't exist)
        request.get_signed_cookie = lambda key, default=None, salt=None: False

        result = order_utils.look_up_anonymous_cart(request)

        self.assertIsNone(result)


class StripeUtilityFunctionsErrorHandlingTest(PostgreSQLTestCase):
    """Test error handling in Stripe utility functions"""

    def test_create_stripe_customer_handles_invalid_request_error(self):
        """Test that create_stripe_customer handles Stripe InvalidRequestError gracefully"""
        from unittest.mock import patch
        import stripe

        with patch('stripe.Customer.create') as mock_stripe_create:
            mock_stripe_create.side_effect = stripe.error.InvalidRequestError(
                message='Invalid token: tok_invalid',
                param='source'
            )

            result = order_utils.create_stripe_customer(
                stripe_token='tok_invalid',
                email='test@test.com',
                metadata_key='test_key',
                metadata_value='test_value'
            )

            # Should return None instead of raising exception
            self.assertIsNone(result)

    def test_create_stripe_customer_handles_authentication_error(self):
        """Test that create_stripe_customer handles Stripe AuthenticationError gracefully"""
        from unittest.mock import patch
        import stripe

        with patch('stripe.Customer.create') as mock_stripe_create:
            mock_stripe_create.side_effect = stripe.error.AuthenticationError(
                message='Invalid API Key provided'
            )

            result = order_utils.create_stripe_customer(
                stripe_token='tok_test',
                email='test@test.com',
                metadata_key='test_key',
                metadata_value='test_value'
            )

            # Should return None instead of raising exception
            self.assertIsNone(result)

    def test_stripe_customer_add_card_handles_invalid_request_error(self):
        """Test that stripe_customer_add_card handles Stripe InvalidRequestError gracefully"""
        from unittest.mock import patch
        import stripe

        with patch('stripe.Customer.retrieve') as mock_stripe_retrieve:
            mock_stripe_retrieve.side_effect = stripe.error.InvalidRequestError(
                message='No such customer: cus_invalid',
                param='id'
            )

            result = order_utils.stripe_customer_add_card(
                customer_token='cus_invalid',
                stripe_token='tok_test'
            )

            # Should return None instead of raising exception
            self.assertIsNone(result)

    def test_stripe_customer_add_card_handles_api_connection_error(self):
        """Test that stripe_customer_add_card handles Stripe APIConnectionError gracefully"""
        from unittest.mock import patch
        import stripe

        with patch('stripe.Customer.retrieve') as mock_stripe_retrieve:
            mock_stripe_retrieve.side_effect = stripe.error.APIConnectionError(
                message='Network communication with Stripe failed'
            )

            result = order_utils.stripe_customer_add_card(
                customer_token='cus_test',
                stripe_token='tok_test'
            )

            # Should return None instead of raising exception
            self.assertIsNone(result)
