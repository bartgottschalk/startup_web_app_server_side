# Unit tests for order utility functions


from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User, Group

from order.models import (
    Cart, Cartdiscount, Cartshippingmethod, Cartsku, Shippingmethod,
    Discountcode, Discounttype, Order, Orderdiscount,
    Sku, Skutype, Skuinventory, Skuprice
)
from decimal import Decimal
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


class GetCartDiscountCodesTest(PostgreSQLTestCase):
    """Test the get_cart_discount_codes utility function with new business rules"""

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

        # Create cart
        self.cart = Cart.objects.create(member=self.member)

        # Create SKU type and inventory
        self.sku_type = Skutype.objects.create(title='product')
        self.sku_inventory = Skuinventory.objects.create(
            title='In Stock',
            identifier='in-stock'
        )

        # Create SKU with price
        self.sku = Sku.objects.create(
            sku_type=self.sku_type,
            sku_inventory=self.sku_inventory,
            color='Red',
            size='Medium'
        )
        Skuprice.objects.create(
            sku=self.sku,
            price=Decimal('100.00'),
            created_date_time=timezone.now()
        )

        # Add SKU to cart
        Cartsku.objects.create(cart=self.cart, sku=self.sku, quantity=1)

        # Create shipping method
        self.shipping_method = Shippingmethod.objects.create(
            identifier='USPSRetailGround',
            carrier='USPS Retail Ground',
            shipping_cost=Decimal('9.56'),
            tracking_code_base_url='https://tools.usps.com/go/TrackConfirmAction?tLabels=',
            active=True
        )

        # Create discount types
        self.item_discount_type = Discounttype.objects.create(
            title='Percent Off',
            applies_to='item_total',
            action='percent-off'
        )
        self.shipping_discount_type = Discounttype.objects.create(
            title='Free Shipping',
            applies_to='shipping',
            action='free-usps-ground-shipping'
        )

    def test_multiple_item_discounts_only_first_applies(self):
        """Test that only the first valid item discount has discount_applied=True"""
        # Create two item discounts
        discount1 = Discountcode.objects.create(
            code='FIRST10',
            description='10% off',
            discounttype=self.item_discount_type,
            discount_amount=Decimal('10'),
            order_minimum=Decimal('0'),
            combinable=True,  # Database flag doesn't matter anymore
            start_date_time=timezone.now(),
            end_date_time=timezone.now() + timedelta(days=30)
        )
        discount2 = Discountcode.objects.create(
            code='SECOND20',
            description='20% off',
            discounttype=self.item_discount_type,
            discount_amount=Decimal('20'),
            order_minimum=Decimal('0'),
            combinable=True,  # Database flag doesn't matter anymore
            start_date_time=timezone.now(),
            end_date_time=timezone.now() + timedelta(days=30)
        )

        # Add both to cart
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount1)
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount2)

        result = order_utils.get_cart_discount_codes(self.cart)

        # Only first discount should be applied
        self.assertEqual(result[discount1.id]['discount_applied'], True)
        self.assertEqual(result[discount2.id]['discount_applied'], False)

    def test_multiple_shipping_discounts_only_first_applies(self):
        """Test that only the first valid shipping discount has discount_applied=True"""
        # Add shipping method to cart
        Cartshippingmethod.objects.create(cart=self.cart, shippingmethod=self.shipping_method)

        # Create two shipping discounts
        discount1 = Discountcode.objects.create(
            code='FREESHIP1',
            description='Free shipping',
            discounttype=self.shipping_discount_type,
            discount_amount=Decimal('0'),
            order_minimum=Decimal('0'),
            combinable=False,  # Database flag doesn't matter anymore
            start_date_time=timezone.now(),
            end_date_time=timezone.now() + timedelta(days=30)
        )
        discount2 = Discountcode.objects.create(
            code='FREESHIP2',
            description='Also free shipping',
            discounttype=self.shipping_discount_type,
            discount_amount=Decimal('0'),
            order_minimum=Decimal('0'),
            combinable=False,  # Database flag doesn't matter anymore
            start_date_time=timezone.now(),
            end_date_time=timezone.now() + timedelta(days=30)
        )

        # Add both to cart
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount1)
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount2)

        result = order_utils.get_cart_discount_codes(self.cart)

        # Only first discount should be applied
        self.assertEqual(result[discount1.id]['discount_applied'], True)
        self.assertEqual(result[discount2.id]['discount_applied'], False)

    def test_item_and_shipping_discounts_both_apply(self):
        """Test that item + shipping discounts can combine"""
        # Add shipping method to cart
        Cartshippingmethod.objects.create(cart=self.cart, shippingmethod=self.shipping_method)

        # Create item discount
        item_discount = Discountcode.objects.create(
            code='SAVE10',
            description='10% off',
            discounttype=self.item_discount_type,
            discount_amount=Decimal('10'),
            order_minimum=Decimal('0'),
            combinable=False,  # Database flag doesn't matter anymore
            start_date_time=timezone.now(),
            end_date_time=timezone.now() + timedelta(days=30)
        )

        # Create shipping discount
        shipping_discount = Discountcode.objects.create(
            code='FREESHIP',
            description='Free shipping',
            discounttype=self.shipping_discount_type,
            discount_amount=Decimal('0'),
            order_minimum=Decimal('0'),
            combinable=False,  # Database flag doesn't matter anymore
            start_date_time=timezone.now(),
            end_date_time=timezone.now() + timedelta(days=30)
        )

        # Add both to cart
        Cartdiscount.objects.create(cart=self.cart, discountcode=item_discount)
        Cartdiscount.objects.create(cart=self.cart, discountcode=shipping_discount)

        result = order_utils.get_cart_discount_codes(self.cart)

        # Both should be applied
        self.assertEqual(result[item_discount.id]['discount_applied'], True)
        self.assertEqual(result[shipping_discount.id]['discount_applied'], True)

    def test_item_discount_not_applied_when_minimum_not_met(self):
        """Test that discount with unmet order minimum has discount_applied=False"""
        # Create discount with high minimum
        discount = Discountcode.objects.create(
            code='BIG100',
            description='10% off orders over $200',
            discounttype=self.item_discount_type,
            discount_amount=Decimal('10'),
            order_minimum=Decimal('200.00'),  # Cart only has $100
            combinable=True,
            start_date_time=timezone.now(),
            end_date_time=timezone.now() + timedelta(days=30)
        )

        Cartdiscount.objects.create(cart=self.cart, discountcode=discount)

        result = order_utils.get_cart_discount_codes(self.cart)

        # Discount should not be applied
        self.assertEqual(result[discount.id]['discount_applied'], False)

    def test_shipping_discount_not_applied_without_usps_shipping(self):
        """Test that shipping discount requires USPS Retail Ground shipping method"""
        # Create non-USPS shipping method
        fedex_shipping = Shippingmethod.objects.create(
            identifier='FedExGround',
            carrier='FedEx',
            shipping_cost=Decimal('15.00'),
            tracking_code_base_url='https://fedex.com',
            active=True
        )
        Cartshippingmethod.objects.create(cart=self.cart, shippingmethod=fedex_shipping)

        # Create shipping discount
        discount = Discountcode.objects.create(
            code='FREESHIP',
            description='Free USPS shipping',
            discounttype=self.shipping_discount_type,
            discount_amount=Decimal('0'),
            order_minimum=Decimal('0'),
            combinable=True,
            start_date_time=timezone.now(),
            end_date_time=timezone.now() + timedelta(days=30)
        )

        Cartdiscount.objects.create(cart=self.cart, discountcode=discount)

        result = order_utils.get_cart_discount_codes(self.cart)

        # Discount should not be applied (wrong shipping method)
        self.assertEqual(result[discount.id]['discount_applied'], False)

    def test_first_discount_fails_minimum_second_applies(self):
        """Test that if first discount fails minimum, second one can apply"""
        # Create first discount with high minimum
        discount1 = Discountcode.objects.create(
            code='BIG200',
            description='20% off orders over $200',
            discounttype=self.item_discount_type,
            discount_amount=Decimal('20'),
            order_minimum=Decimal('200.00'),  # Will fail
            combinable=True,
            start_date_time=timezone.now(),
            end_date_time=timezone.now() + timedelta(days=30)
        )

        # Create second discount with low minimum
        discount2 = Discountcode.objects.create(
            code='SMALL10',
            description='10% off orders over $50',
            discounttype=self.item_discount_type,
            discount_amount=Decimal('10'),
            order_minimum=Decimal('50.00'),  # Will pass
            combinable=True,
            start_date_time=timezone.now(),
            end_date_time=timezone.now() + timedelta(days=30)
        )

        Cartdiscount.objects.create(cart=self.cart, discountcode=discount1)
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount2)

        result = order_utils.get_cart_discount_codes(self.cart)

        # First fails minimum, second should apply
        self.assertEqual(result[discount1.id]['discount_applied'], False)
        self.assertEqual(result[discount2.id]['discount_applied'], True)


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
        # Note: "Combinable" field removed from email formatting per new business rules
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
        # Note: "Combinable" field removed from email formatting per new business rules

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
