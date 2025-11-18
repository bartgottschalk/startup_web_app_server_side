# Model constraint tests for Order app - Django migration readiness

from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from django.db import IntegrityError

from order.models import (
    Orderconfiguration, Cart, Cartshippingaddress, Cartpayment, Skutype,
    Skuinventory, Sku, Skuprice, Skuimage, Product,
    Productimage, Productvideo, Discounttype, Discountcode,
    Shippingmethod, Ordershippingmethod, Orderpayment, Ordershippingaddress,
    Orderbillingaddress, Order, Ordersku,
    Status, Orderstatus
)


class OrderconfigurationConstraintsTest(PostgreSQLTestCase):
    """Test Orderconfiguration model constraints"""

    def test_orderconfiguration_key_max_length(self):
        """Test that key has 100 char limit"""
        long_key = 'k' * 100
        config = Orderconfiguration.objects.create(
            key=long_key,
            string_value='test'
        )
        self.assertEqual(len(config.key), 100)

    def test_orderconfiguration_string_value_max_length(self):
        """Test that string_value has 500 char limit"""
        long_value = 'v' * 500
        config = Orderconfiguration.objects.create(
            key='test',
            string_value=long_value
        )
        self.assertEqual(len(config.string_value), 500)

    def test_orderconfiguration_allows_null_values(self):
        """Test that float_value and string_value can be NULL"""
        config = Orderconfiguration.objects.create(key='test')
        self.assertIsNone(config.float_value)
        self.assertIsNone(config.string_value)


class CartshippingaddressConstraintsTest(PostgreSQLTestCase):
    """Test Cartshippingaddress model constraints"""

    def test_cartshippingaddress_name_max_length(self):
        """Test that name has 200 char limit"""
        long_name = 'N' * 200
        address = Cartshippingaddress.objects.create(name=long_name)
        self.assertEqual(len(address.name), 200)

    def test_cartshippingaddress_address_line1_max_length(self):
        """Test that address_line1 has 200 char limit"""
        long_address = 'A' * 200
        address = Cartshippingaddress.objects.create(address_line1=long_address)
        self.assertEqual(len(address.address_line1), 200)

    def test_cartshippingaddress_city_max_length(self):
        """Test that city has 200 char limit"""
        long_city = 'C' * 200
        address = Cartshippingaddress.objects.create(city=long_city)
        self.assertEqual(len(address.city), 200)

    def test_cartshippingaddress_state_max_length(self):
        """Test that state has 40 char limit"""
        long_state = 'S' * 40
        address = Cartshippingaddress.objects.create(state=long_state)
        self.assertEqual(len(address.state), 40)

    def test_cartshippingaddress_zip_max_length(self):
        """Test that zip has 10 char limit"""
        long_zip = '1' * 10
        address = Cartshippingaddress.objects.create(zip=long_zip)
        self.assertEqual(len(address.zip), 10)

    def test_cartshippingaddress_country_max_length(self):
        """Test that country has 200 char limit"""
        long_country = 'C' * 200
        address = Cartshippingaddress.objects.create(country=long_country)
        self.assertEqual(len(address.country), 200)

    def test_cartshippingaddress_country_code_max_length(self):
        """Test that country_code has 10 char limit"""
        long_code = 'US' * 5  # 10 chars
        address = Cartshippingaddress.objects.create(country_code=long_code)
        self.assertEqual(len(address.country_code), 10)

    def test_cartshippingaddress_allows_null_fields(self):
        """Test that all fields can be NULL"""
        address = Cartshippingaddress.objects.create()
        self.assertIsNone(address.name)
        self.assertIsNone(address.address_line1)
        self.assertIsNone(address.city)
        self.assertIsNone(address.state)
        self.assertIsNone(address.zip)


class CartpaymentConstraintsTest(PostgreSQLTestCase):
    """Test Cartpayment model constraints"""

    def test_cartpayment_stripe_customer_token_max_length(self):
        """Test that stripe_customer_token has 100 char limit"""
        long_token = 'cus_' + 't' * 96  # Total 100 chars
        payment = Cartpayment.objects.create(stripe_customer_token=long_token)
        self.assertEqual(len(payment.stripe_customer_token), 100)

    def test_cartpayment_stripe_card_id_max_length(self):
        """Test that stripe_card_id has 100 char limit"""
        long_card = 'card_' + 'c' * 95  # Total 100 chars
        payment = Cartpayment.objects.create(stripe_card_id=long_card)
        self.assertEqual(len(payment.stripe_card_id), 100)

    def test_cartpayment_email_max_length(self):
        """Test that email has 254 char limit"""
        long_email = 'a' * 240 + '@example.com'  # Total 252 chars
        payment = Cartpayment.objects.create(email=long_email)
        self.assertLessEqual(len(payment.email), 254)

    def test_cartpayment_allows_null_fields(self):
        """Test that all fields can be NULL"""
        payment = Cartpayment.objects.create()
        self.assertIsNone(payment.stripe_customer_token)
        self.assertIsNone(payment.stripe_card_id)
        self.assertIsNone(payment.email)


class CartConstraintsTest(PostgreSQLTestCase):
    """Test Cart model constraints"""

    def test_cart_anonymous_cart_id_max_length(self):
        """Test that anonymous_cart_id has 100 char limit"""
        long_id = 'a' * 100
        cart = Cart.objects.create(anonymous_cart_id=long_id)
        self.assertEqual(len(cart.anonymous_cart_id), 100)

    def test_cart_allows_null_member(self):
        """Test that member can be NULL"""
        cart = Cart.objects.create()
        self.assertIsNone(cart.member)

    def test_cart_allows_null_anonymous_cart_id(self):
        """Test that anonymous_cart_id can be NULL"""
        cart = Cart.objects.create()
        self.assertIsNone(cart.anonymous_cart_id)


class SkutypeConstraintsTest(PostgreSQLTestCase):
    """Test Skutype model constraints"""

    def test_skutype_title_max_length(self):
        """Test that title has 100 char limit"""
        long_title = 't' * 100
        skutype = Skutype.objects.create(title=long_title)
        self.assertEqual(len(skutype.title), 100)


class SkuinventoryConstraintsTest(PostgreSQLTestCase):
    """Test Skuinventory model constraints"""

    def test_skuinventory_title_max_length(self):
        """Test that title has 100 char limit"""
        long_title = 't' * 100
        inventory = Skuinventory.objects.create(
            title=long_title,
            identifier='test'
        )
        self.assertEqual(len(inventory.title), 100)

    def test_skuinventory_identifier_max_length(self):
        """Test that identifier has 100 char limit"""
        long_id = 'i' * 100
        inventory = Skuinventory.objects.create(
            title='test',
            identifier=long_id
        )
        self.assertEqual(len(inventory.identifier), 100)

    def test_skuinventory_identifier_is_unique(self):
        """Test that identifier must be unique"""
        Skuinventory.objects.create(
            title='First',
            identifier='unique-id'
        )
        with self.assertRaises(IntegrityError):
            Skuinventory.objects.create(
                title='Second',
                identifier='unique-id'
            )

    def test_skuinventory_description_max_length(self):
        """Test that description has 500 char limit"""
        long_desc = 'd' * 500
        inventory = Skuinventory.objects.create(
            title='test',
            identifier='test',
            description=long_desc
        )
        self.assertEqual(len(inventory.description), 500)


class SkuConstraintsTest(PostgreSQLTestCase):
    """Test Sku model constraints"""

    def setUp(self):
        self.skutype = Skutype.objects.create(title='product')
        self.skuinventory = Skuinventory.objects.create(
            title='In Stock',
            identifier='in-stock'
        )

    def test_sku_color_max_length(self):
        """Test that color has 500 char limit"""
        long_color = 'c' * 500
        sku = Sku.objects.create(
            sku_type=self.skutype,
            sku_inventory=self.skuinventory,
            color=long_color
        )
        self.assertEqual(len(sku.color), 500)

    def test_sku_size_max_length(self):
        """Test that size has 500 char limit"""
        long_size = 's' * 500
        sku = Sku.objects.create(
            sku_type=self.skutype,
            sku_inventory=self.skuinventory,
            size=long_size
        )
        self.assertEqual(len(sku.size), 500)

    def test_sku_description_max_length(self):
        """Test that description has 1000 char limit"""
        long_desc = 'd' * 1000
        sku = Sku.objects.create(
            sku_type=self.skutype,
            sku_inventory=self.skuinventory,
            description=long_desc
        )
        self.assertEqual(len(sku.description), 1000)

    def test_sku_allows_null_optional_fields(self):
        """Test that optional fields can be NULL"""
        sku = Sku.objects.create(
            sku_type=self.skutype,
            sku_inventory=self.skuinventory
        )
        self.assertIsNone(sku.color)
        self.assertIsNone(sku.size)
        self.assertIsNone(sku.description)


class SkupriceConstraintsTest(PostgreSQLTestCase):
    """Test Skuprice model constraints"""

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

    def test_skuprice_price_default_value(self):
        """Test that price defaults to 0"""
        price = Skuprice.objects.create(
            sku=self.sku,
            created_date_time=timezone.now()
        )
        self.assertEqual(price.price, 0)

    def test_skuprice_created_date_time_is_required(self):
        """Test that created_date_time is required"""
        with self.assertRaises((IntegrityError, ValueError)):
            Skuprice.objects.create(sku=self.sku)


class SkuimageConstraintsTest(PostgreSQLTestCase):
    """Test Skuimage model constraints"""

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

    def test_skuimage_image_url_max_length(self):
        """Test that image_url has 500 char limit"""
        long_url = 'https://' + 'x' * 492  # Total 500 chars
        image = Skuimage.objects.create(
            sku=self.sku,
            image_url=long_url
        )
        self.assertEqual(len(image.image_url), 500)

    def test_skuimage_main_image_default_false(self):
        """Test that main_image defaults to False"""
        image = Skuimage.objects.create(
            sku=self.sku,
            image_url='https://example.com/image.jpg'
        )
        self.assertFalse(image.main_image)

    def test_skuimage_caption_max_length(self):
        """Test that caption has 500 char limit"""
        long_caption = 'c' * 500
        image = Skuimage.objects.create(
            sku=self.sku,
            image_url='https://example.com/image.jpg',
            caption=long_caption
        )
        self.assertEqual(len(image.caption), 500)


class ProductConstraintsTest(PostgreSQLTestCase):
    """Test Product model constraints"""

    def test_product_title_max_length(self):
        """Test that title has 200 char limit"""
        long_title = 't' * 200
        product = Product.objects.create(
            title=long_title,
            title_url='test',
            identifier='TEST001'
        )
        self.assertEqual(len(product.title), 200)

    def test_product_title_url_max_length(self):
        """Test that title_url has 100 char limit"""
        long_url = 't' * 100
        product = Product.objects.create(
            title='test',
            title_url=long_url,
            identifier='TEST002'
        )
        self.assertEqual(len(product.title_url), 100)

    def test_product_identifier_max_length(self):
        """Test that identifier has 100 char limit"""
        long_id = 'P' * 100
        product = Product.objects.create(
            title='test',
            title_url='test',
            identifier=long_id
        )
        self.assertEqual(len(product.identifier), 100)

    def test_product_identifier_is_unique(self):
        """Test that identifier must be unique"""
        Product.objects.create(
            title='First',
            title_url='First',
            identifier='UNIQUE001'
        )
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                title='Second',
                title_url='Second',
                identifier='UNIQUE001'
            )

    def test_product_headline_max_length(self):
        """Test that headline has 5000 char limit"""
        long_headline = 'h' * 5000
        product = Product.objects.create(
            title='test',
            title_url='test',
            identifier='TEST003',
            headline=long_headline
        )
        self.assertEqual(len(product.headline), 5000)

    def test_product_description_part_1_max_length(self):
        """Test that description_part_1 has 5000 char limit"""
        long_desc = 'd' * 5000
        product = Product.objects.create(
            title='test',
            title_url='test',
            identifier='TEST004',
            description_part_1=long_desc
        )
        self.assertEqual(len(product.description_part_1), 5000)

    def test_product_description_part_2_max_length(self):
        """Test that description_part_2 has 5000 char limit"""
        long_desc = 'd' * 5000
        product = Product.objects.create(
            title='test',
            title_url='test',
            identifier='TEST005',
            description_part_2=long_desc
        )
        self.assertEqual(len(product.description_part_2), 5000)


class ProductimageConstraintsTest(PostgreSQLTestCase):
    """Test Productimage model constraints"""

    def setUp(self):
        self.product = Product.objects.create(
            title='Test Product',
            title_url='TestProduct',
            identifier='PROD001'
        )

    def test_productimage_image_url_max_length(self):
        """Test that image_url has 500 char limit"""
        long_url = 'https://' + 'x' * 492  # Total 500 chars
        image = Productimage.objects.create(
            product=self.product,
            image_url=long_url
        )
        self.assertEqual(len(image.image_url), 500)

    def test_productimage_main_image_default_false(self):
        """Test that main_image defaults to False"""
        image = Productimage.objects.create(
            product=self.product,
            image_url='https://example.com/image.jpg'
        )
        self.assertFalse(image.main_image)

    def test_productimage_caption_max_length(self):
        """Test that caption has 500 char limit"""
        long_caption = 'c' * 500
        image = Productimage.objects.create(
            product=self.product,
            image_url='https://example.com/image.jpg',
            caption=long_caption
        )
        self.assertEqual(len(image.caption), 500)


class ProductvideoConstraintsTest(PostgreSQLTestCase):
    """Test Productvideo model constraints"""

    def setUp(self):
        self.product = Product.objects.create(
            title='Test Product',
            title_url='TestProduct',
            identifier='PROD001'
        )

    def test_productvideo_video_url_max_length(self):
        """Test that video_url has 500 char limit"""
        long_url = 'https://' + 'x' * 492  # Total 500 chars
        video = Productvideo.objects.create(
            product=self.product,
            video_url=long_url,
            video_thumbnail_url='https://example.com/thumb.jpg'
        )
        self.assertEqual(len(video.video_url), 500)

    def test_productvideo_video_thumbnail_url_max_length(self):
        """Test that video_thumbnail_url has 500 char limit"""
        long_url = 'https://' + 'x' * 492  # Total 500 chars
        video = Productvideo.objects.create(
            product=self.product,
            video_url='https://example.com/video.mp4',
            video_thumbnail_url=long_url
        )
        self.assertEqual(len(video.video_thumbnail_url), 500)

    def test_productvideo_caption_max_length(self):
        """Test that caption has 500 char limit"""
        long_caption = 'c' * 500
        video = Productvideo.objects.create(
            product=self.product,
            video_url='https://example.com/video.mp4',
            video_thumbnail_url='https://example.com/thumb.jpg',
            caption=long_caption
        )
        self.assertEqual(len(video.caption), 500)


class DiscounttypeConstraintsTest(PostgreSQLTestCase):
    """Test Discounttype model constraints"""

    def test_discounttype_title_max_length(self):
        """Test that title has 100 char limit"""
        long_title = 't' * 100
        dtype = Discounttype.objects.create(
            title=long_title,
            description='test',
            applies_to='order',
            action='percentage_off'
        )
        self.assertEqual(len(dtype.title), 100)

    def test_discounttype_description_max_length(self):
        """Test that description has 500 char limit"""
        long_desc = 'd' * 500
        dtype = Discounttype.objects.create(
            title='test',
            description=long_desc,
            applies_to='order',
            action='percentage_off'
        )
        self.assertEqual(len(dtype.description), 500)

    def test_discounttype_applies_to_max_length(self):
        """Test that applies_to has 100 char limit"""
        long_applies = 'a' * 100
        dtype = Discounttype.objects.create(
            title='test',
            description='test',
            applies_to=long_applies,
            action='percentage_off'
        )
        self.assertEqual(len(dtype.applies_to), 100)

    def test_discounttype_action_max_length(self):
        """Test that action has 100 char limit"""
        long_action = 'a' * 100
        dtype = Discounttype.objects.create(
            title='test',
            description='test',
            applies_to='order',
            action=long_action
        )
        self.assertEqual(len(dtype.action), 100)


class DiscountcodeConstraintsTest(PostgreSQLTestCase):
    """Test Discountcode model constraints"""

    def setUp(self):
        self.discounttype = Discounttype.objects.create(
            title='Percentage Off',
            description='test',
            applies_to='order',
            action='percentage_off'
        )

    def test_discountcode_code_max_length(self):
        """Test that code has 100 char limit"""
        long_code = 'C' * 100
        now = timezone.now()
        discount = Discountcode.objects.create(
            code=long_code,
            description='test',
            start_date_time=now,
            end_date_time=now + timezone.timedelta(days=30),
            discounttype=self.discounttype
        )
        self.assertEqual(len(discount.code), 100)

    def test_discountcode_description_max_length(self):
        """Test that description has 500 char limit"""
        long_desc = 'd' * 500
        now = timezone.now()
        discount = Discountcode.objects.create(
            code='TEST',
            description=long_desc,
            start_date_time=now,
            end_date_time=now + timezone.timedelta(days=30),
            discounttype=self.discounttype
        )
        self.assertEqual(len(discount.description), 500)

    def test_discountcode_combinable_default_false(self):
        """Test that combinable defaults to False"""
        now = timezone.now()
        discount = Discountcode.objects.create(
            code='TEST',
            description='test',
            start_date_time=now,
            end_date_time=now + timezone.timedelta(days=30),
            discounttype=self.discounttype
        )
        self.assertFalse(discount.combinable)

    def test_discountcode_discount_amount_default_zero(self):
        """Test that discount_amount defaults to 0"""
        now = timezone.now()
        discount = Discountcode.objects.create(
            code='TEST',
            description='test',
            start_date_time=now,
            end_date_time=now + timezone.timedelta(days=30),
            discounttype=self.discounttype
        )
        self.assertEqual(discount.discount_amount, 0)

    def test_discountcode_order_minimum_default_zero(self):
        """Test that order_minimum defaults to 0"""
        now = timezone.now()
        discount = Discountcode.objects.create(
            code='TEST',
            description='test',
            start_date_time=now,
            end_date_time=now + timezone.timedelta(days=30),
            discounttype=self.discounttype
        )
        self.assertEqual(discount.order_minimum, 0)


class ShippingmethodConstraintsTest(PostgreSQLTestCase):
    """Test Shippingmethod model constraints"""

    def test_shippingmethod_identifier_max_length(self):
        """Test that identifier has 100 char limit"""
        long_id = 'i' * 100
        method = Shippingmethod.objects.create(
            identifier=long_id,
            carrier='test',
            shipping_cost=5.00,
            tracking_code_base_url='https://test.com'
        )
        self.assertEqual(len(method.identifier), 100)

    def test_shippingmethod_carrier_max_length(self):
        """Test that carrier has 100 char limit"""
        long_carrier = 'c' * 100
        method = Shippingmethod.objects.create(
            identifier='test',
            carrier=long_carrier,
            shipping_cost=5.00,
            tracking_code_base_url='https://test.com'
        )
        self.assertEqual(len(method.carrier), 100)

    def test_shippingmethod_tracking_code_base_url_max_length(self):
        """Test that tracking_code_base_url has 200 char limit"""
        long_url = 'https://' + 'x' * 192  # Total 200 chars
        method = Shippingmethod.objects.create(
            identifier='test',
            carrier='test',
            shipping_cost=5.00,
            tracking_code_base_url=long_url
        )
        self.assertEqual(len(method.tracking_code_base_url), 200)

    def test_shippingmethod_active_default_true(self):
        """Test that active defaults to True"""
        method = Shippingmethod.objects.create(
            identifier='test',
            carrier='test',
            shipping_cost=5.00,
            tracking_code_base_url='https://test.com'
        )
        self.assertTrue(method.active)


class OrderpaymentConstraintsTest(PostgreSQLTestCase):
    """Test Orderpayment model constraints"""

    def test_orderpayment_email_max_length(self):
        """Test that email has 254 char limit"""
        long_email = 'a' * 240 + '@example.com'  # Total 252 chars
        payment = Orderpayment.objects.create(email=long_email)
        self.assertLessEqual(len(payment.email), 254)

    def test_orderpayment_payment_type_max_length(self):
        """Test that payment_type has 20 char limit"""
        long_type = 'c' * 20
        payment = Orderpayment.objects.create(payment_type=long_type)
        self.assertEqual(len(payment.payment_type), 20)

    def test_orderpayment_card_name_max_length(self):
        """Test that card_name has 200 char limit"""
        long_name = 'N' * 200
        payment = Orderpayment.objects.create(card_name=long_name)
        self.assertEqual(len(payment.card_name), 200)

    def test_orderpayment_card_brand_max_length(self):
        """Test that card_brand has 20 char limit"""
        long_brand = 'V' * 20
        payment = Orderpayment.objects.create(card_brand=long_brand)
        self.assertEqual(len(payment.card_brand), 20)

    def test_orderpayment_card_last4_max_length(self):
        """Test that card_last4 has 4 char limit"""
        payment = Orderpayment.objects.create(card_last4='1234')
        self.assertEqual(len(payment.card_last4), 4)

    def test_orderpayment_card_exp_month_max_length(self):
        """Test that card_exp_month has 2 char limit"""
        payment = Orderpayment.objects.create(card_exp_month='12')
        self.assertEqual(len(payment.card_exp_month), 2)

    def test_orderpayment_card_exp_year_max_length(self):
        """Test that card_exp_year has 4 char limit"""
        payment = Orderpayment.objects.create(card_exp_year='2025')
        self.assertEqual(len(payment.card_exp_year), 4)

    def test_orderpayment_card_zip_max_length(self):
        """Test that card_zip has 10 char limit"""
        long_zip = '1' * 10
        payment = Orderpayment.objects.create(card_zip=long_zip)
        self.assertEqual(len(payment.card_zip), 10)


class OrdershippingaddressConstraintsTest(PostgreSQLTestCase):
    """Test Ordershippingaddress model constraints"""

    def test_ordershippingaddress_name_max_length(self):
        """Test that name has 200 char limit"""
        long_name = 'N' * 200
        address = Ordershippingaddress.objects.create(name=long_name)
        self.assertEqual(len(address.name), 200)

    def test_ordershippingaddress_address_line1_max_length(self):
        """Test that address_line1 has 200 char limit"""
        long_address = 'A' * 200
        address = Ordershippingaddress.objects.create(address_line1=long_address)
        self.assertEqual(len(address.address_line1), 200)

    def test_ordershippingaddress_city_max_length(self):
        """Test that city has 200 char limit"""
        long_city = 'C' * 200
        address = Ordershippingaddress.objects.create(city=long_city)
        self.assertEqual(len(address.city), 200)

    def test_ordershippingaddress_state_max_length(self):
        """Test that state has 40 char limit"""
        long_state = 'S' * 40
        address = Ordershippingaddress.objects.create(state=long_state)
        self.assertEqual(len(address.state), 40)

    def test_ordershippingaddress_zip_max_length(self):
        """Test that zip has 10 char limit"""
        long_zip = '1' * 10
        address = Ordershippingaddress.objects.create(zip=long_zip)
        self.assertEqual(len(address.zip), 10)


class OrderbillingaddressConstraintsTest(PostgreSQLTestCase):
    """Test Orderbillingaddress model constraints"""

    def test_orderbillingaddress_name_max_length(self):
        """Test that name has 200 char limit"""
        long_name = 'N' * 200
        address = Orderbillingaddress.objects.create(name=long_name)
        self.assertEqual(len(address.name), 200)

    def test_orderbillingaddress_address_line1_max_length(self):
        """Test that address_line1 has 200 char limit"""
        long_address = 'A' * 200
        address = Orderbillingaddress.objects.create(address_line1=long_address)
        self.assertEqual(len(address.address_line1), 200)

    def test_orderbillingaddress_city_max_length(self):
        """Test that city has 200 char limit"""
        long_city = 'C' * 200
        address = Orderbillingaddress.objects.create(city=long_city)
        self.assertEqual(len(address.city), 200)

    def test_orderbillingaddress_state_max_length(self):
        """Test that state has 40 char limit"""
        long_state = 'S' * 40
        address = Orderbillingaddress.objects.create(state=long_state)
        self.assertEqual(len(address.state), 40)

    def test_orderbillingaddress_zip_max_length(self):
        """Test that zip has 10 char limit"""
        long_zip = '1' * 10
        address = Orderbillingaddress.objects.create(zip=long_zip)
        self.assertEqual(len(address.zip), 10)


class OrderConstraintsTest(PostgreSQLTestCase):
    """Test Order model constraints"""

    def test_order_identifier_max_length(self):
        """Test that identifier has 100 char limit"""
        long_id = 'O' * 100
        order = Order.objects.create(
            identifier=long_id,
            order_total=100.00,
            agreed_with_terms_of_sale=True,
            order_date_time=timezone.now()
        )
        self.assertEqual(len(order.identifier), 100)

    def test_order_identifier_is_unique(self):
        """Test that identifier must be unique"""
        Order.objects.create(
            identifier='UNIQUE001',
            order_total=100.00,
            agreed_with_terms_of_sale=True,
            order_date_time=timezone.now()
        )
        with self.assertRaises(IntegrityError):
            Order.objects.create(
                identifier='UNIQUE001',
                order_total=200.00,
                agreed_with_terms_of_sale=True,
                order_date_time=timezone.now()
            )

    def test_order_sales_tax_amt_default_zero(self):
        """Test that sales_tax_amt defaults to 0"""
        order = Order.objects.create(
            identifier='TEST001',
            order_total=100.00,
            agreed_with_terms_of_sale=True,
            order_date_time=timezone.now()
        )
        self.assertEqual(order.sales_tax_amt, 0)

    def test_order_item_subtotal_default_zero(self):
        """Test that item_subtotal defaults to 0"""
        order = Order.objects.create(
            identifier='TEST002',
            order_total=100.00,
            agreed_with_terms_of_sale=True,
            order_date_time=timezone.now()
        )
        self.assertEqual(order.item_subtotal, 0)

    def test_order_agreed_with_terms_of_sale_default_false(self):
        """Test that agreed_with_terms_of_sale defaults to False"""
        order = Order.objects.create(
            identifier='TEST003',
            order_total=100.00,
            order_date_time=timezone.now()
        )
        self.assertFalse(order.agreed_with_terms_of_sale)

    def test_order_order_date_time_is_required(self):
        """Test that order_date_time is required"""
        with self.assertRaises((IntegrityError, ValueError)):
            Order.objects.create(
                identifier='TEST004',
                order_total=100.00,
                agreed_with_terms_of_sale=True
            )


class OrderskuConstraintsTest(PostgreSQLTestCase):
    """Test Ordersku model constraints"""

    def setUp(self):
        self.order = Order.objects.create(
            identifier='TEST001',
            order_total=100.00,
            agreed_with_terms_of_sale=True,
            order_date_time=timezone.now()
        )

        skutype = Skutype.objects.create(title='product')
        skuinventory = Skuinventory.objects.create(
            title='In Stock',
            identifier='in-stock'
        )
        self.sku = Sku.objects.create(
            sku_type=skutype,
            sku_inventory=skuinventory
        )

    def test_ordersku_quantity_default_one(self):
        """Test that quantity defaults to 1"""
        ordersku = Ordersku.objects.create(
            order=self.order,
            sku=self.sku
        )
        self.assertEqual(ordersku.quantity, 1)

    def test_ordersku_price_each_default_zero(self):
        """Test that price_each defaults to 0"""
        ordersku = Ordersku.objects.create(
            order=self.order,
            sku=self.sku
        )
        self.assertEqual(ordersku.price_each, 0)

    def test_ordersku_unique_together_order_sku(self):
        """Test that (order, sku) must be unique together"""
        Ordersku.objects.create(
            order=self.order,
            sku=self.sku
        )
        with self.assertRaises(IntegrityError):
            Ordersku.objects.create(
                order=self.order,
                sku=self.sku
            )


class StatusConstraintsTest(PostgreSQLTestCase):
    """Test Status model constraints"""

    def test_status_identifier_max_length(self):
        """Test that identifier has 100 char limit"""
        long_id = 'i' * 100
        status = Status.objects.create(
            identifier=long_id,
            title='test',
            description='test'
        )
        self.assertEqual(len(status.identifier), 100)

    def test_status_title_max_length(self):
        """Test that title has 100 char limit"""
        long_title = 't' * 100
        status = Status.objects.create(
            identifier='test',
            title=long_title,
            description='test'
        )
        self.assertEqual(len(status.title), 100)

    def test_status_description_max_length(self):
        """Test that description has 500 char limit"""
        long_desc = 'd' * 500
        status = Status.objects.create(
            identifier='test',
            title='test',
            description=long_desc
        )
        self.assertEqual(len(status.description), 500)


class OrderstatusConstraintsTest(PostgreSQLTestCase):
    """Test Orderstatus model constraints"""

    def setUp(self):
        self.order = Order.objects.create(
            identifier='TEST001',
            order_total=100.00,
            agreed_with_terms_of_sale=True,
            order_date_time=timezone.now()
        )
        self.status = Status.objects.create(
            identifier='pending',
            title='Pending',
            description='Order is pending'
        )

    def test_orderstatus_created_date_time_is_required(self):
        """Test that created_date_time is required"""
        with self.assertRaises((IntegrityError, ValueError)):
            Orderstatus.objects.create(
                order=self.order,
                status=self.status
            )

    def test_orderstatus_unique_together_order_status(self):
        """Test that (order, status) must be unique together"""
        Orderstatus.objects.create(
            order=self.order,
            status=self.status,
            created_date_time=timezone.now()
        )
        with self.assertRaises(IntegrityError):
            Orderstatus.objects.create(
                order=self.order,
                status=self.status,
                created_date_time=timezone.now()
            )


class OrdershippingmethodConstraintsTest(PostgreSQLTestCase):
    """Test Ordershippingmethod model constraints"""

    def setUp(self):
        self.order = Order.objects.create(
            identifier='TEST001',
            order_total=100.00,
            agreed_with_terms_of_sale=True,
            order_date_time=timezone.now()
        )
        self.shippingmethod = Shippingmethod.objects.create(
            identifier='standard',
            carrier='USPS',
            shipping_cost=5.00,
            tracking_code_base_url='https://test.com'
        )

    def test_ordershippingmethod_tracking_number_max_length(self):
        """Test that tracking_number has 100 char limit"""
        long_tracking = 'T' * 100
        osm = Ordershippingmethod.objects.create(
            order=self.order,
            shippingmethod=self.shippingmethod,
            tracking_number=long_tracking
        )
        self.assertEqual(len(osm.tracking_number), 100)

    def test_ordershippingmethod_unique_together_order_shippingmethod(self):
        """Test that (order, shippingmethod) must be unique together"""
        Ordershippingmethod.objects.create(
            order=self.order,
            shippingmethod=self.shippingmethod
        )
        with self.assertRaises(IntegrityError):
            Ordershippingmethod.objects.create(
                order=self.order,
                shippingmethod=self.shippingmethod
            )
