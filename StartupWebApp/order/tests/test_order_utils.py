# Unit tests for order utility functions

import json

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User, Group

from order.models import (
    Cart, Cartsku, Cartdiscount, Cartshippingmethod,
    Product, Productsku, Productimage,
    Sku, Skuprice, Skutype, Skuinventory,
    Shippingmethod, Discountcode, Discounttype,
    Orderconfiguration, Order, Orderdiscount,
    Orderpayment, Ordershippingaddress, Orderbillingaddress,
    Ordershippingmethod
)
from user.models import Member, Termsofuse

from order.utilities import order_utils


class CalculateCartItemDiscountTest(TestCase):
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

    def _create_discount_code(self, code, discounttype, discount_amount, order_minimum=0.0, combinable=True):
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


class CalculateShippingDiscountTest(TestCase):
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

    def _create_discount_code(self, code, discounttype, discount_amount, order_minimum=0.0, combinable=True):
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


class GetOrderDiscountCodesTest(TestCase):
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

    def _create_discount_code(self, code, discounttype, discount_amount, order_minimum=0.0, combinable=True):
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


class GetConfirmationEmailDiscountCodeTextFormatTest(TestCase):
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
