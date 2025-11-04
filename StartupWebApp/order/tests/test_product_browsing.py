# Unit tests for product browsing endpoints

import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from order.models import (
    Product, Productimage, Productvideo, Productsku,
    Sku, Skuprice, Skuimage, Skutype, Skuinventory,
    Order, Orderpayment, Ordershippingaddress, Orderbillingaddress,
    Ordersku, Status, Orderstatus, Shippingmethod, Ordershippingmethod,
    Orderconfiguration
)
from user.models import Member, Prospect, Termsofuse

from StartupWebApp.utilities import unittest_utilities


class IndexEndpointTest(TestCase):
    """Test the index endpoint"""

    def test_index_returns_version(self):
        """Test that index endpoint returns API version"""
        response = self.client.get('/order/')

        self.assertEqual(response.status_code, 200)
        self.assertIn("order API", response.content.decode('utf8'))
        self.assertIn("0.0.1", response.content.decode('utf8'))


class ProductsEndpointTest(TestCase):
    """Test the products list endpoint"""

    def setUp(self):
        # Create necessary objects
        skutype = Skutype.objects.create(title='product')
        skuinventory = Skuinventory.objects.create(
            title='In Stock',
            identifier='in-stock',
            description='In Stock items'
        )

        # Create first product
        self.product1 = Product.objects.create(
            title='Paper Clips',
            title_url='PaperClips',
            identifier='PROD001',
            headline='High quality paper clips',
            description_part_1='Made from metal',
            description_part_2='Very durable'
        )

        sku1 = Sku.objects.create(
            color='Silver',
            size='Medium',
            sku_type=skutype,
            description='Standard paperclip',
            sku_inventory=skuinventory
        )

        Skuprice.objects.create(
            sku=sku1,
            price=3.50,
            created_date_time=timezone.now()
        )

        Productsku.objects.create(product=self.product1, sku=sku1)

        Productimage.objects.create(
            product=self.product1,
            image_url='https://example.com/paperclip.jpg',
            main_image=True
        )

        # Create second product with multiple SKUs (different prices)
        self.product2 = Product.objects.create(
            title='Notebooks',
            title_url='Notebooks',
            identifier='PROD002',
            headline='Quality notebooks',
            description_part_1='100 pages',
            description_part_2='College ruled'
        )

        sku2a = Sku.objects.create(
            color='Blue',
            size='Small',
            sku_type=skutype,
            description='Small notebook',
            sku_inventory=skuinventory
        )

        sku2b = Sku.objects.create(
            color='Red',
            size='Large',
            sku_type=skutype,
            description='Large notebook',
            sku_inventory=skuinventory
        )

        Skuprice.objects.create(
            sku=sku2a,
            price=5.00,
            created_date_time=timezone.now()
        )

        Skuprice.objects.create(
            sku=sku2b,
            price=8.00,
            created_date_time=timezone.now()
        )

        Productsku.objects.create(product=self.product2, sku=sku2a)
        Productsku.objects.create(product=self.product2, sku=sku2b)

        Productimage.objects.create(
            product=self.product2,
            image_url='https://example.com/notebook.jpg',
            main_image=True
        )

    def test_products_returns_all_products(self):
        """Test that products endpoint returns all products"""
        response = self.client.get('/order/products')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertIn('products_data', data)
        self.assertIn('order-api-version', data)
        self.assertEqual(data['order-api-version'], '0.0.1')

        products_data = data['products_data']
        self.assertEqual(len(products_data), 2)
        self.assertIn('PROD001', products_data)
        self.assertIn('PROD002', products_data)

    def test_products_includes_product_details(self):
        """Test that products include all necessary details"""
        response = self.client.get('/order/products')

        data = json.loads(response.content.decode('utf8'))
        product_data = data['products_data']['PROD001']

        self.assertEqual(product_data['title'], 'Paper Clips')
        self.assertEqual(product_data['title_url'], 'PaperClips')
        self.assertEqual(product_data['identifier'], 'PROD001')
        self.assertEqual(product_data['headline'], 'High quality paper clips')
        self.assertEqual(product_data['description_part_1'], 'Made from metal')
        self.assertEqual(product_data['description_part_2'], 'Very durable')

    def test_products_includes_price_range(self):
        """Test that products include price_low and price_high"""
        response = self.client.get('/order/products')

        data = json.loads(response.content.decode('utf8'))

        # Product with single SKU
        product1_data = data['products_data']['PROD001']
        self.assertEqual(product1_data['price_low'], 3.50)
        self.assertEqual(product1_data['price_high'], 3.50)

        # Product with multiple SKUs
        product2_data = data['products_data']['PROD002']
        self.assertEqual(product2_data['price_low'], 5.00)
        self.assertEqual(product2_data['price_high'], 8.00)

    def test_products_includes_main_image(self):
        """Test that products include main product image"""
        response = self.client.get('/order/products')

        data = json.loads(response.content.decode('utf8'))
        product_data = data['products_data']['PROD001']

        self.assertEqual(product_data['product_image_url'],
                        'https://example.com/paperclip.jpg')

    def test_products_when_no_products_exist(self):
        """Test products endpoint when no products exist"""
        Product.objects.all().delete()

        response = self.client.get('/order/products')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(len(data['products_data']), 0)


class ProductEndpointTest(TestCase):
    """Test the individual product detail endpoint"""

    def setUp(self):
        # Create necessary objects
        self.skutype = Skutype.objects.create(title='product')
        self.skuinventory = Skuinventory.objects.create(
            title='In Stock',
            identifier='in-stock',
            description='In Stock items'
        )

        # Create product
        self.product = Product.objects.create(
            title='Paper Clips',
            title_url='PaperClips',
            identifier='PROD001',
            headline='High quality paper clips',
            description_part_1='Made from metal',
            description_part_2='Very durable'
        )

        # Create SKUs
        self.sku1 = Sku.objects.create(
            color='Silver',
            size='Medium',
            sku_type=self.skutype,
            description='Standard paperclip',
            sku_inventory=self.skuinventory
        )

        self.sku2 = Sku.objects.create(
            color='Gold',
            size='Large',
            sku_type=self.skutype,
            description='Premium paperclip',
            sku_inventory=self.skuinventory
        )

        Skuprice.objects.create(
            sku=self.sku1,
            price=3.50,
            created_date_time=timezone.now()
        )

        Skuprice.objects.create(
            sku=self.sku2,
            price=5.00,
            created_date_time=timezone.now()
        )

        Productsku.objects.create(product=self.product, sku=self.sku1)
        Productsku.objects.create(product=self.product, sku=self.sku2)

        # Create product images
        Productimage.objects.create(
            product=self.product,
            image_url='https://example.com/paperclip-main.jpg',
            main_image=True,
            caption='Main product image'
        )

        Productimage.objects.create(
            product=self.product,
            image_url='https://example.com/paperclip-alt.jpg',
            main_image=False,
            caption='Alternative view'
        )

        # Create product video
        Productvideo.objects.create(
            product=self.product,
            video_url='https://example.com/paperclip.mp4',
            video_thumbnail_url='https://example.com/paperclip-thumb.jpg',
            caption='Product demo video'
        )

        # Create SKU images
        Skuimage.objects.create(
            sku=self.sku1,
            image_url='https://example.com/silver-sku.jpg',
            main_image=True,
            caption='Silver variant'
        )

    def test_product_returns_success_with_valid_identifier(self):
        """Test that product endpoint returns success with valid identifier"""
        response = self.client.get('/order/product/PROD001')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['product'], 'success')
        self.assertEqual(data['product_identifier'], 'PROD001')
        self.assertIn('product_data', data)

    def test_product_includes_all_product_details(self):
        """Test that product includes complete product information"""
        response = self.client.get('/order/product/PROD001')

        data = json.loads(response.content.decode('utf8'))
        product_data = data['product_data']

        self.assertEqual(product_data['title'], 'Paper Clips')
        self.assertEqual(product_data['title_url'], 'PaperClips')
        self.assertEqual(product_data['identifier'], 'PROD001')
        self.assertEqual(product_data['headline'], 'High quality paper clips')
        self.assertEqual(product_data['description_part_1'], 'Made from metal')
        self.assertEqual(product_data['description_part_2'], 'Very durable')

    def test_product_includes_all_images(self):
        """Test that product includes all product images"""
        response = self.client.get('/order/product/PROD001')

        data = json.loads(response.content.decode('utf8'))
        product_images = data['product_data']['product_images']

        self.assertEqual(len(product_images), 2)

        # Check that main image is included
        main_image_found = False
        for img_id, img_data in product_images.items():
            if img_data['main']:
                main_image_found = True
                self.assertEqual(img_data['image_url'],
                               'https://example.com/paperclip-main.jpg')
                self.assertEqual(img_data['caption'], 'Main product image')

        self.assertTrue(main_image_found, 'Main image should be present')

    def test_product_includes_all_videos(self):
        """Test that product includes all product videos"""
        response = self.client.get('/order/product/PROD001')

        data = json.loads(response.content.decode('utf8'))
        product_videos = data['product_data']['product_videos']

        self.assertEqual(len(product_videos), 1)

        video_data = list(product_videos.values())[0]
        self.assertEqual(video_data['video_url'],
                        'https://example.com/paperclip.mp4')
        self.assertEqual(video_data['video_thumbnail_url'],
                        'https://example.com/paperclip-thumb.jpg')
        self.assertEqual(video_data['caption'], 'Product demo video')

    def test_product_includes_all_skus(self):
        """Test that product includes all SKUs with details"""
        response = self.client.get('/order/product/PROD001')

        data = json.loads(response.content.decode('utf8'))
        skus = data['product_data']['skus']

        self.assertEqual(len(skus), 2)

        # Check SKU details
        sku1_data = skus[str(self.sku1.id)]
        self.assertEqual(sku1_data['color'], 'Silver')
        self.assertEqual(sku1_data['size'], 'Medium')
        self.assertEqual(sku1_data['description'], 'Standard paperclip')
        self.assertEqual(sku1_data['price'], 3.50)
        self.assertEqual(sku1_data['inventory_status_identifier'], 'in-stock')
        self.assertEqual(sku1_data['inventory_status_title'], 'In Stock')

    def test_product_includes_sku_images(self):
        """Test that SKUs include their specific images"""
        response = self.client.get('/order/product/PROD001')

        data = json.loads(response.content.decode('utf8'))
        sku1_data = data['product_data']['skus'][str(self.sku1.id)]

        self.assertIn('sku_images', sku1_data)
        self.assertEqual(len(sku1_data['sku_images']), 1)

        sku_image = list(sku1_data['sku_images'].values())[0]
        self.assertEqual(sku_image['image_url'],
                        'https://example.com/silver-sku.jpg')
        self.assertTrue(sku_image['main'])
        self.assertEqual(sku_image['caption'], 'Silver variant')

    def test_product_with_invalid_identifier_returns_error(self):
        """Test that invalid product identifier returns error"""
        response = self.client.get('/order/product/INVALID')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['product'], 'error')
        self.assertIn('errors', data)
        self.assertEqual(data['errors']['error'], 'product-identifier-not-found')
        self.assertEqual(data['product_identifier'], 'INVALID')


class OrderDetailEndpointTest(TestCase):
    """Test the order detail endpoint"""

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

        # Create prospect
        self.prospect = Prospect.objects.create(
            email='prospect@test.com',
            pr_cd='PROSPECT456',
            created_date_time=timezone.now()
        )

        # Create order configuration and status
        Orderconfiguration.objects.create(
            key='initial_order_status',
            string_value='pending'
        )

        status = Status.objects.create(
            identifier='pending',
            title='Pending',
            description='Order is pending'
        )

        # Create shipping method
        shippingmethod = Shippingmethod.objects.create(
            identifier='standard',
            carrier='USPS',
            shipping_cost=5.00,
            tracking_code_base_url='https://tools.usps.com/go/TrackConfirmAction'
        )

        # Create product and SKU for order
        skutype = Skutype.objects.create(title='product')
        skuinventory = Skuinventory.objects.create(
            title='In Stock',
            identifier='in-stock'
        )

        product = Product.objects.create(
            title='Test Product',
            title_url='TestProduct',
            identifier='PROD001'
        )

        Productimage.objects.create(
            product=product,
            image_url='https://example.com/product.jpg',
            main_image=True
        )

        self.sku = Sku.objects.create(
            color='Blue',
            size='Medium',
            sku_type=skutype,
            sku_inventory=skuinventory
        )

        Skuprice.objects.create(
            sku=self.sku,
            price=10.00,
            created_date_time=timezone.now()
        )

        Productsku.objects.create(product=product, sku=self.sku)

        # Create member order
        payment = Orderpayment.objects.create(
            email=self.user.email,
            payment_type='card',
            card_brand='Visa',
            card_last4='4242'
        )

        shipping_address = Ordershippingaddress.objects.create(
            name='Test User',
            address_line1='123 Main St',
            city='Anytown',
            state='CA',
            zip='12345',
            country='United States',
            country_code='US'
        )

        billing_address = Orderbillingaddress.objects.create(
            name='Test User',
            address_line1='123 Main St',
            city='Anytown',
            state='CA',
            zip='12345',
            country='United States',
            country_code='US'
        )

        self.member_order = Order.objects.create(
            identifier='ORDER001',
            member=self.member,
            payment=payment,
            shipping_address=shipping_address,
            billing_address=billing_address,
            sales_tax_amt=0,
            item_subtotal=10.00,
            item_discount_amt=0,
            shipping_amt=5.00,
            shipping_discount_amt=0,
            order_total=15.00,
            agreed_with_terms_of_sale=True,
            order_date_time=timezone.now()
        )

        Ordersku.objects.create(
            order=self.member_order,
            sku=self.sku,
            quantity=1,
            price_each=10.00
        )

        Orderstatus.objects.create(
            order=self.member_order,
            status=status,
            created_date_time=timezone.now()
        )

        Ordershippingmethod.objects.create(
            order=self.member_order,
            shippingmethod=shippingmethod
        )

        # Create prospect (anonymous) order
        prospect_payment = Orderpayment.objects.create(
            email=self.prospect.email,
            payment_type='card',
            card_brand='Mastercard',
            card_last4='5555'
        )

        prospect_shipping_address = Ordershippingaddress.objects.create(
            name='Prospect User',
            address_line1='456 Oak Ave',
            city='Other Town',
            state='NY',
            zip='54321',
            country='United States',
            country_code='US'
        )

        prospect_billing_address = Orderbillingaddress.objects.create(
            name='Prospect User',
            address_line1='456 Oak Ave',
            city='Other Town',
            state='NY',
            zip='54321',
            country='United States',
            country_code='US'
        )

        self.prospect_order = Order.objects.create(
            identifier='ORDER002',
            prospect=self.prospect,
            payment=prospect_payment,
            shipping_address=prospect_shipping_address,
            billing_address=prospect_billing_address,
            sales_tax_amt=0,
            item_subtotal=20.00,
            item_discount_amt=0,
            shipping_amt=5.00,
            shipping_discount_amt=0,
            order_total=25.00,
            agreed_with_terms_of_sale=True,
            order_date_time=timezone.now()
        )

        Ordersku.objects.create(
            order=self.prospect_order,
            sku=self.sku,
            quantity=2,
            price_each=10.00
        )

        Orderstatus.objects.create(
            order=self.prospect_order,
            status=status,
            created_date_time=timezone.now()
        )

        Ordershippingmethod.objects.create(
            order=self.prospect_order,
            shippingmethod=shippingmethod
        )

    def test_order_detail_member_can_view_own_order(self):
        """Test that logged-in member can view their own order"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/ORDER001')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['order_detail'], 'success')
        self.assertIn('order_data', data)

    def test_order_detail_member_cannot_view_other_order(self):
        """Test that member cannot view another member's order"""
        self.client.login(username='testuser', password='testpass123')

        # Try to view prospect order
        response = self.client.get('/order/ORDER002')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['order_detail'], 'error')
        self.assertEqual(data['errors']['error'], 'order-not-in-account')

    def test_order_detail_anonymous_can_view_prospect_order(self):
        """Test that anonymous users can view prospect orders"""
        response = self.client.get('/order/ORDER002')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['order_detail'], 'success')
        self.assertIn('order_data', data)

    def test_order_detail_anonymous_cannot_view_member_order(self):
        """Test that anonymous users cannot view member orders"""
        response = self.client.get('/order/ORDER001')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['order_detail'], 'error')
        self.assertEqual(data['errors']['error'], 'log-in-required-to-view-order')

    def test_order_detail_with_invalid_identifier_returns_error(self):
        """Test that invalid order identifier returns error"""
        response = self.client.get('/order/INVALID')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['order_detail'], 'error')
        self.assertEqual(data['errors']['error'], 'order-not-found')
        self.assertEqual(data['order_identifier'], 'INVALID')
