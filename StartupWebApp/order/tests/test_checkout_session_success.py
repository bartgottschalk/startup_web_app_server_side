# Unit tests for Checkout Session Success Handler endpoint

import json
from unittest.mock import patch, MagicMock
from decimal import Decimal

from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from order.models import (
    Cart, Cartsku, Cartshippingmethod,
    Product, Productsku, Productimage,
    Sku, Skuprice, Skutype, Skuinventory,
    Shippingmethod,
    Order, Ordersku, Orderstatus, Status,
    Orderconfiguration
)
from user.models import Member, Termsofuse, Prospect, Emailtype, Email, Emailstatus

from StartupWebApp.utilities import unittest_utilities


class CheckoutSessionSuccessHandlerTest(PostgreSQLTestCase):
    """Test the checkout_session_success endpoint"""

    def setUp(self):
        # Create groups and terms
        Group.objects.create(name='Members')
        Termsofuse.objects.create(
            version='1',
            version_note='Test',
            publication_date_time=timezone.now()
        )

        # Create user and member
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.member = Member.objects.create(
            user=self.user,
            mb_cd='MEMBER123'
        )

        # Allow checkout
        Orderconfiguration.objects.create(
            key='usernames_allowed_to_checkout',
            string_value='*'
        )
        Orderconfiguration.objects.create(
            key='an_ct_values_allowed_to_checkout',
            string_value='*'
        )

        # Create initial order status
        Status.objects.create(
            identifier='order-received',
            title='Order Received'
        )
        Orderconfiguration.objects.create(
            key='initial_order_status',
            string_value='order-received'
        )

        # Create shipping method
        self.shipping_method = Shippingmethod.objects.create(
            identifier='standard',
            carrier='USPS',
            shipping_cost=Decimal('5.99'),
            tracking_code_base_url='https://tools.usps.com/go/TrackConfirmAction?tLabels=',
            active=True
        )

        # Create product and SKU
        skutype = Skutype.objects.create(title='product')
        skuinventory = Skuinventory.objects.create(
            title='In Stock',
            identifier='in-stock'
        )

        product = Product.objects.create(
            title='Test Product',
            title_url='TestProduct',
            identifier='PROD001',
            headline='A great test product',
            description_part_1='This is a test product'
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
            sku_inventory=skuinventory,
            description='Test SKU'
        )

        Skuprice.objects.create(
            sku=self.sku,
            price=Decimal('29.99'),
            created_date_time=timezone.now()
        )

        Productsku.objects.create(product=product, sku=self.sku)

        # Create cart with items for member
        self.cart = Cart.objects.create(member=self.member)
        Cartsku.objects.create(cart=self.cart, sku=self.sku, quantity=2)
        Cartshippingmethod.objects.create(
            cart=self.cart,
            shippingmethod=self.shipping_method
        )

        # Create email templates
        email_type_member = Emailtype.objects.create(title='Member')
        email_type_prospect = Emailtype.objects.create(title='Prospect')
        email_status = Emailstatus.objects.create(title='Active')

        Email.objects.create(
            em_cd='ORDER_CONFIRMATION_MEMBER',
            email_type=email_type_member,
            email_status=email_status,
            subject='Order Confirmation - StartUpWebApp',
            from_address='bart+startupwebapp@mosaicmeshai.com',
            bcc_address='',
            body_html='',
            body_text='Hi {recipient_first_name}!{line_break}Thank you for your order!'
        )

        Email.objects.create(
            em_cd='ORDER_CONFIRMATION_PROSPECT',
            email_type=email_type_prospect,
            email_status=email_status,
            subject='Order Confirmation - StartUpWebApp',
            from_address='bart+startupwebapp@mosaicmeshai.com',
            bcc_address='',
            body_html='',
            body_text='Hi {recipient_first_name}!{line_break}Thank you for your order!'
        )

        Orderconfiguration.objects.create(
            key='order_confirmation_em_cd_member',
            string_value='ORDER_CONFIRMATION_MEMBER'
        )
        Orderconfiguration.objects.create(
            key='order_confirmation_em_cd_prospect',
            string_value='ORDER_CONFIRMATION_PROSPECT'
        )

    def test_checkout_session_success_requires_session_id(self):
        """Test that endpoint requires session_id parameter"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/checkout-session-success')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['checkout_session_success'], 'error')
        self.assertEqual(data['errors']['error'], 'session-id-required')

    @patch('stripe.checkout.Session.retrieve')
    def test_checkout_session_success_handles_invalid_session(self, mock_retrieve):
        """Test error handling for invalid session_id"""
        import stripe
        mock_retrieve.side_effect = stripe.error.InvalidRequestError(
            'No such checkout session',
            param='id'
        )

        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/checkout-session-success?session_id=invalid_session')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['checkout_session_success'], 'error')
        self.assertEqual(data['errors']['error'], 'invalid-session')

    @patch('stripe.checkout.Session.retrieve')
    def test_checkout_session_success_requires_payment_complete(self, mock_retrieve):
        """Test that endpoint requires payment to be completed"""
        # Mock incomplete session
        mock_session = MagicMock()
        mock_session.payment_status = 'unpaid'
        mock_retrieve.return_value = mock_session

        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/checkout-session-success?session_id=cs_test_123')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['checkout_session_success'], 'error')
        self.assertEqual(data['errors']['error'], 'payment-not-completed')

    @patch('stripe.checkout.Session.retrieve')
    def test_checkout_session_success_when_no_cart_found(self, mock_retrieve):
        """Test error handling when cart is not found"""
        # Mock completed session
        mock_session = MagicMock()
        mock_session.payment_status = 'paid'
        mock_retrieve.return_value = mock_session

        # Create user without cart
        user2 = User.objects.create_user(
            username='nocartuser',
            email='nocart@test.com',
            password='testpass123'
        )
        Member.objects.create(user=user2, mb_cd='MEMBER456')

        self.client.login(username='nocartuser', password='testpass123')

        response = self.client.get('/order/checkout-session-success?session_id=cs_test_nocart')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['checkout_session_success'], 'error')
        self.assertEqual(data['errors']['error'], 'cart-not-found')

    @patch('stripe.checkout.Session.retrieve')
    @patch('django.core.mail.EmailMultiAlternatives.send')
    def test_checkout_session_success_creates_order_for_member(self, mock_email_send, mock_retrieve):
        """Test successful order creation for authenticated member"""
        # Mock completed Stripe session
        mock_session = MagicMock()
        mock_session.id = 'cs_test_123'
        mock_session.payment_status = 'paid'
        mock_session.amount_total = 6597  # $65.97 in cents (2 × $29.99 + $5.99 shipping)
        mock_session.amount_subtotal = 5998  # $59.98 in cents
        mock_session.customer_email = 'test@test.com'

        # Mock customer details (billing address)
        mock_session.customer_details = MagicMock()
        mock_session.customer_details.name = 'John Doe'
        mock_session.customer_details.email = 'test@test.com'
        mock_session.customer_details.phone = '+1234567890'
        mock_session.customer_details.address = MagicMock()
        mock_session.customer_details.address.line1 = '123 Main St'
        mock_session.customer_details.address.line2 = 'Apt 4'
        mock_session.customer_details.address.city = 'New York'
        mock_session.customer_details.address.state = 'NY'
        mock_session.customer_details.address.postal_code = '10001'
        mock_session.customer_details.address.country = 'US'

        # Mock shipping details (new Stripe API structure)
        mock_session.collected_information = MagicMock()
        mock_session.collected_information.shipping_details = MagicMock()
        mock_session.collected_information.shipping_details.name = 'John Doe'
        mock_session.collected_information.shipping_details.address = MagicMock()
        mock_session.collected_information.shipping_details.address.line1 = '456 Oak Ave'
        mock_session.collected_information.shipping_details.address.line2 = ''
        mock_session.collected_information.shipping_details.address.city = 'Boston'
        mock_session.collected_information.shipping_details.address.state = 'MA'
        mock_session.collected_information.shipping_details.address.postal_code = '02101'
        mock_session.collected_information.shipping_details.address.country = 'US'

        # Mock payment intent
        mock_session.payment_intent = 'pi_test_123'

        mock_retrieve.return_value = mock_session

        self.client.login(username='testuser', password='testpass123')

        response = self.client.get('/order/checkout-session-success?session_id=cs_test_123')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['checkout_session_success'], 'success')
        self.assertIn('order_identifier', data)

        # Verify order was created
        order = Order.objects.get(identifier=data['order_identifier'])
        self.assertEqual(order.member, self.member)
        self.assertIsNone(order.prospect)
        self.assertTrue(order.agreed_with_terms_of_sale)

        # Verify shipping address
        self.assertIsNotNone(order.shipping_address)
        self.assertEqual(order.shipping_address.name, 'John Doe')
        self.assertEqual(order.shipping_address.address_line1, '456 Oak Ave')
        self.assertEqual(order.shipping_address.city, 'Boston')
        self.assertEqual(order.shipping_address.state, 'MA')
        self.assertEqual(order.shipping_address.zip, '02101')
        self.assertEqual(order.shipping_address.country_code, 'US')

        # Verify billing address
        self.assertIsNotNone(order.billing_address)
        self.assertEqual(order.billing_address.name, 'John Doe')
        self.assertEqual(order.billing_address.address_line1, '123 Main St')
        self.assertEqual(order.billing_address.city, 'New York')
        self.assertEqual(order.billing_address.state, 'NY')
        self.assertEqual(order.billing_address.zip, '10001')

        # Verify payment
        self.assertIsNotNone(order.payment)
        self.assertEqual(order.payment.email, 'test@test.com')
        self.assertEqual(order.payment.stripe_payment_intent_id, 'pi_test_123')

        # Verify order SKUs were created
        order_skus = Ordersku.objects.filter(order=order)
        self.assertEqual(order_skus.count(), 1)
        self.assertEqual(order_skus.first().sku, self.sku)
        self.assertEqual(order_skus.first().quantity, 2)
        self.assertEqual(order_skus.first().price_each, Decimal('29.99'))

        # Verify order status was created
        order_statuses = Orderstatus.objects.filter(order=order)
        self.assertEqual(order_statuses.count(), 1)
        self.assertEqual(order_statuses.first().status.identifier, 'order-received')

        # Verify cart was deleted
        with self.assertRaises(Cart.DoesNotExist):
            Cart.objects.get(id=self.cart.id)

        # Verify email was sent
        mock_email_send.assert_called_once()

    @patch('stripe.checkout.Session.retrieve')
    @patch('order.utilities.order_utils.look_up_cart')
    @patch('django.core.mail.EmailMultiAlternatives.send')
    def test_checkout_session_success_creates_order_for_prospect(
        self, mock_email_send, mock_look_up_cart, mock_retrieve
    ):
        """Test successful order creation for anonymous prospect"""
        # Create prospect
        prospect = Prospect.objects.create(
            email='prospect@test.com',
            pr_cd='PROSPECT123',
            created_date_time=timezone.now()
        )

        # Create anonymous cart (without member)
        anon_cart = Cart.objects.create(anonymous_cart_id='anon_cart_123')
        Cartsku.objects.create(cart=anon_cart, sku=self.sku, quantity=1)
        Cartshippingmethod.objects.create(
            cart=anon_cart,
            shippingmethod=self.shipping_method
        )

        # Mock cart lookup
        mock_look_up_cart.return_value = anon_cart

        # Mock completed Stripe session
        mock_session = MagicMock()
        mock_session.id = 'cs_test_prospect'
        mock_session.payment_status = 'paid'
        mock_session.amount_total = 3598  # $35.98 (1 × $29.99 + $5.99)
        mock_session.amount_subtotal = 2999
        mock_session.customer_email = 'prospect@test.com'

        # Mock addresses
        mock_session.customer_details = MagicMock()
        mock_session.customer_details.name = 'Jane Smith'
        mock_session.customer_details.email = 'prospect@test.com'
        mock_session.customer_details.phone = '+19876543210'
        mock_session.customer_details.address = MagicMock()
        mock_session.customer_details.address.line1 = '789 Elm St'
        mock_session.customer_details.address.line2 = None
        mock_session.customer_details.address.city = 'Chicago'
        mock_session.customer_details.address.state = 'IL'
        mock_session.customer_details.address.postal_code = '60601'
        mock_session.customer_details.address.country = 'US'

        mock_session.collected_information = MagicMock()
        mock_session.collected_information.shipping_details = MagicMock()
        mock_session.collected_information.shipping_details.name = 'Jane Smith'
        mock_session.collected_information.shipping_details.address = MagicMock()
        mock_session.collected_information.shipping_details.address.line1 = '789 Elm St'
        mock_session.collected_information.shipping_details.address.line2 = None
        mock_session.collected_information.shipping_details.address.city = 'Chicago'
        mock_session.collected_information.shipping_details.address.state = 'IL'
        mock_session.collected_information.shipping_details.address.postal_code = '60601'
        mock_session.collected_information.shipping_details.address.country = 'US'

        mock_session.payment_intent = 'pi_test_prospect'

        mock_retrieve.return_value = mock_session

        # Don't log in - anonymous request
        response = self.client.get('/order/checkout-session-success?session_id=cs_test_prospect')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['checkout_session_success'], 'success')

        # Verify order was created for prospect
        order = Order.objects.get(identifier=data['order_identifier'])
        self.assertIsNone(order.member)
        self.assertEqual(order.prospect, prospect)

        # Verify email was sent
        mock_email_send.assert_called_once()

    @patch('order.utilities.order_utils.look_up_cart')
    @patch('stripe.checkout.Session.retrieve')
    @patch('django.core.mail.EmailMultiAlternatives.send')
    def test_creates_prospect_with_created_date_time_for_new_anonymous_user(
        self, mock_email_send, mock_retrieve, mock_look_up_cart
    ):
        """Test that Prospect is created with created_date_time for new anonymous users"""
        # Create anonymous cart (no existing prospect)
        anon_cart = Cart.objects.create(anonymous_cart_id='new_anon_cart')
        Cartsku.objects.create(cart=anon_cart, sku=self.sku, quantity=1)
        Cartshippingmethod.objects.create(
            cart=anon_cart,
            shippingmethod=self.shipping_method
        )

        # Mock cart lookup
        mock_look_up_cart.return_value = anon_cart

        # Mock completed Stripe session
        mock_session = MagicMock()
        mock_session.id = 'cs_test_new_prospect'
        mock_session.payment_status = 'paid'
        mock_session.amount_total = 3598
        mock_session.amount_subtotal = 2999
        mock_session.customer_email = 'newprospect@test.com'  # Email that doesn't exist yet

        mock_session.customer_details = MagicMock()
        mock_session.customer_details.name = 'New User'
        mock_session.customer_details.email = 'newprospect@test.com'
        mock_session.customer_details.phone = '+15551234567'
        mock_session.customer_details.address = MagicMock()
        mock_session.customer_details.address.line1 = '999 New St'
        mock_session.customer_details.address.city = 'Newcity'
        mock_session.customer_details.address.state = 'CA'
        mock_session.customer_details.address.postal_code = '90210'
        mock_session.customer_details.address.country = 'US'

        mock_session.collected_information = MagicMock()
        mock_session.collected_information.shipping_details = MagicMock()
        mock_session.collected_information.shipping_details.name = 'New User'
        mock_session.collected_information.shipping_details.address = MagicMock()
        mock_session.collected_information.shipping_details.address.line1 = '999 New St'
        mock_session.collected_information.shipping_details.address.city = 'Newcity'
        mock_session.collected_information.shipping_details.address.state = 'CA'
        mock_session.collected_information.shipping_details.address.postal_code = '90210'
        mock_session.collected_information.shipping_details.address.country = 'US'

        mock_session.payment_intent = 'pi_test_new_prospect'

        mock_retrieve.return_value = mock_session

        # Verify prospect doesn't exist yet
        self.assertFalse(Prospect.objects.filter(email='newprospect@test.com').exists())

        # Call endpoint (don't log in - anonymous)
        response = self.client.get('/order/checkout-session-success?session_id=cs_test_new_prospect')

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        # Verify prospect was created with created_date_time
        prospect = Prospect.objects.get(email='newprospect@test.com')
        self.assertIsNotNone(prospect.created_date_time, "Prospect should have created_date_time set")
        self.assertIsNotNone(prospect.pr_cd, "Prospect should have pr_cd set")

        # Verify order was created
        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['checkout_session_success'], 'success')
        order = Order.objects.get(identifier=data['order_identifier'])
        self.assertEqual(order.prospect, prospect)

    @patch('stripe.checkout.Session.retrieve')
    @patch('django.core.mail.EmailMultiAlternatives.send')
    def test_checkout_session_success_prevents_duplicate_orders(self, mock_email_send, mock_retrieve):
        """Test that the same session cannot create multiple orders"""
        # Mock completed session
        mock_session = MagicMock()
        mock_session.id = 'cs_test_duplicate'
        mock_session.payment_status = 'paid'
        mock_session.amount_total = 6597
        mock_session.amount_subtotal = 5998
        mock_session.customer_email = 'test@test.com'
        mock_session.payment_intent = 'pi_test_duplicate'

        # Mock addresses (minimal for this test)
        mock_session.customer_details = MagicMock()
        mock_session.customer_details.name = 'Test User'
        mock_session.customer_details.email = 'test@test.com'
        mock_session.customer_details.phone = '+11234567890'
        mock_session.customer_details.address = MagicMock()
        mock_session.customer_details.address.line1 = '123 Test St'
        mock_session.customer_details.address.line2 = None
        mock_session.customer_details.address.city = 'Test City'
        mock_session.customer_details.address.state = 'TS'
        mock_session.customer_details.address.postal_code = '12345'
        mock_session.customer_details.address.country = 'US'

        mock_session.collected_information = MagicMock()
        mock_session.collected_information.shipping_details = MagicMock()
        mock_session.collected_information.shipping_details.name = 'Test User'
        mock_session.collected_information.shipping_details.address = MagicMock()
        mock_session.collected_information.shipping_details.address.line1 = '123 Test St'
        mock_session.collected_information.shipping_details.address.line2 = None
        mock_session.collected_information.shipping_details.address.city = 'Test City'
        mock_session.collected_information.shipping_details.address.state = 'TS'
        mock_session.collected_information.shipping_details.address.postal_code = '12345'
        mock_session.collected_information.shipping_details.address.country = 'US'

        mock_session.payment_intent = 'pi_test_duplicate'

        mock_retrieve.return_value = mock_session

        self.client.login(username='testuser', password='testpass123')

        # First request should succeed
        response1 = self.client.get('/order/checkout-session-success?session_id=cs_test_duplicate')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response1)
        data1 = json.loads(response1.content.decode('utf8'))
        self.assertEqual(data1['checkout_session_success'], 'success')
        order_identifier = data1['order_identifier']

        # Second request with same session should return existing order
        response2 = self.client.get('/order/checkout-session-success?session_id=cs_test_duplicate')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response2)
        data2 = json.loads(response2.content.decode('utf8'))
        self.assertEqual(data2['checkout_session_success'], 'success')
        self.assertEqual(data2['order_identifier'], order_identifier)

        # Verify only one order was created
        orders = Order.objects.filter(payment__stripe_payment_intent_id='pi_test_duplicate')
        self.assertEqual(orders.count(), 1)

        # Verify email was sent only once
        self.assertEqual(mock_email_send.call_count, 1)
