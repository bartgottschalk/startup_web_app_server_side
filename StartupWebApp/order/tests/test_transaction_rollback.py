# Unit tests for Transaction Rollback (HIGH-004 Phase 2)
# TDD RED phase - these tests should FAIL until Phase 3 implementation

from unittest.mock import patch, MagicMock
from decimal import Decimal

from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from order.models import (
    Cart, Cartsku, Cartshippingmethod, Cartdiscount,
    Product, Productsku, Productimage,
    Sku, Skuprice, Skutype, Skuinventory,
    Shippingmethod, Discountcode, Discounttype,
    Order, Orderpayment, Ordersku, Orderstatus, Ordershippingmethod,
    Orderbillingaddress, Ordershippingaddress, Orderdiscount,
    Status, Orderconfiguration
)
from user.models import Member, Termsofuse, Emailtype, Email, Emailstatus


class TransactionRollbackTest(PostgreSQLTestCase):
    """Test transaction rollback on order creation failures (HIGH-004)"""

    def setUp(self):
        """Set up test fixtures for transaction rollback tests"""
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
        self.order_status = Status.objects.create(
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

        # Create discount type and code
        discount_type = Discounttype.objects.create(
            title='Percentage Off',
            description='Percentage off entire order',
            applies_to='order',
            action='percentage_off'
        )

        now = timezone.now()
        self.discount_code = Discountcode.objects.create(
            code='SAVE10',
            description='10% off',
            start_date_time=now,
            end_date_time=now + timezone.timedelta(days=30),
            combinable=True,
            discounttype=discount_type,
            discount_amount=10.0,
            order_minimum=0.0
        )

        # Create cart with items for member
        self.cart = Cart.objects.create(member=self.member)
        Cartsku.objects.create(cart=self.cart, sku=self.sku, quantity=2)
        Cartshippingmethod.objects.create(
            cart=self.cart,
            shippingmethod=self.shipping_method
        )
        Cartdiscount.objects.create(
            cart=self.cart,
            discountcode=self.discount_code
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

    def _create_mock_stripe_session(self, cart_id, payment_intent_id='pi_test_123'):
        """Helper to create a mock Stripe session object"""
        mock_session = MagicMock()
        mock_session.id = 'cs_test_123'
        mock_session.payment_status = 'paid'
        mock_session.payment_intent = payment_intent_id
        mock_session.customer_email = 'test@test.com'
        mock_session.metadata = {'cart_id': str(cart_id)}

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

        return mock_session

    @patch('stripe.checkout.Session.retrieve')
    @patch('django.core.mail.EmailMultiAlternatives.send')
    def test_order_creation_success_all_objects_created(self, mock_email_send, mock_session_retrieve):
        """
        Test 16: Verify successful order creation creates all 9+ database objects.

        Expected objects:
        1. Orderpayment
        2. Ordershippingaddress
        3. Orderbillingaddress
        4. Order
        5. Ordersku(s) - one per cart item
        6. Orderdiscount(s) - one per discount code
        7. Orderstatus
        8. Ordershippingmethod
        9. Prospect (if anonymous checkout)

        This test should PASS even before Phase 3 implementation.
        """
        from order.views import handle_checkout_session_completed

        # Mock Stripe session retrieval
        mock_session = self._create_mock_stripe_session(self.cart.id)
        mock_session_retrieve.return_value = mock_session

        # Create webhook event
        event = {
            'data': {
                'object': {
                    'id': 'cs_test_123',
                    'payment_intent': 'pi_test_123',
                    'payment_status': 'paid',
                    'metadata': {'cart_id': str(self.cart.id)}
                }
            }
        }

        # Verify no objects exist before
        self.assertEqual(Orderpayment.objects.count(), 0)
        self.assertEqual(Ordershippingaddress.objects.count(), 0)
        self.assertEqual(Orderbillingaddress.objects.count(), 0)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Ordersku.objects.count(), 0)
        self.assertEqual(Orderdiscount.objects.count(), 0)
        self.assertEqual(Orderstatus.objects.count(), 0)
        self.assertEqual(Ordershippingmethod.objects.count(), 0)

        # Call handler
        response = handle_checkout_session_completed(event)

        # Verify response
        self.assertEqual(response.status_code, 200)

        # Verify all objects were created
        self.assertEqual(Orderpayment.objects.count(), 1, "Payment object not created")
        self.assertEqual(Ordershippingaddress.objects.count(), 1, "Shipping address not created")
        self.assertEqual(Orderbillingaddress.objects.count(), 1, "Billing address not created")
        self.assertEqual(Order.objects.count(), 1, "Order not created")
        self.assertEqual(Ordersku.objects.count(), 1, "Ordersku not created")
        self.assertEqual(Orderdiscount.objects.count(), 1, "Orderdiscount not created")
        self.assertEqual(Orderstatus.objects.count(), 1, "Orderstatus not created")
        self.assertEqual(Ordershippingmethod.objects.count(), 1, "Ordershippingmethod not created")

        # Verify relationships
        order = Order.objects.first()
        self.assertIsNotNone(order.payment)
        self.assertIsNotNone(order.shipping_address)
        self.assertIsNotNone(order.billing_address)
        self.assertEqual(order.ordersku_set.count(), 1)
        self.assertEqual(order.orderdiscount_set.count(), 1)
        self.assertEqual(order.orderstatus_set.count(), 1)
        self.assertEqual(order.ordershippingmethod_set.count(), 1)

        # Verify email was sent
        mock_email_send.assert_called_once()

    @patch('stripe.checkout.Session.retrieve')
    @patch('order.models.Orderpayment.objects.create')
    def test_payment_creation_fails_no_objects_created(self, mock_payment_create, mock_session_retrieve):
        """
        Test 17: Verify that if Payment creation fails, NO database objects are created.

        This tests atomicity at the very first step.
        Expected: FAIL (transaction rollback not implemented)
        """
        from order.views import handle_checkout_session_completed

        # Mock Stripe session retrieval
        mock_session = self._create_mock_stripe_session(self.cart.id, 'pi_test_payment_fail')
        mock_session_retrieve.return_value = mock_session

        # Mock payment creation to raise exception
        mock_payment_create.side_effect = Exception("Database error creating payment")

        # Create webhook event
        event = {
            'data': {
                'object': {
                    'id': 'cs_test_123',
                    'payment_intent': 'pi_test_payment_fail',
                    'payment_status': 'paid',
                    'metadata': {'cart_id': str(self.cart.id)}
                }
            }
        }

        # Call handler - should handle exception
        response = handle_checkout_session_completed(event)

        # Should return error response
        self.assertEqual(response.status_code, 500)

        # CRITICAL: Verify NO objects were created (rollback should occur)
        self.assertEqual(Orderpayment.objects.count(), 0, "Payment object should be rolled back")
        self.assertEqual(Ordershippingaddress.objects.count(), 0, "Shipping address should not exist")
        self.assertEqual(Orderbillingaddress.objects.count(), 0, "Billing address should not exist")
        self.assertEqual(Order.objects.count(), 0, "Order should not exist")
        self.assertEqual(Ordersku.objects.count(), 0, "Ordersku should not exist")
        self.assertEqual(Orderdiscount.objects.count(), 0, "Orderdiscount should not exist")
        self.assertEqual(Orderstatus.objects.count(), 0, "Orderstatus should not exist")
        self.assertEqual(Ordershippingmethod.objects.count(), 0, "Ordershippingmethod should not exist")

    @patch('stripe.checkout.Session.retrieve')
    @patch('order.models.Order.objects.create')
    def test_order_creation_fails_rollback_all(self, mock_order_create, mock_session_retrieve):
        """
        Test 18: Verify that if Order creation fails, Payment and Address objects are rolled back.

        Order is created AFTER Payment and Addresses, so they should all rollback.
        Expected: FAIL (transaction rollback not implemented)
        """
        from order.views import handle_checkout_session_completed

        # Mock Stripe session retrieval
        mock_session = self._create_mock_stripe_session(self.cart.id, 'pi_test_order_fail')
        mock_session_retrieve.return_value = mock_session

        # Mock order creation to raise exception
        mock_order_create.side_effect = Exception("Database error creating order")

        # Create webhook event
        event = {
            'data': {
                'object': {
                    'id': 'cs_test_123',
                    'payment_intent': 'pi_test_order_fail',
                    'payment_status': 'paid',
                    'metadata': {'cart_id': str(self.cart.id)}
                }
            }
        }

        # Call handler
        response = handle_checkout_session_completed(event)

        # Should return error response
        self.assertEqual(response.status_code, 500)

        # CRITICAL: Verify ALL objects were rolled back
        self.assertEqual(Orderpayment.objects.count(), 0, "Payment should be rolled back")
        self.assertEqual(Ordershippingaddress.objects.count(), 0, "Shipping address should be rolled back")
        self.assertEqual(Orderbillingaddress.objects.count(), 0, "Billing address should be rolled back")
        self.assertEqual(Order.objects.count(), 0, "Order should be rolled back")
        self.assertEqual(Ordersku.objects.count(), 0, "Ordersku should not exist")
        self.assertEqual(Orderdiscount.objects.count(), 0, "Orderdiscount should not exist")
        self.assertEqual(Orderstatus.objects.count(), 0, "Orderstatus should not exist")
        self.assertEqual(Ordershippingmethod.objects.count(), 0, "Ordershippingmethod should not exist")

    @patch('stripe.checkout.Session.retrieve')
    @patch('order.models.Ordersku.objects.create')
    def test_ordersku_creation_fails_rollback_all(self, mock_ordersku_create, mock_session_retrieve):
        """
        Test 19: Verify that if Ordersku creation fails, entire order creation is rolled back.

        Ordersku is created AFTER Order, Payment, and Addresses.
        Expected: FAIL (transaction rollback not implemented)
        """
        from order.views import handle_checkout_session_completed

        # Mock Stripe session retrieval
        mock_session = self._create_mock_stripe_session(self.cart.id, 'pi_test_ordersku_fail')
        mock_session_retrieve.return_value = mock_session

        # Mock ordersku creation to raise exception
        mock_ordersku_create.side_effect = Exception("Database error creating ordersku")

        # Create webhook event
        event = {
            'data': {
                'object': {
                    'id': 'cs_test_123',
                    'payment_intent': 'pi_test_ordersku_fail',
                    'payment_status': 'paid',
                    'metadata': {'cart_id': str(self.cart.id)}
                }
            }
        }

        # Call handler
        response = handle_checkout_session_completed(event)

        # Should return error response
        self.assertEqual(response.status_code, 500)

        # CRITICAL: Verify entire order creation was rolled back
        self.assertEqual(Orderpayment.objects.count(), 0, "Payment should be rolled back")
        self.assertEqual(Ordershippingaddress.objects.count(), 0, "Shipping address should be rolled back")
        self.assertEqual(Orderbillingaddress.objects.count(), 0, "Billing address should be rolled back")
        self.assertEqual(Order.objects.count(), 0, "Order should be rolled back")
        self.assertEqual(Ordersku.objects.count(), 0, "Ordersku should be rolled back")
        self.assertEqual(Orderdiscount.objects.count(), 0, "Orderdiscount should not exist")
        self.assertEqual(Orderstatus.objects.count(), 0, "Orderstatus should not exist")
        self.assertEqual(Ordershippingmethod.objects.count(), 0, "Ordershippingmethod should not exist")

    @patch('stripe.checkout.Session.retrieve')
    @patch('order.models.Orderstatus.objects.create')
    def test_orderstatus_creation_fails_rollback_all(self, mock_orderstatus_create, mock_session_retrieve):
        """
        Test 20: Verify that if Orderstatus creation fails, entire order creation is rolled back.

        Orderstatus is created near the end, after most other objects.
        Expected: FAIL (transaction rollback not implemented)
        """
        from order.views import handle_checkout_session_completed

        # Mock Stripe session retrieval
        mock_session = self._create_mock_stripe_session(self.cart.id, 'pi_test_orderstatus_fail')
        mock_session_retrieve.return_value = mock_session

        # Mock orderstatus creation to raise exception
        mock_orderstatus_create.side_effect = Exception("Database error creating orderstatus")

        # Create webhook event
        event = {
            'data': {
                'object': {
                    'id': 'cs_test_123',
                    'payment_intent': 'pi_test_orderstatus_fail',
                    'payment_status': 'paid',
                    'metadata': {'cart_id': str(self.cart.id)}
                }
            }
        }

        # Call handler
        response = handle_checkout_session_completed(event)

        # Should return error response
        self.assertEqual(response.status_code, 500)

        # CRITICAL: Verify entire order creation was rolled back
        self.assertEqual(Orderpayment.objects.count(), 0, "Payment should be rolled back")
        self.assertEqual(Ordershippingaddress.objects.count(), 0, "Shipping address should be rolled back")
        self.assertEqual(Orderbillingaddress.objects.count(), 0, "Billing address should be rolled back")
        self.assertEqual(Order.objects.count(), 0, "Order should be rolled back")
        self.assertEqual(Ordersku.objects.count(), 0, "Ordersku should be rolled back")
        self.assertEqual(Orderdiscount.objects.count(), 0, "Orderdiscount should be rolled back")
        self.assertEqual(Orderstatus.objects.count(), 0, "Orderstatus should be rolled back")
        self.assertEqual(Ordershippingmethod.objects.count(), 0, "Ordershippingmethod should not exist")
