# Unit tests for Email Failure Handling (HIGH-004 Phase 2)
# TDD RED phase - these tests should FAIL until Phase 3 implementation

from unittest.mock import patch, MagicMock
from decimal import Decimal
from smtplib import SMTPException

from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from order.models import (
    Cart, Cartsku, Cartshippingmethod, Cartdiscount,
    Product, Productsku, Productimage,
    Sku, Skuprice, Skutype, Skuinventory,
    Shippingmethod, Discountcode, Discounttype,
    Order, Orderpayment, Ordersku, Orderstatus, Ordershippingmethod,
    Orderbillingaddress, Ordershippingaddress,
    Orderemailfailure,
    Status, Orderconfiguration
)
from user.models import Member, Termsofuse, Emailtype, Email, Emailstatus


class EmailFailureHandlingTest(PostgreSQLTestCase):
    """Test email failure handling during order creation (HIGH-004)"""

    def setUp(self):
        """Set up test fixtures for email failure handling tests"""
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

        self.email_member = Email.objects.create(
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
    @patch('user.models.Email.objects.get')
    def test_email_template_missing_order_still_saved(self, mock_email_get, mock_session_retrieve):
        """
        Test 21: Email template lookup fails, but order is still saved successfully.

        Scenario: Email.objects.get() raises DoesNotExist
        Expected behavior:
        - Order and all related objects ARE created and saved
        - Orderemailfailure record IS created with failure_type='template_lookup'
        - Response is HTTP 200 (success)
        - Cart IS deleted (order saved, consistent with existing checkout flow)

        Expected: FAIL (email failure handling not implemented)
        """
        from order.views import handle_checkout_session_completed

        # Mock Stripe session retrieval
        mock_session = self._create_mock_stripe_session(self.cart.id, 'pi_test_email_template_fail')
        mock_session_retrieve.return_value = mock_session

        # Mock email template lookup to raise DoesNotExist
        mock_email_get.side_effect = Email.DoesNotExist("Email template not found")

        # Create webhook event
        event = {
            'data': {
                'object': {
                    'id': 'cs_test_123',
                    'payment_intent': 'pi_test_email_template_fail',
                    'payment_status': 'paid',
                    'metadata': {'cart_id': str(self.cart.id)}
                }
            }
        }

        # Verify no order exists before
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Orderemailfailure.objects.count(), 0)

        # Call handler
        response = handle_checkout_session_completed(event)

        # CRITICAL: Should return 200 (order saved successfully despite email failure)
        self.assertEqual(response.status_code, 200, "Should return 200 even when email fails")

        # CRITICAL: Verify order WAS created and saved
        self.assertEqual(Order.objects.count(), 1, "Order should be saved despite email failure")
        self.assertEqual(Orderpayment.objects.count(), 1, "Payment should be saved")
        self.assertEqual(Ordershippingaddress.objects.count(), 1, "Shipping address should be saved")
        self.assertEqual(Orderbillingaddress.objects.count(), 1, "Billing address should be saved")
        self.assertEqual(Ordersku.objects.count(), 1, "Ordersku should be saved")
        self.assertEqual(Orderstatus.objects.count(), 1, "Orderstatus should be saved")
        self.assertEqual(Ordershippingmethod.objects.count(), 1, "Ordershippingmethod should be saved")

        # CRITICAL: Verify Orderemailfailure record was created
        self.assertEqual(Orderemailfailure.objects.count(), 1, "Orderemailfailure record should be created")

        failure_record = Orderemailfailure.objects.first()
        self.assertEqual(failure_record.failure_type, 'template_lookup', "Failure type should be template_lookup")
        self.assertEqual(failure_record.order, Order.objects.first(), "Should link to created order")
        self.assertEqual(failure_record.customer_email, 'test@test.com', "Should record customer email")
        self.assertTrue(failure_record.is_member_order, "Should be marked as member order")
        self.assertFalse(failure_record.resolved, "Should not be resolved")
        self.assertIn('Email template not found', failure_record.error_message, "Should record error message")

        # CRITICAL: Cart SHOULD be deleted (order saved successfully, consistent with existing checkout flow)
        self.assertEqual(
            Cart.objects.filter(id=self.cart.id).count(), 0,
            "Cart should be deleted even when email fails"
        )

    @patch('stripe.checkout.Session.retrieve')
    @patch('user.models.Email.objects.get')
    def test_email_formatting_fails_order_still_saved(self, mock_email_get, mock_session_retrieve):
        """
        Test 22: Email formatting fails, but order is still saved successfully.

        Scenario: Email body formatting raises exception (e.g., missing template variable)
        Expected behavior:
        - Order and all related objects ARE created and saved
        - Orderemailfailure record IS created with failure_type='formatting'
        - Response is HTTP 200 (success)
        - Cart IS deleted (order saved, consistent with existing checkout flow)

        Expected: FAIL (email failure handling not implemented)
        """
        from order.views import handle_checkout_session_completed

        # Mock Stripe session retrieval
        mock_session = self._create_mock_stripe_session(self.cart.id, 'pi_test_email_format_fail')
        mock_session_retrieve.return_value = mock_session

        # Return valid email template
        mock_email_get.return_value = self.email_member

        # Mock email formatting to raise KeyError (missing template variable)
        with patch('order.views.send_order_confirmation_email') as mock_send_email:
            mock_send_email.side_effect = KeyError("Missing template variable")

            # Create webhook event
            event = {
                'data': {
                    'object': {
                        'id': 'cs_test_123',
                        'payment_intent': 'pi_test_email_format_fail',
                        'payment_status': 'paid',
                        'metadata': {'cart_id': str(self.cart.id)}
                    }
                }
            }

            # Verify no order exists before
            self.assertEqual(Order.objects.count(), 0)
            self.assertEqual(Orderemailfailure.objects.count(), 0)

            # Call handler
            response = handle_checkout_session_completed(event)

            # CRITICAL: Should return 200 (order saved successfully despite email failure)
            self.assertEqual(response.status_code, 200, "Should return 200 even when email formatting fails")

            # CRITICAL: Verify order WAS created and saved
            self.assertEqual(Order.objects.count(), 1, "Order should be saved despite email formatting failure")
            self.assertEqual(Orderpayment.objects.count(), 1, "Payment should be saved")

            # CRITICAL: Verify Orderemailfailure record was created
            self.assertEqual(Orderemailfailure.objects.count(), 1, "Orderemailfailure record should be created")

            failure_record = Orderemailfailure.objects.first()
            self.assertEqual(failure_record.failure_type, 'formatting', "Failure type should be formatting")
            self.assertEqual(failure_record.order, Order.objects.first(), "Should link to created order")
            self.assertEqual(failure_record.customer_email, 'test@test.com', "Should record customer email")
            self.assertFalse(failure_record.resolved, "Should not be resolved")

            # CRITICAL: Cart SHOULD be deleted (order saved successfully, consistent with existing checkout flow)
            self.assertEqual(
                Cart.objects.filter(id=self.cart.id).count(), 0,
                "Cart should be deleted even when email fails"
            )

    @patch('stripe.checkout.Session.retrieve')
    @patch('django.core.mail.EmailMultiAlternatives.send')
    def test_smtp_send_fails_order_still_saved(self, mock_email_send, mock_session_retrieve):
        """
        Test 23: SMTP send fails, but order is still saved successfully.

        Scenario: EmailMultiAlternatives.send() raises SMTPException
        Expected behavior:
        - Order and all related objects ARE created and saved
        - Orderemailfailure record IS created with failure_type='smtp_send'
        - Response is HTTP 200 (success)
        - Cart IS deleted (order saved, consistent with existing checkout flow)

        Expected: FAIL (email failure handling not implemented)
        """
        from order.views import handle_checkout_session_completed

        # Mock Stripe session retrieval
        mock_session = self._create_mock_stripe_session(self.cart.id, 'pi_test_smtp_fail')
        mock_session_retrieve.return_value = mock_session

        # Mock SMTP send to raise SMTPException
        mock_email_send.side_effect = SMTPException("SMTP server connection failed")

        # Create webhook event
        event = {
            'data': {
                'object': {
                    'id': 'cs_test_123',
                    'payment_intent': 'pi_test_smtp_fail',
                    'payment_status': 'paid',
                    'metadata': {'cart_id': str(self.cart.id)}
                }
            }
        }

        # Verify no order exists before
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Orderemailfailure.objects.count(), 0)

        # Call handler
        response = handle_checkout_session_completed(event)

        # CRITICAL: Should return 200 (order saved successfully despite SMTP failure)
        self.assertEqual(response.status_code, 200, "Should return 200 even when SMTP send fails")

        # CRITICAL: Verify order WAS created and saved
        self.assertEqual(Order.objects.count(), 1, "Order should be saved despite SMTP failure")
        self.assertEqual(Orderpayment.objects.count(), 1, "Payment should be saved")
        self.assertEqual(Ordershippingaddress.objects.count(), 1, "Shipping address should be saved")
        self.assertEqual(Orderbillingaddress.objects.count(), 1, "Billing address should be saved")
        self.assertEqual(Ordersku.objects.count(), 1, "Ordersku should be saved")
        self.assertEqual(Orderstatus.objects.count(), 1, "Orderstatus should be saved")
        self.assertEqual(Ordershippingmethod.objects.count(), 1, "Ordershippingmethod should be saved")

        # CRITICAL: Verify Orderemailfailure record was created
        self.assertEqual(Orderemailfailure.objects.count(), 1, "Orderemailfailure record should be created")

        failure_record = Orderemailfailure.objects.first()
        self.assertEqual(failure_record.failure_type, 'smtp_send', "Failure type should be smtp_send")
        self.assertEqual(failure_record.order, Order.objects.first(), "Should link to created order")
        self.assertEqual(failure_record.customer_email, 'test@test.com', "Should record customer email")
        self.assertTrue(failure_record.is_member_order, "Should be marked as member order")
        self.assertFalse(failure_record.resolved, "Should not be resolved")
        self.assertIn('SMTP server connection failed', failure_record.error_message, "Should record error message")

        # CRITICAL: Cart SHOULD be deleted (order saved successfully, consistent with existing checkout flow)
        self.assertEqual(Cart.objects.filter(id=self.cart.id).count(), 0, "Cart should be deleted even when SMTP fails")

    @patch('stripe.checkout.Session.retrieve')
    @patch('django.core.mail.EmailMultiAlternatives.send')
    def test_cart_deleted_when_email_succeeds(self, mock_email_send, mock_session_retrieve):
        """
        Test 24: Verify cart IS deleted when email SUCCEEDS.

        This is the baseline/control test to prove cart deletion happens regardless of email status.
        Compare with tests 21-23 which verify cart is deleted even when email FAILS.
        """
        from order.views import handle_checkout_session_completed

        # Mock Stripe session retrieval
        mock_session = self._create_mock_stripe_session(self.cart.id, 'pi_test_email_success')
        mock_session_retrieve.return_value = mock_session

        # Mock email send to succeed (no exception)
        mock_email_send.return_value = 1

        # Create webhook event
        event = {
            'data': {
                'object': {
                    'id': 'cs_test_123',
                    'payment_intent': 'pi_test_email_success',
                    'payment_status': 'paid',
                    'metadata': {'cart_id': str(self.cart.id)}
                }
            }
        }

        # Store cart ID before handler runs
        cart_id_before = self.cart.id

        # Verify cart exists before
        self.assertEqual(Cart.objects.filter(id=cart_id_before).count(), 1, "Cart should exist before handler")

        # Call handler
        response = handle_checkout_session_completed(event)

        # Should return 200 (success)
        self.assertEqual(response.status_code, 200, "Should return 200 when email succeeds")

        # Verify order was created
        self.assertEqual(Order.objects.count(), 1, "Order should be created")

        # CRITICAL: Cart SHOULD be deleted when email succeeds
        self.assertEqual(
            Cart.objects.filter(id=cart_id_before).count(), 0,
            "Cart should be deleted when email succeeds"
        )

        # No email failure record should exist
        self.assertEqual(Orderemailfailure.objects.count(), 0, "No email failure record when email succeeds")

        # Email should have been sent
        mock_email_send.assert_called_once()
