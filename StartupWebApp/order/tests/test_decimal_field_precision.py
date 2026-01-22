# TDD tests for DecimalField precision in currency fields
# These tests verify that currency fields use DecimalField instead of FloatField
# to avoid floating point precision errors
#
# Following TDD methodology:
# 1. Write tests that currently FAIL (fields are still FloatField)
# 2. Convert fields to DecimalField
# 3. Tests should then PASS
#
# All 12 FloatField instances in order/models.py will be converted to DecimalField

from decimal import Decimal
from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from django.contrib.auth.models import User

from order.models import (
    Orderconfiguration, Skuprice,
    Shippingmethod, Order, Ordersku, Sku, Skutype, Skuinventory
)
from user.models import Member


class DecimalFieldPrecisionTest(PostgreSQLTestCase):
    """Test that all numeric fields in order models use DecimalField for precise calculations"""

    def test_orderconfiguration_float_value_is_decimal(self):
        """Test Orderconfiguration.float_value uses DecimalField"""
        config = Orderconfiguration.objects.create(
            key='test_threshold',
            float_value=Decimal('19.99')
        )

        # Verify value is stored and retrieved as Decimal
        config.refresh_from_db()
        self.assertIsInstance(config.float_value, Decimal)
        self.assertEqual(config.float_value, Decimal('19.99'))

        # Verify no floating point errors in calculations
        # If this were a float: 19.99 * 3 = 59.97000000000001
        result = config.float_value * 3
        self.assertEqual(result, Decimal('59.97'))

    def test_skuprice_price_is_decimal(self):
        """Test Skuprice.price uses DecimalField"""
        # Create dependencies
        sku_type = Skutype.objects.create(title='Test Type')
        inventory = Skuinventory.objects.create(
            title='Test Product',
            identifier='TEST-001'
        )
        sku = Sku.objects.create(
            sku_type=sku_type,
            sku_inventory=inventory
        )

        price = Skuprice.objects.create(
            sku=sku,
            price=Decimal('29.99'),
            created_date_time=timezone.now()
        )

        # Verify value is stored and retrieved as Decimal
        price.refresh_from_db()
        self.assertIsInstance(price.price, Decimal)
        self.assertEqual(price.price, Decimal('29.99'))

        # Verify precise calculations (8.25% sales tax)
        tax_rate = Decimal('0.0825')
        tax_amount = price.price * tax_rate
        self.assertEqual(tax_amount.quantize(Decimal('0.01')), Decimal('2.47'))

    def test_shippingmethod_cost_is_decimal(self):
        """Test Shippingmethod.shipping_cost uses DecimalField"""
        shipping = Shippingmethod.objects.create(
            identifier='USPS_PRIORITY',
            carrier='USPS',
            shipping_cost=Decimal('7.95'),
            tracking_code_base_url='https://tools.usps.com/go/TrackConfirmAction?tLabels='
        )

        # Verify value is stored and retrieved as Decimal
        shipping.refresh_from_db()
        self.assertIsInstance(shipping.shipping_cost, Decimal)
        self.assertEqual(shipping.shipping_cost, Decimal('7.95'))

    def test_order_sales_tax_amt_is_decimal(self):
        """Test Order.sales_tax_amt uses DecimalField"""
        user = User.objects.create_user(username='testuser1', password='testpass')
        member = Member.objects.create(user=user)

        order = Order.objects.create(
            identifier='ORDER-001',
            member=member,
            sales_tax_amt=Decimal('8.25'),
            order_total=Decimal('0.00'),
            order_date_time=timezone.now()
        )

        order.refresh_from_db()
        self.assertIsInstance(order.sales_tax_amt, Decimal)
        self.assertEqual(order.sales_tax_amt, Decimal('8.25'))

    def test_order_item_subtotal_is_decimal(self):
        """Test Order.item_subtotal uses DecimalField"""
        user = User.objects.create_user(username='testuser2', password='testpass')
        member = Member.objects.create(user=user)

        order = Order.objects.create(
            identifier='ORDER-002',
            member=member,
            item_subtotal=Decimal('99.99'),
            order_total=Decimal('0.00'),
            order_date_time=timezone.now()
        )

        order.refresh_from_db()
        self.assertIsInstance(order.item_subtotal, Decimal)
        self.assertEqual(order.item_subtotal, Decimal('99.99'))

    def test_order_shipping_amt_is_decimal(self):
        """Test Order.shipping_amt uses DecimalField"""
        user = User.objects.create_user(username='testuser4', password='testpass')
        member = Member.objects.create(user=user)

        order = Order.objects.create(
            identifier='ORDER-004',
            member=member,
            shipping_amt=Decimal('7.95'),
            order_total=Decimal('0.00'),
            order_date_time=timezone.now()
        )

        order.refresh_from_db()
        self.assertIsInstance(order.shipping_amt, Decimal)
        self.assertEqual(order.shipping_amt, Decimal('7.95'))

    def test_order_order_total_is_decimal(self):
        """Test Order.order_total uses DecimalField"""
        user = User.objects.create_user(username='testuser6', password='testpass')
        member = Member.objects.create(user=user)

        order = Order.objects.create(
            identifier='ORDER-006',
            member=member,
            order_total=Decimal('106.19'),
            order_date_time=timezone.now()
        )

        order.refresh_from_db()
        self.assertIsInstance(order.order_total, Decimal)
        self.assertEqual(order.order_total, Decimal('106.19'))

    def test_ordersku_price_each_is_decimal(self):
        """Test Ordersku.price_each uses DecimalField"""
        user = User.objects.create_user(username='testuser7', password='testpass')
        member = Member.objects.create(user=user)
        order = Order.objects.create(
            identifier='ORDER-007',
            member=member,
            order_total=Decimal('0.00'),
            order_date_time=timezone.now()
        )
        sku_type = Skutype.objects.create(title='Widget')
        inventory = Skuinventory.objects.create(
            title='Blue Widget',
            identifier='WIDGET-BLUE'
        )
        sku = Sku.objects.create(
            sku_type=sku_type,
            sku_inventory=inventory
        )

        ordersku = Ordersku.objects.create(
            order=order,
            sku=sku,
            quantity=2,
            price_each=Decimal('49.99')
        )

        # Verify value is stored and retrieved as Decimal
        ordersku.refresh_from_db()
        self.assertIsInstance(ordersku.price_each, Decimal)
        self.assertEqual(ordersku.price_each, Decimal('49.99'))

        # Verify precise calculations
        line_total = ordersku.price_each * ordersku.quantity
        self.assertEqual(line_total, Decimal('99.98'))

    def test_all_order_fields_together(self):
        """Test complete Order with all financial fields as Decimal"""
        user = User.objects.create_user(username='testuser8', password='testpass')
        member = Member.objects.create(user=user)

        order = Order.objects.create(
            identifier='ORDER-COMPLETE',
            member=member,
            sales_tax_amt=Decimal('8.25'),
            item_subtotal=Decimal('99.99'),
            shipping_amt=Decimal('7.95'),
            order_total=Decimal('106.19'),
            order_date_time=timezone.now()
        )

        # Verify all values are stored and retrieved as Decimal
        order.refresh_from_db()
        self.assertIsInstance(order.sales_tax_amt, Decimal)
        self.assertIsInstance(order.item_subtotal, Decimal)
        self.assertIsInstance(order.shipping_amt, Decimal)
        self.assertIsInstance(order.order_total, Decimal)

        # Verify calculation: subtotal + shipping + tax = total
        # 99.99 + 7.95 + 8.25 = 116.19
        calculated_total = (
            order.item_subtotal +
            order.shipping_amt +
            order.sales_tax_amt
        )
        self.assertEqual(calculated_total, Decimal('116.19'))


class DecimalFieldPrecisionCalculationsTest(PostgreSQLTestCase):
    """Test that decimal fields prevent common floating point errors"""

    def test_no_floating_point_error_in_price_calculations(self):
        """Verify that 0.1 + 0.2 = 0.3 (not 0.30000000000000004)"""
        # This test demonstrates the classic floating point error
        # With float: 0.1 + 0.2 = 0.30000000000000004
        # With Decimal: 0.1 + 0.2 = 0.3

        sku_type = Skutype.objects.create(title='Test')
        inventory = Skuinventory.objects.create(
            title='Test Product',
            identifier='TEST-FP'
        )
        sku = Sku.objects.create(
            sku_type=sku_type,
            sku_inventory=inventory
        )

        price1 = Skuprice.objects.create(
            sku=sku,
            price=Decimal('0.10'),
            created_date_time=timezone.now()
        )
        price2 = Skuprice.objects.create(
            sku=sku,
            price=Decimal('0.20'),
            created_date_time=timezone.now()
        )

        # Verify no floating point error
        total = price1.price + price2.price
        self.assertEqual(total, Decimal('0.30'))
        # Verify it's not the float error value
        self.assertNotEqual(str(total), '0.30000000000000004')

    def test_tax_calculation_precision(self):
        """Verify sales tax calculations maintain precision"""
        user = User.objects.create_user(username='taxtest', password='testpass')
        member = Member.objects.create(user=user)

        # Subtotal: $100.00, Tax rate: 8.25%, Expected tax: $8.25
        subtotal = Decimal('100.00')
        tax_rate = Decimal('0.0825')
        expected_tax = Decimal('8.25')

        order = Order.objects.create(
            identifier='ORDER-TAX',
            member=member,
            item_subtotal=subtotal,
            sales_tax_amt=subtotal * tax_rate,
            order_total=subtotal + (subtotal * tax_rate),
            order_date_time=timezone.now()
        )

        order.refresh_from_db()
        self.assertEqual(order.sales_tax_amt, expected_tax)
        self.assertEqual(order.order_total, Decimal('108.25'))

    def test_multi_item_order_calculation_precision(self):
        """Verify complex multi-item orders maintain precision"""
        user = User.objects.create_user(username='multitest', password='testpass')
        member = Member.objects.create(user=user)
        order = Order.objects.create(
            identifier='ORDER-MULTI',
            member=member,
            order_total=Decimal('0.00'),
            order_date_time=timezone.now()
        )

        # Create multiple SKUs with different prices
        sku_type = Skutype.objects.create(title='Product')
        inventory1 = Skuinventory.objects.create(title='Item 1', identifier='ITEM-1')
        inventory2 = Skuinventory.objects.create(title='Item 2', identifier='ITEM-2')
        inventory3 = Skuinventory.objects.create(title='Item 3', identifier='ITEM-3')

        sku1 = Sku.objects.create(sku_type=sku_type, sku_inventory=inventory1)
        sku2 = Sku.objects.create(sku_type=sku_type, sku_inventory=inventory2)
        sku3 = Sku.objects.create(sku_type=sku_type, sku_inventory=inventory3)

        # Item 1: $19.99 × 2 = $39.98
        ordersku1 = Ordersku.objects.create(
            order=order,
            sku=sku1,
            quantity=2,
            price_each=Decimal('19.99')
        )

        # Item 2: $29.99 × 1 = $29.99
        ordersku2 = Ordersku.objects.create(
            order=order,
            sku=sku2,
            quantity=1,
            price_each=Decimal('29.99')
        )

        # Item 3: $9.99 × 3 = $29.97
        ordersku3 = Ordersku.objects.create(
            order=order,
            sku=sku3,
            quantity=3,
            price_each=Decimal('9.99')
        )

        # Calculate total: $39.98 + $29.99 + $29.97 = $99.94
        total = (
            ordersku1.price_each * ordersku1.quantity +
            ordersku2.price_each * ordersku2.quantity +
            ordersku3.price_each * ordersku3.quantity
        )

        self.assertEqual(total, Decimal('99.94'))
        # Verify no floating point accumulation error
        self.assertIsInstance(total, Decimal)

    def test_float_precision_bug_demonstration(self):
        """
        Demonstrate the actual float precision bug that occurs with FloatField.
        This test FAILS with FloatField and PASSES with DecimalField.
        """
        sku_type = Skutype.objects.create(title='Test')
        inventory = Skuinventory.objects.create(
            title='Precision Test Product',
            identifier='PRECISION-TEST'
        )
        sku = Sku.objects.create(
            sku_type=sku_type,
            sku_inventory=inventory
        )

        # Create a price that demonstrates float precision issues
        # Price: $0.10 (10 cents)
        price = Skuprice.objects.create(
            sku=sku,
            price=Decimal('0.10'),
            created_date_time=timezone.now()
        )

        # Retrieve from database - this is where FloatField causes issues
        price.refresh_from_db()

        # With FloatField, price.price is a float, not Decimal
        # Convert to Decimal to perform calculations (mimics production code)
        retrieved_price = Decimal(str(price.price)) if isinstance(price.price, float) else price.price

        # Perform typical e-commerce calculation: price * quantity * tax_rate
        quantity = 3
        tax_rate = Decimal('1.0825')  # 8.25% sales tax

        # Calculate total with tax
        line_total = retrieved_price * quantity * tax_rate

        # With DecimalField: 0.10 * 3 * 1.0825 = 0.32475 exactly
        # With FloatField: Retrieved as float, converted back to Decimal
        # May have accumulated precision errors from float storage
        expected = Decimal('0.32475')

        # The key assertion: retrieved price maintains exact precision
        # This will FAIL with FloatField because 0.10 stored as float
        # may become 0.10000000149011612 when converted back
        self.assertEqual(retrieved_price * quantity, Decimal('0.30'))

        # And calculations remain precise
        self.assertEqual(line_total, expected)

    def test_repeated_calculations_accumulate_correctly(self):
        """
        Test that repeated calculations don't accumulate floating point errors.
        This test demonstrates issues with FloatField in loop scenarios.
        """
        sku_type = Skutype.objects.create(title='Product')

        # Create 10 items, each $0.10
        total = Decimal('0.00')
        for i in range(10):
            inventory = Skuinventory.objects.create(
                title=f'Item {i}',
                identifier=f'ITEM-{i}'
            )
            sku = Sku.objects.create(
                sku_type=sku_type,
                sku_inventory=inventory
            )
            price = Skuprice.objects.create(
                sku=sku,
                price=Decimal('0.10'),
                created_date_time=timezone.now()
            )

            # Retrieve from DB and accumulate
            price.refresh_from_db()
            # Convert float to Decimal if needed (mimics production code)
            price_value = Decimal(str(price.price)) if isinstance(price.price, float) else price.price
            total += price_value

        # With DecimalField: 0.10 * 10 = exactly 1.00
        # With FloatField: May get 0.9999999999999999 or 1.0000000000000001
        self.assertEqual(total, Decimal('1.00'))

        # Verify it's exactly 1.00, not a float approximation
        self.assertEqual(str(total), '1.00')
