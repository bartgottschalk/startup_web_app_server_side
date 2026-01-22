# Unit tests for Stripe Webhook Handler endpoint

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
    Order, Status,
    Orderconfiguration, Orderpayment
)
from user.models import Member, Termsofuse, Emailtype, Email, Emailstatus


class StripeWebhookHandlerTest(PostgreSQLTestCase):
    """Test the stripe_webhook endpoint"""

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

        # Webhook test data
        self.webhook_secret = 'whsec_test_secret_123'
        self.test_payload = json.dumps({
            'id': 'evt_test_123',
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_123',
                    'payment_intent': 'pi_test_123',
                    'payment_status': 'paid'
                }
            }
        })

    @patch('stripe.Webhook.construct_event')
    def test_webhook_rejects_invalid_signature(self, mock_construct_event):
        """Test that webhook rejects requests with invalid signatures"""
        import stripe
        mock_construct_event.side_effect = stripe.error.SignatureVerificationError(
            'Invalid signature',
            sig_header='invalid_sig'
        )

        response = self.client.post(
            '/order/stripe-webhook',
            data=self.test_payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='invalid_signature'
        )

        # Should return 400 for signature verification failure
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content.decode('utf8'))
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'invalid-signature')

    @patch('stripe.Webhook.construct_event')
    def test_webhook_handles_malformed_json(self, mock_construct_event):
        """Test that webhook handles malformed JSON gracefully"""
        mock_construct_event.side_effect = ValueError('Invalid JSON')

        response = self.client.post(
            '/order/stripe-webhook',
            data='invalid json{',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_sig'
        )

        # Should return 400 for parse errors
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content.decode('utf8'))
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'invalid-payload')

    @patch('stripe.Webhook.construct_event')
    def test_webhook_handles_checkout_session_completed_existing_order(self, mock_construct_event):
        """Test webhook handles checkout.session.completed when order already exists"""
        # Create existing order with payment
        payment = Orderpayment.objects.create(
            email='test@test.com',
            payment_type='card',
            card_name='John Doe',
            stripe_payment_intent_id='pi_test_existing'
        )

        Order.objects.create(
            identifier='TEST-ORDER-001',
            member=self.member,
            payment=payment,
            sales_tax_amt=0,
            item_subtotal=Decimal('59.98'),
            shipping_amt=Decimal('5.99'),
            order_total=Decimal('65.97'),
            agreed_with_terms_of_sale=True,
            order_date_time=timezone.now()
        )

        # Mock webhook event - use dict-like access
        mock_event = {
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_123',
                    'payment_intent': 'pi_test_existing',
                    'payment_status': 'paid'
                }
            }
        }
        mock_construct_event.return_value = mock_event

        payload = json.dumps({
            'id': 'evt_test_123',
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_123',
                    'payment_intent': 'pi_test_existing',
                    'payment_status': 'paid'
                }
            }
        })

        response = self.client.post(
            '/order/stripe-webhook',
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_sig'
        )

        # Should return 200 - order already exists, nothing to do
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['received'], True)
        self.assertIn('order_identifier', data)
        self.assertEqual(data['order_identifier'], 'TEST-ORDER-001')

    @patch('stripe.Webhook.construct_event')
    def test_webhook_handles_checkout_session_expired(self, mock_construct_event):
        """Test webhook handles checkout.session.expired event"""
        # Mock webhook event - use dict-like access
        mock_event = {
            'type': 'checkout.session.expired',
            'data': {
                'object': {
                    'id': 'cs_test_expired'
                }
            }
        }
        mock_construct_event.return_value = mock_event

        payload = json.dumps({
            'id': 'evt_test_expired',
            'type': 'checkout.session.expired',
            'data': {
                'object': {
                    'id': 'cs_test_expired'
                }
            }
        })

        response = self.client.post(
            '/order/stripe-webhook',
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_sig'
        )

        # Should return 200 - just log the expiration
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['received'], True)

    @patch('stripe.Webhook.construct_event')
    def test_webhook_handles_unknown_event_type(self, mock_construct_event):
        """Test webhook handles unknown event types gracefully"""
        # Mock webhook event - use dict-like access
        mock_event = {
            'type': 'payment_intent.created',
            'data': {
                'object': {}
            }
        }
        mock_construct_event.return_value = mock_event

        payload = json.dumps({
            'id': 'evt_test_unknown',
            'type': 'payment_intent.created',
            'data': {
                'object': {}
            }
        })

        response = self.client.post(
            '/order/stripe-webhook',
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_sig'
        )

        # Should return 200 - acknowledge receipt but don't process
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['received'], True)

    @patch('stripe.checkout.Session.retrieve')
    @patch('stripe.Webhook.construct_event')
    @patch('django.core.mail.EmailMultiAlternatives.send')
    def test_webhook_creates_order_for_checkout_session_completed(
        self, mock_email_send, mock_construct_event, mock_session_retrieve
    ):
        """Test webhook creates order when checkout.session.completed event arrives first"""
        # Mock Stripe session retrieval
        mock_session = MagicMock()
        mock_session.id = 'cs_test_webhook'
        mock_session.payment_status = 'paid'
        mock_session.payment_intent = 'pi_test_webhook_new'
        mock_session.customer_email = 'test@test.com'
        mock_session.metadata = {'cart_id': str(self.cart.id)}

        # Mock customer details (billing address)
        mock_session.customer_details = MagicMock()
        mock_session.customer_details.name = 'John Doe'
        mock_session.customer_details.email = 'test@test.com'
        mock_session.customer_details.address = MagicMock()
        mock_session.customer_details.address.line1 = '123 Main St'
        mock_session.customer_details.address.city = 'Anytown'
        mock_session.customer_details.address.state = 'CA'
        mock_session.customer_details.address.postal_code = '12345'
        mock_session.customer_details.address.country = 'US'

        # Mock shipping details
        mock_session.collected_information = MagicMock()
        mock_session.collected_information.shipping_details = MagicMock()
        mock_session.collected_information.shipping_details.name = 'John Doe'
        mock_session.collected_information.shipping_details.address = MagicMock()
        mock_session.collected_information.shipping_details.address.line1 = '123 Main St'
        mock_session.collected_information.shipping_details.address.city = 'Anytown'
        mock_session.collected_information.shipping_details.address.state = 'CA'
        mock_session.collected_information.shipping_details.address.postal_code = '12345'
        mock_session.collected_information.shipping_details.address.country = 'US'

        mock_session_retrieve.return_value = mock_session

        # Mock webhook event - use dict-like access
        mock_event = {
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_webhook',
                    'payment_intent': 'pi_test_webhook_new',
                    'payment_status': 'paid',
                    'metadata': {
                        'cart_id': str(self.cart.id)
                    }
                }
            }
        }
        mock_construct_event.return_value = mock_event

        payload = json.dumps({
            'id': 'evt_test_create_order',
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_webhook',
                    'payment_intent': 'pi_test_webhook_new',
                    'payment_status': 'paid',
                    'metadata': {
                        'cart_id': str(self.cart.id)
                    }
                }
            }
        })

        # Verify no order exists yet
        self.assertEqual(Order.objects.count(), 0)

        response = self.client.post(
            '/order/stripe-webhook',
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_sig'
        )

        # Should return 200 and create order
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['received'], True)
        self.assertIn('order_identifier', data)

        # Verify order was created
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.member, self.member)
        self.assertEqual(order.payment.stripe_payment_intent_id, 'pi_test_webhook_new')

        # Verify email was sent
        mock_email_send.assert_called_once()
