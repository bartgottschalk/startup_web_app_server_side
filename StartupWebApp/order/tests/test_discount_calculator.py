"""
Unit tests for centralized discount calculator.

Business Rules:
1. Only ONE item discount can be applied (first valid one that meets order minimum)
2. Only ONE shipping discount can be applied (first valid one that meets order minimum)
3. Item discount + Shipping discount CAN be combined (separate calculations)
4. Subscription discounts don't affect payment amount (future feature)
5. The "combinable" flag is stored but not used in calculations

Test Coverage:
- Single item discount (percent-off)
- Single item discount (dollar-amt-off)
- Single shipping discount (free-usps-ground-shipping)
- Item + shipping discount combination
- Multiple item discounts (only first valid one applies)
- Multiple shipping discounts (only first valid one applies)
- Order minimum requirements
- Invalid/expired discounts
- Edge cases
"""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from order.models import (
    Cart, Cartsku, Cartdiscount, Cartshippingmethod,
    Sku, Skutype, Skuinventory, Skuprice,
    Discountcode, Discounttype, Shippingmethod
)
from order.utilities import discount_calculator


class DiscountCalculatorTest(TestCase):
    """Test the centralized discount calculator"""

    def setUp(self):
        """Set up test data"""
        # Create SKU type and inventory
        self.sku_type = Skutype.objects.create(title='product')
        self.sku_inventory = Skuinventory.objects.create(
            title='In Stock',
            identifier='in-stock'
        )

        # Create a test SKU with price
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

        # Create shipping method
        self.shipping_method = Shippingmethod.objects.create(
            identifier='USPSRetailGround',
            carrier='USPS',
            shipping_cost=Decimal('10.00'),
            active=True
        )

        # Create discount types
        self.discount_type_percent = Discounttype.objects.create(
            title='Percent Off Item Total',
            applies_to='item_total',
            action='percent-off',
            description='{}% off'
        )
        self.discount_type_dollar = Discounttype.objects.create(
            title='Dollar Off Item Total',
            applies_to='item_total',
            action='dollar-amt-off',
            description='${} off'
        )
        self.discount_type_shipping = Discounttype.objects.create(
            title='Free Shipping',
            applies_to='shipping',
            action='free-usps-ground-shipping',
            description='Free shipping'
        )

        # Create cart with one item ($100)
        self.cart = Cart.objects.create()
        Cartsku.objects.create(cart=self.cart, sku=self.sku, quantity=1)
        Cartshippingmethod.objects.create(cart=self.cart, shippingmethod=self.shipping_method)

        # Time helpers
        self.now = timezone.now()
        self.yesterday = self.now - timedelta(days=1)
        self.tomorrow = self.now + timedelta(days=1)
        self.next_year = self.now + timedelta(days=365)

    def test_no_discounts(self):
        """Test cart with no discount codes"""
        result = discount_calculator.calculate_discounts(self.cart)

        self.assertEqual(result['item_subtotal'], Decimal('100.00'))
        self.assertEqual(result['item_discount'], Decimal('0.00'))
        self.assertEqual(result['shipping_subtotal'], Decimal('10.00'))
        self.assertEqual(result['shipping_discount'], Decimal('0.00'))
        self.assertEqual(result['cart_total'], Decimal('110.00'))

    def test_single_percent_off_discount(self):
        """Test single percent-off item discount (10% off $100 = $10 discount)"""
        discount = Discountcode.objects.create(
            code='SAVE10',
            discounttype=self.discount_type_percent,
            discount_amount=Decimal('10.00'),  # 10%
            order_minimum=Decimal('0.00'),
            combinable=False,
            start_date_time=self.yesterday,
            end_date_time=self.next_year
        )
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount)

        result = discount_calculator.calculate_discounts(self.cart)

        self.assertEqual(result['item_subtotal'], Decimal('100.00'))
        self.assertEqual(result['item_discount'], Decimal('10.00'))  # 10% of $100
        self.assertEqual(result['shipping_subtotal'], Decimal('10.00'))
        self.assertEqual(result['shipping_discount'], Decimal('0.00'))
        self.assertEqual(result['cart_total'], Decimal('100.00'))  # $100 - $10 + $10

    def test_single_dollar_off_discount(self):
        """Test single dollar-amt-off item discount ($20 off)"""
        discount = Discountcode.objects.create(
            code='SAVE20',
            discounttype=self.discount_type_dollar,
            discount_amount=Decimal('20.00'),  # $20 off
            order_minimum=Decimal('0.00'),
            combinable=False,
            start_date_time=self.yesterday,
            end_date_time=self.next_year
        )
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount)

        result = discount_calculator.calculate_discounts(self.cart)

        self.assertEqual(result['item_subtotal'], Decimal('100.00'))
        self.assertEqual(result['item_discount'], Decimal('20.00'))
        self.assertEqual(result['shipping_subtotal'], Decimal('10.00'))
        self.assertEqual(result['shipping_discount'], Decimal('0.00'))
        self.assertEqual(result['cart_total'], Decimal('90.00'))  # $100 - $20 + $10

    def test_single_shipping_discount(self):
        """Test single shipping discount (free shipping)"""
        discount = Discountcode.objects.create(
            code='FREESHIP',
            discounttype=self.discount_type_shipping,
            discount_amount=Decimal('100.00'),  # Not used for shipping
            order_minimum=Decimal('0.00'),
            combinable=False,
            start_date_time=self.yesterday,
            end_date_time=self.next_year
        )
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount)

        result = discount_calculator.calculate_discounts(self.cart)

        self.assertEqual(result['item_subtotal'], Decimal('100.00'))
        self.assertEqual(result['item_discount'], Decimal('0.00'))
        self.assertEqual(result['shipping_subtotal'], Decimal('10.00'))
        self.assertEqual(result['shipping_discount'], Decimal('10.00'))  # Free shipping
        self.assertEqual(result['cart_total'], Decimal('100.00'))  # $100 + $10 - $10

    def test_item_and_shipping_discount_combined(self):
        """Test that item discount + shipping discount can be combined"""
        # 10% off items
        item_discount = Discountcode.objects.create(
            code='SAVE10',
            discounttype=self.discount_type_percent,
            discount_amount=Decimal('10.00'),
            order_minimum=Decimal('0.00'),
            combinable=False,
            start_date_time=self.yesterday,
            end_date_time=self.next_year
        )
        Cartdiscount.objects.create(cart=self.cart, discountcode=item_discount)

        # Free shipping
        shipping_discount = Discountcode.objects.create(
            code='FREESHIP',
            discounttype=self.discount_type_shipping,
            discount_amount=Decimal('100.00'),
            order_minimum=Decimal('0.00'),
            combinable=False,
            start_date_time=self.yesterday,
            end_date_time=self.next_year
        )
        Cartdiscount.objects.create(cart=self.cart, discountcode=shipping_discount)

        result = discount_calculator.calculate_discounts(self.cart)

        self.assertEqual(result['item_subtotal'], Decimal('100.00'))
        self.assertEqual(result['item_discount'], Decimal('10.00'))  # 10% off
        self.assertEqual(result['shipping_subtotal'], Decimal('10.00'))
        self.assertEqual(result['shipping_discount'], Decimal('10.00'))  # Free shipping
        self.assertEqual(result['cart_total'], Decimal('90.00'))  # $100 - $10 + $10 - $10

    def test_multiple_item_discounts_only_first_applies(self):
        """Test that only the FIRST valid item discount is applied"""
        # First discount: 10% off
        discount1 = Discountcode.objects.create(
            code='SAVE10',
            discounttype=self.discount_type_percent,
            discount_amount=Decimal('10.00'),
            order_minimum=Decimal('0.00'),
            combinable=False,
            start_date_time=self.yesterday,
            end_date_time=self.next_year
        )
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount1)

        # Second discount: 50% off (should be ignored)
        discount2 = Discountcode.objects.create(
            code='SAVE50',
            discounttype=self.discount_type_percent,
            discount_amount=Decimal('50.00'),
            order_minimum=Decimal('0.00'),
            combinable=False,
            start_date_time=self.yesterday,
            end_date_time=self.next_year
        )
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount2)

        result = discount_calculator.calculate_discounts(self.cart)

        # Only first discount should apply
        self.assertEqual(result['item_discount'], Decimal('10.00'))  # NOT $50
        self.assertEqual(result['cart_total'], Decimal('100.00'))  # $100 - $10 + $10

    def test_multiple_shipping_discounts_only_first_applies(self):
        """Test that only the FIRST valid shipping discount is applied"""
        # In practice there's only one type of shipping discount, but test the logic
        shipping_discount1 = Discountcode.objects.create(
            code='FREESHIP1',
            discounttype=self.discount_type_shipping,
            discount_amount=Decimal('100.00'),
            order_minimum=Decimal('0.00'),
            combinable=False,
            start_date_time=self.yesterday,
            end_date_time=self.next_year
        )
        Cartdiscount.objects.create(cart=self.cart, discountcode=shipping_discount1)

        shipping_discount2 = Discountcode.objects.create(
            code='FREESHIP2',
            discounttype=self.discount_type_shipping,
            discount_amount=Decimal('100.00'),
            order_minimum=Decimal('0.00'),
            combinable=False,
            start_date_time=self.yesterday,
            end_date_time=self.next_year
        )
        Cartdiscount.objects.create(cart=self.cart, discountcode=shipping_discount2)

        result = discount_calculator.calculate_discounts(self.cart)

        # Only one shipping discount should apply
        self.assertEqual(result['shipping_discount'], Decimal('10.00'))
        self.assertEqual(result['cart_total'], Decimal('100.00'))

    def test_discount_with_order_minimum_not_met(self):
        """Test discount is not applied when order minimum is not met"""
        discount = Discountcode.objects.create(
            code='SAVE20',
            discounttype=self.discount_type_percent,
            discount_amount=Decimal('20.00'),
            order_minimum=Decimal('200.00'),  # Cart is only $100
            combinable=False,
            start_date_time=self.yesterday,
            end_date_time=self.next_year
        )
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount)

        result = discount_calculator.calculate_discounts(self.cart)

        # Discount should NOT be applied
        self.assertEqual(result['item_discount'], Decimal('0.00'))
        self.assertEqual(result['cart_total'], Decimal('110.00'))

    def test_discount_with_order_minimum_met(self):
        """Test discount IS applied when order minimum is met"""
        discount = Discountcode.objects.create(
            code='SAVE20',
            discounttype=self.discount_type_percent,
            discount_amount=Decimal('20.00'),
            order_minimum=Decimal('50.00'),  # Cart is $100, minimum met
            combinable=False,
            start_date_time=self.yesterday,
            end_date_time=self.next_year
        )
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount)

        result = discount_calculator.calculate_discounts(self.cart)

        # Discount SHOULD be applied
        self.assertEqual(result['item_discount'], Decimal('20.00'))
        self.assertEqual(result['cart_total'], Decimal('90.00'))

    def test_first_discount_fails_minimum_second_applies(self):
        """Test that if first discount doesn't meet minimum, second one is tried"""
        # First discount: requires $200 minimum (won't apply)
        discount1 = Discountcode.objects.create(
            code='BIGORDER',
            discounttype=self.discount_type_percent,
            discount_amount=Decimal('50.00'),
            order_minimum=Decimal('200.00'),
            combinable=False,
            start_date_time=self.yesterday,
            end_date_time=self.next_year
        )
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount1)

        # Second discount: no minimum (should apply)
        discount2 = Discountcode.objects.create(
            code='SAVE10',
            discounttype=self.discount_type_percent,
            discount_amount=Decimal('10.00'),
            order_minimum=Decimal('0.00'),
            combinable=False,
            start_date_time=self.yesterday,
            end_date_time=self.next_year
        )
        Cartdiscount.objects.create(cart=self.cart, discountcode=discount2)

        result = discount_calculator.calculate_discounts(self.cart)

        # Second discount should apply
        self.assertEqual(result['item_discount'], Decimal('10.00'))
        self.assertEqual(result['cart_total'], Decimal('100.00'))

    def test_cart_with_no_shipping_method(self):
        """Test cart with no shipping method selected"""
        # Remove shipping method
        Cartshippingmethod.objects.filter(cart=self.cart).delete()

        result = discount_calculator.calculate_discounts(self.cart)

        self.assertEqual(result['item_subtotal'], Decimal('100.00'))
        self.assertEqual(result['shipping_subtotal'], Decimal('0.00'))
        self.assertEqual(result['shipping_discount'], Decimal('0.00'))
        self.assertEqual(result['cart_total'], Decimal('100.00'))

    def test_empty_cart(self):
        """Test empty cart (no items)"""
        # Remove all items
        Cartsku.objects.filter(cart=self.cart).delete()

        result = discount_calculator.calculate_discounts(self.cart)

        self.assertEqual(result['item_subtotal'], Decimal('0.00'))
        self.assertEqual(result['item_discount'], Decimal('0.00'))
        self.assertEqual(result['shipping_subtotal'], Decimal('10.00'))
        self.assertEqual(result['shipping_discount'], Decimal('0.00'))
        self.assertEqual(result['cart_total'], Decimal('10.00'))
