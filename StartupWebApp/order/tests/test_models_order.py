# Unit tests for Order app models


from django.test import TestCase
from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.db import IntegrityError

from order.models import (
    Orderconfiguration, Cart, Cartshippingaddress, Cartpayment, Skutype,
    Skuinventory, Sku, Skuprice, Product, Shippingmethod,
    Order, Status
)
from user.models import Member, Prospect, Termsofuse


class OrderconfigurationModelTest(PostgreSQLTestCase):
    """Test Orderconfiguration model"""

    def test_orderconfiguration_creation_with_float_value(self):
        """Test creating configuration with float value"""
        config = Orderconfiguration.objects.create(
            key='shipping_threshold',
            float_value=50.00
        )

        self.assertEqual(config.key, 'shipping_threshold')
        self.assertEqual(config.float_value, 50.00)
        self.assertIsNone(config.string_value)

    def test_orderconfiguration_creation_with_string_value(self):
        """Test creating configuration with string value"""
        config = Orderconfiguration.objects.create(
            key='default_carrier',
            string_value='USPS'
        )

        self.assertEqual(config.key, 'default_carrier')
        self.assertEqual(config.string_value, 'USPS')
        self.assertIsNone(config.float_value)

    def test_orderconfiguration_str_representation(self):
        """Test __str__ method"""
        config = Orderconfiguration.objects.create(
            key='test_key',
            float_value=10.5,
            string_value='test_value'
        )

        result = str(config)
        self.assertIn('test_key', result)
        self.assertIn('10.5', result)
        self.assertIn('test_value', result)

    def test_orderconfiguration_custom_table_name(self):
        """Test that model uses custom table name"""
        config = Orderconfiguration.objects.create(
            key='test',
            string_value='value'
        )

        self.assertEqual(config._meta.db_table, 'order_configuration')


class CartShippingAddressModelTest(PostgreSQLTestCase):
    """Test Cartshippingaddress model"""

    def test_cartshippingaddress_creation(self):
        """Test creating cart shipping address"""
        address = Cartshippingaddress.objects.create(
            name='John Doe',
            address_line1='123 Main St',
            city='Anytown',
            state='CA',
            zip='12345',
            country='United States',
            country_code='US'
        )

        self.assertEqual(address.name, 'John Doe')
        self.assertEqual(address.city, 'Anytown')
        self.assertEqual(address.country_code, 'US')

    def test_cartshippingaddress_str_representation(self):
        """Test __str__ method"""
        address = Cartshippingaddress.objects.create(
            name='Jane Smith',
            address_line1='456 Oak Ave',
            city='Somewhere',
            state='NY',
            zip='54321',
            country_code='US'
        )

        result = str(address)
        self.assertIn('Jane Smith', result)
        self.assertIn('456 Oak Ave', result)
        self.assertIn('Somewhere', result)
        self.assertIn('NY', result)
        self.assertIn('54321', result)

    def test_cartshippingaddress_custom_table_name(self):
        """Test that model uses custom table name"""
        address = Cartshippingaddress.objects.create(
            name='Test',
            address_line1='Test St'
        )

        self.assertEqual(address._meta.db_table, 'order_cart_shipping_address')


class CartPaymentModelTest(PostgreSQLTestCase):
    """Test Cartpayment model"""

    def test_cartpayment_creation(self):
        """Test creating cart payment"""
        payment = Cartpayment.objects.create(
            stripe_customer_token='cus_test123',
            stripe_card_id='card_test456',
            email='test@test.com'
        )

        self.assertEqual(payment.stripe_customer_token, 'cus_test123')
        self.assertEqual(payment.stripe_card_id, 'card_test456')
        self.assertEqual(payment.email, 'test@test.com')

    def test_cartpayment_str_representation(self):
        """Test __str__ method"""
        payment = Cartpayment.objects.create(
            stripe_customer_token='cus_abc',
            stripe_card_id='card_xyz',
            email='user@example.com'
        )

        result = str(payment)
        self.assertIn('user@example.com', result)
        self.assertIn('cus_abc', result)

    def test_cartpayment_custom_table_name(self):
        """Test that model uses custom table name"""
        payment = Cartpayment.objects.create(email='test@test.com')

        self.assertEqual(payment._meta.db_table, 'order_cart_payment')


class CartModelTest(PostgreSQLTestCase):
    """Test Cart model"""

    def setUp(self):
        Group.objects.create(name='Members')
        Termsofuse.objects.create(
            version='1',
            version_note='Test',
            publication_date_time=timezone.now()
        )

        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com'
        )
        self.member = Member.objects.create(user=self.user, mb_cd='MEMBER123')

    def test_cart_creation_for_member(self):
        """Test creating cart for member"""
        cart = Cart.objects.create(member=self.member)

        self.assertEqual(cart.member, self.member)
        self.assertIsNone(cart.anonymous_cart_id)

    def test_cart_creation_for_anonymous(self):
        """Test creating cart for anonymous user"""
        cart = Cart.objects.create(anonymous_cart_id='anon_12345')

        self.assertIsNone(cart.member)
        self.assertEqual(cart.anonymous_cart_id, 'anon_12345')

    def test_cart_str_representation(self):
        """Test __str__ method"""
        cart = Cart.objects.create(member=self.member)

        result = str(cart)
        self.assertIn('testuser', result)

    def test_cart_cascade_deletes_member(self):
        """Test that deleting member deletes cart"""
        cart = Cart.objects.create(member=self.member)
        cart_id = cart.id

        self.member.delete()

        self.assertFalse(Cart.objects.filter(id=cart_id).exists())

    def test_cart_custom_table_name(self):
        """Test that model uses custom table name"""
        cart = Cart.objects.create()

        self.assertEqual(cart._meta.db_table, 'order_cart')


class SkutypeModelTest(PostgreSQLTestCase):
    """Test Skutype model"""

    def test_skutype_creation(self):
        """Test creating SKU type"""
        skutype = Skutype.objects.create(title='product')

        self.assertEqual(skutype.title, 'product')

    def test_skutype_str_representation(self):
        """Test __str__ method"""
        skutype = Skutype.objects.create(title='service')

        self.assertEqual(str(skutype), 'service')

    def test_skutype_custom_table_name(self):
        """Test that model uses custom table name"""
        skutype = Skutype.objects.create(title='test')

        self.assertEqual(skutype._meta.db_table, 'order_sku_type')


class SkuinventoryModelTest(PostgreSQLTestCase):
    """Test Skuinventory model"""

    def test_skuinventory_creation(self):
        """Test creating SKU inventory"""
        inventory = Skuinventory.objects.create(
            title='In Stock',
            identifier='in-stock',
            description='Available items'
        )

        self.assertEqual(inventory.title, 'In Stock')
        self.assertEqual(inventory.identifier, 'in-stock')

    def test_skuinventory_unique_identifier(self):
        """Test that identifier is unique"""
        Skuinventory.objects.create(
            title='First',
            identifier='unique-id'
        )

        with self.assertRaises(IntegrityError):
            Skuinventory.objects.create(
                title='Second',
                identifier='unique-id'
            )

    def test_skuinventory_str_representation(self):
        """Test __str__ method"""
        inventory = Skuinventory.objects.create(
            title='Out of Stock',
            identifier='out-of-stock'
        )

        self.assertEqual(str(inventory), 'Out of Stock')

    def test_skuinventory_custom_table_name(self):
        """Test that model uses custom table name"""
        inventory = Skuinventory.objects.create(
            title='Test',
            identifier='test'
        )

        self.assertEqual(inventory._meta.db_table, 'order_sku_inventory')


class SkuModelTest(PostgreSQLTestCase):
    """Test Sku model"""

    def setUp(self):
        self.skutype = Skutype.objects.create(title='product')
        self.skuinventory = Skuinventory.objects.create(
            title='In Stock',
            identifier='in-stock'
        )

    def test_sku_creation(self):
        """Test creating SKU"""
        sku = Sku.objects.create(
            sku_type=self.skutype,
            sku_inventory=self.skuinventory,
            color='Blue',
            size='Medium',
            description='Test SKU'
        )

        self.assertEqual(sku.color, 'Blue')
        self.assertEqual(sku.size, 'Medium')
        self.assertEqual(sku.sku_type, self.skutype)

    def test_sku_str_representation(self):
        """Test __str__ method"""
        sku = Sku.objects.create(
            sku_type=self.skutype,
            sku_inventory=self.skuinventory,
            color='Red',
            size='Large'
        )

        result = str(sku)
        self.assertIn('Red', result)
        self.assertIn('Large', result)
        self.assertIn('product', result)

    def test_sku_cascade_deletes_skutype(self):
        """Test that deleting skutype deletes SKU"""
        sku = Sku.objects.create(
            sku_type=self.skutype,
            sku_inventory=self.skuinventory
        )
        sku_id = sku.id

        self.skutype.delete()

        self.assertFalse(Sku.objects.filter(id=sku_id).exists())

    def test_sku_custom_table_name(self):
        """Test that model uses custom table name"""
        sku = Sku.objects.create(
            sku_type=self.skutype,
            sku_inventory=self.skuinventory
        )

        self.assertEqual(sku._meta.db_table, 'order_sku')


class SkupriceModelTest(PostgreSQLTestCase):
    """Test Skuprice model"""

    def setUp(self):
        skutype = Skutype.objects.create(title='product')
        skuinventory = Skuinventory.objects.create(
            title='In Stock',
            identifier='in-stock'
        )
        self.sku = Sku.objects.create(
            sku_type=skutype,
            sku_inventory=skuinventory
        )

    def test_skuprice_creation(self):
        """Test creating SKU price"""
        price = Skuprice.objects.create(
            sku=self.sku,
            price=29.99,
            created_date_time=timezone.now()
        )

        self.assertEqual(price.sku, self.sku)
        self.assertEqual(price.price, 29.99)

    def test_skuprice_str_representation(self):
        """Test __str__ method"""
        price = Skuprice.objects.create(
            sku=self.sku,
            price=49.99,
            created_date_time=timezone.now()
        )

        result = str(price)
        self.assertIn('49.99', result)

    def test_skuprice_cascade_deletes_sku(self):
        """Test that deleting SKU deletes prices"""
        price = Skuprice.objects.create(
            sku=self.sku,
            price=10.00,
            created_date_time=timezone.now()
        )
        price_id = price.id

        self.sku.delete()

        self.assertFalse(Skuprice.objects.filter(id=price_id).exists())

    def test_skuprice_custom_table_name(self):
        """Test that model uses custom table name"""
        price = Skuprice.objects.create(
            sku=self.sku,
            price=10.00,
            created_date_time=timezone.now()
        )

        self.assertEqual(price._meta.db_table, 'order_sku_price')


class ProductModelTest(PostgreSQLTestCase):
    """Test Product model"""

    def test_product_creation(self):
        """Test creating product"""
        product = Product.objects.create(
            title='Test Product',
            title_url='TestProduct',
            identifier='PROD001',
            headline='Great product',
            description_part_1='Part 1',
            description_part_2='Part 2'
        )

        self.assertEqual(product.title, 'Test Product')
        self.assertEqual(product.identifier, 'PROD001')

    def test_product_unique_identifier(self):
        """Test that identifier is unique"""
        Product.objects.create(
            title='First Product',
            title_url='FirstProduct',
            identifier='UNIQUE123'
        )

        with self.assertRaises(IntegrityError):
            Product.objects.create(
                title='Second Product',
                title_url='SecondProduct',
                identifier='UNIQUE123'
            )

    def test_product_str_representation(self):
        """Test __str__ method"""
        product = Product.objects.create(
            title='My Product',
            title_url='MyProduct',
            identifier='PROD002'
        )

        self.assertEqual(str(product), 'MyProduct')

    def test_product_custom_table_name(self):
        """Test that model uses custom table name"""
        product = Product.objects.create(
            title='Test',
            title_url='Test',
            identifier='TEST'
        )

        self.assertEqual(product._meta.db_table, 'order_product')


class ShippingmethodModelTest(PostgreSQLTestCase):
    """Test Shippingmethod model"""

    def test_shippingmethod_creation(self):
        """Test creating shipping method"""
        method = Shippingmethod.objects.create(
            identifier='standard',
            carrier='USPS',
            shipping_cost=5.00,
            tracking_code_base_url='https://tools.usps.com/track',
            active=True
        )

        self.assertEqual(method.identifier, 'standard')
        self.assertEqual(method.carrier, 'USPS')
        self.assertTrue(method.active)

    def test_shippingmethod_str_representation(self):
        """Test __str__ method"""
        method = Shippingmethod.objects.create(
            identifier='express',
            carrier='FedEx',
            shipping_cost=15.00,
            tracking_code_base_url='https://www.fedex.com/track'
        )

        result = str(method)
        self.assertIn('FedEx', result)
        self.assertIn('15', result)

    def test_shippingmethod_custom_table_name(self):
        """Test that model uses custom table name"""
        method = Shippingmethod.objects.create(
            identifier='test',
            carrier='Test',
            shipping_cost=0,
            tracking_code_base_url='https://test.com'
        )

        self.assertEqual(method._meta.db_table, 'order_shipping_method')


class OrderModelTest(PostgreSQLTestCase):
    """Test Order model"""

    def setUp(self):
        Group.objects.create(name='Members')
        Termsofuse.objects.create(
            version='1',
            version_note='Test',
            publication_date_time=timezone.now()
        )

        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com'
        )
        self.member = Member.objects.create(user=self.user, mb_cd='MEMBER123')

        self.prospect = Prospect.objects.create(
            email='prospect@test.com',
            pr_cd='PROSPECT456',
            created_date_time=timezone.now()
        )

    def test_order_creation_for_member(self):
        """Test creating order for member"""
        order = Order.objects.create(
            identifier='ORDER001',
            member=self.member,
            item_subtotal=100.00,
            order_total=105.00,
            agreed_with_terms_of_sale=True,
            order_date_time=timezone.now()
        )

        self.assertEqual(order.identifier, 'ORDER001')
        self.assertEqual(order.member, self.member)
        self.assertEqual(order.item_subtotal, 100.00)

    def test_order_creation_for_prospect(self):
        """Test creating order for prospect"""
        order = Order.objects.create(
            identifier='ORDER002',
            prospect=self.prospect,
            item_subtotal=50.00,
            order_total=55.00,
            agreed_with_terms_of_sale=True,
            order_date_time=timezone.now()
        )

        self.assertEqual(order.prospect, self.prospect)
        self.assertIsNone(order.member)

    def test_order_unique_identifier(self):
        """Test that identifier is unique"""
        Order.objects.create(
            identifier='UNIQUE001',
            member=self.member,
            order_total=10.00,
            agreed_with_terms_of_sale=True,
            order_date_time=timezone.now()
        )

        with self.assertRaises(IntegrityError):
            Order.objects.create(
                identifier='UNIQUE001',
                member=self.member,
                order_total=20.00,
                agreed_with_terms_of_sale=True,
                order_date_time=timezone.now()
            )

    def test_order_str_representation(self):
        """Test __str__ method"""
        order = Order.objects.create(
            identifier='ORDER003',
            member=self.member,
            sales_tax_amt=5.00,
            order_total=105.00,
            agreed_with_terms_of_sale=True,
            order_date_time=timezone.now()
        )

        result = str(order)
        self.assertIn('5', result)
        self.assertIn('testuser', result)

    def test_order_cascade_deletes_member(self):
        """Test that deleting member deletes orders"""
        order = Order.objects.create(
            identifier='ORDER004',
            member=self.member,
            order_total=100.00,
            agreed_with_terms_of_sale=True,
            order_date_time=timezone.now()
        )
        order_id = order.id

        self.member.delete()

        self.assertFalse(Order.objects.filter(id=order_id).exists())

    def test_order_custom_table_name(self):
        """Test that model uses custom table name"""
        order = Order.objects.create(
            identifier='TEST',
            order_total=10.00,
            agreed_with_terms_of_sale=True,
            order_date_time=timezone.now()
        )

        self.assertEqual(order._meta.db_table, 'order_order')


class StatusModelTest(PostgreSQLTestCase):
    """Test Status model"""

    def test_status_creation(self):
        """Test creating status"""
        status = Status.objects.create(
            identifier='pending',
            title='Pending',
            description='Order is pending'
        )

        self.assertEqual(status.identifier, 'pending')
        self.assertEqual(status.title, 'Pending')

    def test_status_str_representation(self):
        """Test __str__ method"""
        status = Status.objects.create(
            identifier='shipped',
            title='Shipped',
            description='Order has been shipped'
        )

        result = str(status)
        self.assertIn('shipped', result)
        self.assertIn('Shipped', result)

    def test_status_custom_table_name(self):
        """Test that model uses custom table name"""
        status = Status.objects.create(
            identifier='test',
            title='Test',
            description='Test'
        )

        self.assertEqual(status._meta.db_table, 'order_status')
