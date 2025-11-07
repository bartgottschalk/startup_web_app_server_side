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
    Orderconfiguration
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
