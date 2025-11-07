# Unit tests for payment processing and order placement endpoints

import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from order.models import (
    Cart, Cartsku, Cartpayment, Cartshippingaddress,
    Product, Productsku, Productimage,
    Sku, Skuprice, Skutype, Skuinventory,
    Orderconfiguration
)
from user.models import Member, Prospect, Termsofuse

from StartupWebApp.utilities import unittest_utilities


class AnonymousEmailAddressPaymentLookupEndpointTest(TestCase):
    """Test the anonymous_email_address_payment_lookup endpoint"""

    def setUp(self):
        # Create order configuration for checkout
        Orderconfiguration.objects.create(
            key='usernames_allowed_to_checkout',
            string_value='*'
        )

        Orderconfiguration.objects.create(
            key='an_ct_values_allowed_to_checkout',
            string_value='*'
        )

        # Create existing member with email
        Group.objects.create(name='Members')
        Termsofuse.objects.create(
            version='1',
            version_note='Test',
            publication_date_time=timezone.now()
        )

        self.user = User.objects.create_user(
            username='existinguser',
            email='existing@test.com',
            password='testpass123'
        )
        self.member = Member.objects.create(user=self.user, mb_cd='MEMBER123')

        # Create existing prospect
        self.prospect = Prospect.objects.create(
            email='prospect@test.com',
            pr_cd='PROSPECT456',
            created_date_time=timezone.now()
        )

    def test_anonymous_email_address_payment_lookup_when_checkout_not_allowed(self):
        """Test that endpoint requires checkout permission"""
        config = Orderconfiguration.objects.get(
            key='an_ct_values_allowed_to_checkout'
        )
        config.string_value = ''
        config.save()

        response = self.client.post('/order/anonymous-email-address-payment-lookup', {
            'anonymous_email_address': 'test@test.com'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertFalse(data['checkout_allowed'])

    def test_anonymous_email_address_payment_lookup_without_email(self):
        """Test error when email address is missing"""
        response = self.client.post('/order/anonymous-email-address-payment-lookup', {})

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['anonymous_email_address_payment_lookup'], 'error')
        self.assertEqual(data['errors']['error'], 'anonymous-email-address-required')

    def test_anonymous_email_address_payment_lookup_with_member_email(self):
        """Test error when email is already associated with member"""
        response = self.client.post('/order/anonymous-email-address-payment-lookup', {
            'anonymous_email_address': 'existing@test.com'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['anonymous_email_address_payment_lookup'], 'error')
        self.assertEqual(data['errors']['error'], 'email-address-is-associated-with-member')
        self.assertIn('login', data['errors']['description'])

    def test_anonymous_email_address_payment_lookup_with_existing_prospect(self):
        """Test success when email is already a prospect"""
        response = self.client.post('/order/anonymous-email-address-payment-lookup', {
            'anonymous_email_address': 'prospect@test.com'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['anonymous_email_address_payment_lookup'], 'success')
        self.assertIn('stripe_publishable_key', data)

    def test_anonymous_email_address_payment_lookup_creates_new_prospect(self):
        """Test that new prospect is created for new email"""
        self.assertEqual(Prospect.objects.filter(email='newuser@test.com').count(), 0)

        response = self.client.post('/order/anonymous-email-address-payment-lookup', {
            'anonymous_email_address': 'newuser@test.com'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['anonymous_email_address_payment_lookup'], 'success')

        # Verify prospect was created
        self.assertEqual(Prospect.objects.filter(email='newuser@test.com').count(), 1)
        prospect = Prospect.objects.get(email='newuser@test.com')
        self.assertTrue(prospect.email_unsubscribed)  # Default to unsubscribed
        self.assertIsNotNone(prospect.pr_cd)
        self.assertIsNotNone(prospect.email_unsubscribe_string)


class ChangeConfirmationEmailAddressEndpointTest(TestCase):
    """Test the change_confirmation_email_address endpoint"""

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

        # Create order configuration for checkout
        Orderconfiguration.objects.create(
            key='usernames_allowed_to_checkout',
            string_value='*'
        )

        Orderconfiguration.objects.create(
            key='an_ct_values_allowed_to_checkout',
            string_value='*'
        )

        # Create cart with payment and shipping
        self.cart = Cart.objects.create(member=self.member)

        self.cart_payment = Cartpayment.objects.create(
            stripe_customer_token='cus_test123',
            stripe_card_id='card_test456',
            email='test@test.com'
        )
        self.cart.payment = self.cart_payment

        self.cart_shipping = Cartshippingaddress.objects.create(
            name='Test User',
            address_line1='123 Main St',
            city='Anytown',
            state='CA',
            zip='12345'
        )
        self.cart.shipping_address = self.cart_shipping
        self.cart.save()

    def test_change_confirmation_email_address_when_checkout_not_allowed(self):
        """Test that endpoint requires checkout permission"""
        config = Orderconfiguration.objects.get(
            key='usernames_allowed_to_checkout'
        )
        config.string_value = ''
        config.save()

        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/change-confirmation-email-address', {})

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertFalse(data['checkout_allowed'])

    def test_change_confirmation_email_address_clears_cart_payment(self):
        """Test that changing email clears cart payment"""
        self.client.login(username='testuser', password='testpass123')

        self.assertIsNotNone(self.cart.payment)
        self.assertIsNotNone(self.cart.shipping_address)

        response = self.client.post('/order/change-confirmation-email-address', {})

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['change_confirmation_email_address'], 'success')

        # Verify payment and shipping were cleared
        self.cart.refresh_from_db()
        self.assertIsNone(self.cart.payment)
        self.assertIsNone(self.cart.shipping_address)


class ProcessStripePaymentTokenEndpointTest(TestCase):
    """Test the process_stripe_payment_token endpoint (simplified - no Stripe API mocking)"""

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

        # Create order configuration for checkout
        Orderconfiguration.objects.create(
            key='usernames_allowed_to_checkout',
            string_value='*'
        )

        Orderconfiguration.objects.create(
            key='an_ct_values_allowed_to_checkout',
            string_value='*'
        )

        # Create cart
        self.cart = Cart.objects.create(member=self.member)

    def test_process_stripe_payment_token_when_checkout_not_allowed(self):
        """Test that endpoint requires checkout permission"""
        config = Orderconfiguration.objects.get(
            key='usernames_allowed_to_checkout'
        )
        config.string_value = ''
        config.save()

        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/process-stripe-payment-token', {
            'stripe_token': 'tok_test123',
            'email': 'test@test.com',
            'stripe_payment_args': json.dumps({
                'shipping_name': 'Test User',
                'shipping_address_line1': '123 Main St',
                'shipping_address_city': 'Anytown',
                'shipping_address_zip': '12345',
                'shipping_address_country': 'United States',
                'shipping_address_country_code': 'US'
            })
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertFalse(data['checkout_allowed'])

    def test_process_stripe_payment_token_without_token(self):
        """Test error when stripe_token is missing"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/process-stripe-payment-token', {
            'email': 'test@test.com',
            'stripe_payment_args': json.dumps({})
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['process_stripe_payment_token'], 'error')
        self.assertEqual(data['errors']['error'], 'stripe-token-required')

    def test_process_stripe_payment_token_first_payment_authenticated_user(self):
        """Test creating first Stripe customer and cart payment for authenticated user"""
        from unittest.mock import patch, MagicMock

        with patch('order.utilities.order_utils.create_stripe_customer') as mock_create_customer:
            # Mock Stripe customer creation
            mock_customer = MagicMock()
            mock_customer.id = 'cus_test_authenticated'
            mock_customer.default_source = 'card_test123'
            mock_create_customer.return_value = mock_customer

            self.client.login(username='testuser', password='testpass123')

            response = self.client.post('/order/process-stripe-payment-token', {
                'stripe_token': 'tok_test123',
                'email': 'test@test.com',
                'stripe_payment_args': json.dumps({
                    'shipping_name': 'Test User',
                    'shipping_address_line1': '123 Main St',
                    'shipping_address_city': 'Anytown',
                    'shipping_address_state': 'CA',
                    'shipping_address_zip': '12345',
                    'shipping_address_country': 'United States',
                    'shipping_address_country_code': 'US'
                })
            })

            unittest_utilities.validate_response_is_OK_and_JSON(self, response)

            data = json.loads(response.content.decode('utf8'))
            self.assertEqual(data['process_stripe_payment_token'], 'success')

            # Verify Stripe customer was created with correct parameters
            mock_create_customer.assert_called_once_with(
                'tok_test123', 'test@test.com', 'member_username', 'testuser'
            )

            # Verify cart payment was created
            self.cart.refresh_from_db()
            self.assertIsNotNone(self.cart.payment)
            self.assertEqual(self.cart.payment.stripe_customer_token, 'cus_test_authenticated')
            self.assertEqual(self.cart.payment.stripe_card_id, 'card_test123')
            self.assertEqual(self.cart.payment.email, 'test@test.com')

            # Verify shipping address was created
            self.assertIsNotNone(self.cart.shipping_address)
            self.assertEqual(self.cart.shipping_address.name, 'Test User')
            self.assertEqual(self.cart.shipping_address.address_line1, '123 Main St')
            self.assertEqual(self.cart.shipping_address.city, 'Anytown')
            self.assertEqual(self.cart.shipping_address.state, 'CA')

    def test_process_stripe_payment_token_first_payment_anonymous_user(self):
        """Test creating first Stripe customer for anonymous user"""
        from unittest.mock import patch, MagicMock

        with patch('order.utilities.order_utils.create_stripe_customer') as mock_create_customer, \
             patch('order.utilities.order_utils.look_up_cart') as mock_look_up_cart:

            # Mock Stripe customer creation
            mock_customer = MagicMock()
            mock_customer.id = 'cus_test_anonymous'
            mock_customer.default_source = 'card_test456'
            mock_create_customer.return_value = mock_customer

            # Create anonymous cart
            anon_cart = Cart.objects.create(anonymous_cart_id='anon_123')
            mock_look_up_cart.return_value = anon_cart

            response = self.client.post('/order/process-stripe-payment-token', {
                'stripe_token': 'tok_anon_test',
                'email': 'anonymous@test.com',
                'stripe_payment_args': json.dumps({
                    'shipping_name': 'Anonymous User',
                    'shipping_address_line1': '456 Oak Ave',
                    'shipping_address_city': 'Somewhere',
                    'shipping_address_zip': '54321',
                    'shipping_address_country': 'United States',
                    'shipping_address_country_code': 'US'
                })
            })

            unittest_utilities.validate_response_is_OK_and_JSON(self, response)

            data = json.loads(response.content.decode('utf8'))
            self.assertEqual(data['process_stripe_payment_token'], 'success')

            # Verify Stripe customer was created for anonymous user (prospect)
            mock_create_customer.assert_called_once_with(
                'tok_anon_test', 'anonymous@test.com', 'prospect_email_addr', 'anonymous@test.com'
            )

            # Verify cart payment was created
            anon_cart.refresh_from_db()
            self.assertIsNotNone(anon_cart.payment)
            self.assertEqual(anon_cart.payment.stripe_customer_token, 'cus_test_anonymous')

    def test_process_stripe_payment_token_add_card_to_existing_customer(self):
        """Test adding a new card to existing customer payment"""
        from unittest.mock import patch, MagicMock
        from order.models import Cartpayment

        # Create existing cart payment
        existing_payment = Cartpayment.objects.create(
            stripe_customer_token='cus_existing',
            stripe_card_id='card_old',
            email='test@test.com'
        )
        self.cart.payment = existing_payment
        self.cart.save()

        with patch('order.utilities.order_utils.stripe_customer_add_card') as mock_add_card:
            # Mock adding new card
            mock_card = MagicMock()
            mock_card.id = 'card_new123'
            mock_add_card.return_value = mock_card

            self.client.login(username='testuser', password='testpass123')

            response = self.client.post('/order/process-stripe-payment-token', {
                'stripe_token': 'tok_new_card',
                'email': 'test@test.com',
                'stripe_payment_args': json.dumps({
                    'shipping_name': 'Test User',
                    'shipping_address_line1': '123 Main St',
                    'shipping_address_city': 'Anytown',
                    'shipping_address_zip': '12345',
                    'shipping_address_country': 'United States',
                    'shipping_address_country_code': 'US'
                })
            })

            unittest_utilities.validate_response_is_OK_and_JSON(self, response)

            data = json.loads(response.content.decode('utf8'))
            self.assertEqual(data['process_stripe_payment_token'], 'success')

            # Verify card was added to existing customer
            mock_add_card.assert_called_once_with('cus_existing', 'tok_new_card')

            # Verify cart payment was updated with new card
            self.cart.refresh_from_db()
            self.assertEqual(self.cart.payment.stripe_card_id, 'card_new123')
            # Customer token should remain the same
            self.assertEqual(self.cart.payment.stripe_customer_token, 'cus_existing')

    def test_process_stripe_payment_token_update_existing_shipping_address(self):
        """Test updating existing cart shipping address"""
        from unittest.mock import patch, MagicMock
        from order.models import Cartshippingaddress

        # Create existing shipping address
        existing_address = Cartshippingaddress.objects.create(
            name='Old Name',
            address_line1='Old Address',
            city='Old City',
            state='CA',
            zip='11111',
            country='United States',
            country_code='US'
        )
        self.cart.shipping_address = existing_address
        self.cart.save()

        with patch('order.utilities.order_utils.create_stripe_customer') as mock_create_customer:
            mock_customer = MagicMock()
            mock_customer.id = 'cus_test'
            mock_customer.default_source = 'card_test'
            mock_create_customer.return_value = mock_customer

            self.client.login(username='testuser', password='testpass123')

            response = self.client.post('/order/process-stripe-payment-token', {
                'stripe_token': 'tok_test',
                'email': 'test@test.com',
                'stripe_payment_args': json.dumps({
                    'shipping_name': 'Updated Name',
                    'shipping_address_line1': 'Updated Address',
                    'shipping_address_city': 'Updated City',
                    'shipping_address_state': 'NY',
                    'shipping_address_zip': '99999',
                    'shipping_address_country': 'United States',
                    'shipping_address_country_code': 'US'
                })
            })

            unittest_utilities.validate_response_is_OK_and_JSON(self, response)

            data = json.loads(response.content.decode('utf8'))
            self.assertEqual(data['process_stripe_payment_token'], 'success')

            # Verify existing address was updated (not replaced)
            self.cart.refresh_from_db()
            self.assertEqual(self.cart.shipping_address.id, existing_address.id)
            self.assertEqual(self.cart.shipping_address.name, 'Updated Name')
            self.assertEqual(self.cart.shipping_address.address_line1, 'Updated Address')
            self.assertEqual(self.cart.shipping_address.city, 'Updated City')
            self.assertEqual(self.cart.shipping_address.state, 'NY')
            self.assertEqual(self.cart.shipping_address.zip, '99999')

    def test_process_stripe_payment_token_stripe_error_handling(self):
        """Test Stripe error handling (CardError, etc.)"""
        from unittest.mock import patch
        import stripe

        with patch('order.utilities.order_utils.create_stripe_customer') as mock_create_customer:
            # Mock Stripe error
            error_body = {'error': {'type': 'card_error', 'code': 'card_declined', 'message': 'Your card was declined.'}}
            mock_create_customer.side_effect = stripe.error.CardError(
                'Card declined', 'card', 'card_declined', http_status=402, json_body=error_body
            )

            self.client.login(username='testuser', password='testpass123')

            response = self.client.post('/order/process-stripe-payment-token', {
                'stripe_token': 'tok_invalid',
                'email': 'test@test.com',
                'stripe_payment_args': json.dumps({
                    'shipping_name': 'Test User',
                    'shipping_address_line1': '123 Main St',
                    'shipping_address_city': 'Anytown',
                    'shipping_address_zip': '12345',
                    'shipping_address_country': 'United States',
                    'shipping_address_country_code': 'US'
                })
            })

            unittest_utilities.validate_response_is_OK_and_JSON(self, response)

            data = json.loads(response.content.decode('utf8'))
            self.assertEqual(data['process_stripe_payment_token'], 'error')
            self.assertEqual(data['errors']['error'], 'error-creating-stripe-customer')


class ConfirmPlaceOrderEndpointTest(TestCase):
    """Test the confirm_place_order endpoint (simplified - no actual order creation)"""

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

        # Create order configuration for checkout
        Orderconfiguration.objects.create(
            key='usernames_allowed_to_checkout',
            string_value='*'
        )

        Orderconfiguration.objects.create(
            key='an_ct_values_allowed_to_checkout',
            string_value='*'
        )

        # Create order status and shipping configurations
        from order.models import Status, Shippingmethod

        status = Status.objects.create(
            identifier='processing',
            title='Processing',
            description='Order is being processed'
        )

        shipping_method = Shippingmethod.objects.create(
            identifier='standard',
            carrier='USPS',
            shipping_cost=5.00,
            tracking_code_base_url='https://tools.usps.com/go/TrackConfirmAction?tLabels='
        )

        Orderconfiguration.objects.create(
            key='initial_order_status',
            string_value='processing'
        )

        Orderconfiguration.objects.create(
            key='default_shipping_method',
            string_value='standard'
        )

        Orderconfiguration.objects.create(
            key='order_confirmation_em_cd_member',
            string_value='order_confirmation_member'
        )

        Orderconfiguration.objects.create(
            key='order_confirmation_em_cd_prospect',
            string_value='order_confirmation_prospect'
        )

        # Create product and SKU data for cart
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
            sku_inventory=skuinventory,
            description='Test SKU'
        )

        Skuprice.objects.create(
            sku=self.sku,
            price=25.00,
            created_date_time=timezone.now()
        )

        Productsku.objects.create(product=product, sku=self.sku)

        # Create cart payment
        self.cart_payment = Cartpayment.objects.create(
            stripe_customer_token='cus_test123',
            stripe_card_id='card_test456'
        )

        # Create cart with items and link payment
        self.cart = Cart.objects.create(
            member=self.member,
            payment=self.cart_payment
        )
        Cartsku.objects.create(cart=self.cart, sku=self.sku, quantity=2)

        # Create cart shipping method
        from order.models import Cartshippingmethod
        Cartshippingmethod.objects.create(
            cart=self.cart,
            shippingmethod=shipping_method
        )

    def test_confirm_place_order_when_checkout_not_allowed(self):
        """Test that endpoint requires checkout permission"""
        config = Orderconfiguration.objects.get(
            key='usernames_allowed_to_checkout'
        )
        config.string_value = ''
        config.save()

        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/confirm-place-order', {
            'agree_to_terms_of_sale': 'true'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertFalse(data['checkout_allowed'])

    def test_confirm_place_order_without_terms_agreement(self):
        """Test error when terms of sale not provided"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/confirm-place-order', {
            'stripe_payment_info': json.dumps({}),
            'stripe_shipping_addr': json.dumps({}),
            'stripe_billing_addr': json.dumps({})
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['confirm_place_order'], 'error')
        self.assertEqual(data['errors']['error'], 'agree-to-terms-of-sale-required')

    def test_confirm_place_order_with_false_terms_agreement(self):
        """Test error when terms of sale not agreed to"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/confirm-place-order', {
            'agree_to_terms_of_sale': 'false',
            'stripe_payment_info': json.dumps({}),
            'stripe_shipping_addr': json.dumps({}),
            'stripe_billing_addr': json.dumps({})
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['confirm_place_order'], 'error')
        self.assertEqual(data['errors']['error'],
                        'agree-to-terms-of-sale-must-be-checked')

    def test_confirm_place_order_when_no_cart(self):
        """Test error when cart doesn't exist"""
        self.cart.delete()

        self.client.login(username='testuser', password='testpass123')

        response = self.client.post('/order/confirm-place-order', {
            'agree_to_terms_of_sale': 'true',
            'stripe_payment_info': json.dumps({
                'email': 'test@test.com',
                'payment_type': 'card',
                'card_name': 'Test User',
                'card_brand': 'Visa',
                'card_last4': '4242',
                'card_exp_month': '12',
                'card_exp_year': '2025',
                'card_zip': '12345'
            }),
            'stripe_shipping_addr': json.dumps({
                'name': 'Test User',
                'address_line1': '123 Main St',
                'address_city': 'Anytown',
                'address_state': 'CA',
                'address_zip': '12345',
                'address_country': 'United States',
                'address_country_code': 'US'
            }),
            'stripe_billing_addr': json.dumps({
                'name': 'Test User',
                'address_line1': '123 Main St',
                'address_city': 'Anytown',
                'address_state': 'CA',
                'address_zip': '12345',
                'address_country': 'United States',
                'address_country_code': 'US'
            })
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(data['confirm_place_order'], 'error')
        self.assertEqual(data['errors']['error'], 'cart-not-found')

    def test_confirm_place_order_success_authenticated_user(self):
        """Test successful order placement for authenticated user"""
        from order.models import Order, Orderpayment, Ordershippingaddress, Orderbillingaddress
        from unittest.mock import patch, MagicMock

        # Mock email sending to avoid needing Email templates
        with patch('user.models.Email.objects.get') as mock_email_get, \
             patch('user.models.Emailtype.objects.get') as mock_emailtype_get:

            mock_email = MagicMock()
            mock_email.subject = 'Order Confirmation'
            mock_email.body_html = '<p>Thank you for your order</p>'
            mock_email.body_text = 'Thank you for your order. Order info: {order_information}'
            mock_email.from_address = 'noreply@test.com'
            mock_email.bcc_address = ''
            mock_email.em_cd = 'order_confirmation_member'
            # Create a mock email_type that won't match any comparisons
            mock_email.email_type = MagicMock()
            mock_email.email_type.id = 999  # Unique ID that won't match
            mock_email_get.return_value = mock_email

            # Mock Emailtype lookups to return distinct objects
            def emailtype_side_effect(title):
                mock_type = MagicMock()
                mock_type.title = title
                mock_type.id = hash(title)  # Different ID for each type
                return mock_type
            mock_emailtype_get.side_effect = emailtype_side_effect

            with patch('django.core.mail.EmailMultiAlternatives.send') as mock_send_email:
                self.client.login(username='testuser', password='testpass123')

                response = self.client.post('/order/confirm-place-order', {
                    'agree_to_terms_of_sale': 'true',
                    'save_defaults': 'false',
                    'stripe_payment_info': json.dumps({
                        'email': 'testuser@test.com',
                        'payment_type': 'card',
                        'card_name': 'Test User',
                        'card_brand': 'Visa',
                        'card_last4': '4242',
                        'card_exp_month': '12',
                        'card_exp_year': '2025',
                        'card_zip': '12345'
                    }),
                    'stripe_shipping_addr': json.dumps({
                        'name': 'Test User',
                        'address_line1': '123 Main St',
                        'address_city': 'Anytown',
                        'address_state': 'CA',
                        'address_zip': '12345',
                        'address_country': 'United States',
                        'address_country_code': 'US'
                    }),
                    'stripe_billing_addr': json.dumps({
                        'name': 'Test User',
                        'address_line1': '123 Main St',
                        'address_city': 'Anytown',
                        'address_state': 'CA',
                        'address_zip': '12345',
                        'address_country': 'United States',
                        'address_country_code': 'US'
                    })
                })

                unittest_utilities.validate_response_is_OK_and_JSON(self, response)

                data = json.loads(response.content.decode('utf8'))
                self.assertEqual(data['confirm_place_order'], 'success')
                self.assertIn('order_identifier', data)

                # Verify order was created
                order = Order.objects.get(identifier=data['order_identifier'])
                self.assertEqual(order.member, self.member)
                self.assertEqual(order.agreed_with_terms_of_sale, True)
                self.assertTrue(order.order_total > 0)

                # Verify payment was created
                self.assertEqual(order.payment.email, 'testuser@test.com')
                self.assertEqual(order.payment.card_brand, 'Visa')
                self.assertEqual(order.payment.card_last4, '4242')

                # Verify shipping address was created
                self.assertEqual(order.shipping_address.name, 'Test User')
                self.assertEqual(order.shipping_address.city, 'Anytown')

                # Verify billing address was created
                self.assertEqual(order.billing_address.name, 'Test User')
                self.assertEqual(order.billing_address.city, 'Anytown')

                # Verify cart was cleared
                self.assertEqual(Cart.objects.filter(member=self.member).count(), 0)

    def test_confirm_place_order_success_anonymous_user(self):
        """Test successful order placement for anonymous user"""
        from order.models import Order
        from unittest.mock import patch, MagicMock

        # Mock email sending to avoid needing Email templates
        with patch('user.models.Email.objects.get') as mock_email_get, \
             patch('user.models.Emailtype.objects.get') as mock_emailtype_get:

            mock_email = MagicMock()
            mock_email.subject = 'Order Confirmation'
            mock_email.body_html = '<p>Thank you for your order</p>'
            mock_email.body_text = 'Thank you for your order. Order info: {order_information}'
            mock_email.from_address = 'noreply@test.com'
            mock_email.bcc_address = ''
            mock_email.em_cd = 'order_confirmation_prospect'
            mock_email.email_type = MagicMock()
            mock_email.email_type.id = 999
            mock_email_get.return_value = mock_email

            def emailtype_side_effect(title):
                mock_type = MagicMock()
                mock_type.title = title
                mock_type.id = hash(title)
                return mock_type
            mock_emailtype_get.side_effect = emailtype_side_effect

            with patch('django.core.mail.EmailMultiAlternatives.send') as mock_send_email, \
                 patch('order.utilities.order_utils.look_up_cart') as mock_look_up_cart:
                # Create prospect for anonymous user
                prospect = Prospect.objects.create(
                    email='anonymous@test.com',
                    created_date_time=timezone.now()
                )

                # Create anonymous cart
                anonymous_cart_id = 'test_anon_cart_123'

                # Create cart for anonymous user
                anonymous_cart = Cart.objects.create(anonymous_cart_id=anonymous_cart_id)
                Cartsku.objects.create(cart=anonymous_cart, sku=self.sku, quantity=1)

                # Mock look_up_cart to return our anonymous cart
                mock_look_up_cart.return_value = anonymous_cart

                # Add shipping method for anonymous cart
                from order.models import Cartshippingmethod, Shippingmethod
                shipping_method = Shippingmethod.objects.get(identifier='standard')
                Cartshippingmethod.objects.create(
                    cart=anonymous_cart,
                    shippingmethod=shipping_method
                )

                response = self.client.post('/order/confirm-place-order', {
                    'agree_to_terms_of_sale': 'true',
                    'stripe_payment_info': json.dumps({
                        'email': 'anonymous@test.com',
                        'payment_type': 'card',
                        'card_name': 'Anonymous User',
                        'card_brand': 'Mastercard',
                        'card_last4': '5555',
                        'card_exp_month': '06',
                        'card_exp_year': '2026',
                        'card_zip': '54321'
                    }),
                    'stripe_shipping_addr': json.dumps({
                        'name': 'Anonymous User',
                        'address_line1': '456 Oak Ave',
                        'address_city': 'Somewhere',
                        'address_state': 'NY',
                        'address_zip': '54321',
                        'address_country': 'United States',
                        'address_country_code': 'US'
                    }),
                    'stripe_billing_addr': json.dumps({
                        'name': 'Anonymous User',
                        'address_line1': '456 Oak Ave',
                        'address_city': 'Somewhere',
                        'address_state': 'NY',
                        'address_zip': '54321',
                        'address_country': 'United States',
                        'address_country_code': 'US'
                    })
                })

                unittest_utilities.validate_response_is_OK_and_JSON(self, response)

                data = json.loads(response.content.decode('utf8'))
                self.assertEqual(data['confirm_place_order'], 'success')

                # Verify order was created with prospect
                order = Order.objects.get(identifier=data['order_identifier'])
                self.assertIsNone(order.member)
                self.assertIsNotNone(order.prospect)
                self.assertEqual(order.prospect.email, 'anonymous@test.com')

                # Verify cart was cleared
                self.assertEqual(Cart.objects.filter(anonymous_cart_id=anonymous_cart_id).count(), 0)

    def test_confirm_place_order_with_save_defaults(self):
        """Test order placement with save defaults enabled"""
        from user.models import Defaultshippingaddress
        from unittest.mock import patch, MagicMock

        # Mock email sending and Stripe API
        with patch('user.models.Email.objects.get') as mock_email_get, \
             patch('user.models.Emailtype.objects.get') as mock_emailtype_get, \
             patch('stripe.Customer.modify') as mock_stripe_modify:

            mock_email = MagicMock()
            mock_email.subject = 'Order Confirmation'
            mock_email.body_html = '<p>Thank you for your order</p>'
            mock_email.body_text = 'Thank you for your order. Order info: {order_information}'
            mock_email.from_address = 'noreply@test.com'
            mock_email.bcc_address = ''
            mock_email.em_cd = 'order_confirmation_member'
            mock_email.email_type = MagicMock()
            mock_email.email_type.id = 999
            mock_email_get.return_value = mock_email

            def emailtype_side_effect(title):
                mock_type = MagicMock()
                mock_type.title = title
                mock_type.id = hash(title)
                return mock_type
            mock_emailtype_get.side_effect = emailtype_side_effect

            # Mock Stripe Customer.modify to avoid real API calls
            mock_stripe_modify.return_value = {'id': 'cus_test123'}

            with patch('django.core.mail.EmailMultiAlternatives.send') as mock_send_email:
                self.client.login(username='testuser', password='testpass123')

                # Verify no default shipping address exists
                self.assertIsNone(self.member.default_shipping_address)
                self.assertFalse(self.member.use_default_shipping_and_payment_info)

                response = self.client.post('/order/confirm-place-order', {
                    'agree_to_terms_of_sale': 'true',
                    'save_defaults': 'true',
                    'stripe_payment_info': json.dumps({
                        'email': 'testuser@test.com',
                        'payment_type': 'card',
                        'card_name': 'Test User',
                        'card_brand': 'Visa',
                        'card_last4': '4242',
                        'card_exp_month': '12',
                        'card_exp_year': '2025',
                        'card_zip': '12345'
                    }),
                    'stripe_shipping_addr': json.dumps({
                        'name': 'Test User Saved',
                        'address_line1': '789 Pine Rd',
                        'address_city': 'Defaultcity',
                        'address_state': 'TX',
                        'address_zip': '78901',
                        'address_country': 'United States',
                        'address_country_code': 'US'
                    }),
                    'stripe_billing_addr': json.dumps({
                        'name': 'Test User',
                        'address_line1': '123 Main St',
                        'address_city': 'Anytown',
                        'address_state': 'CA',
                        'address_zip': '12345',
                        'address_country': 'United States',
                        'address_country_code': 'US'
                    })
                })

                unittest_utilities.validate_response_is_OK_and_JSON(self, response)

                data = json.loads(response.content.decode('utf8'))
                self.assertEqual(data['confirm_place_order'], 'success')

                # Refresh member from database
                self.member.refresh_from_db()

                # Verify default shipping address was saved
                self.assertIsNotNone(self.member.default_shipping_address)
                self.assertEqual(self.member.default_shipping_address.name, 'Test User Saved')
                self.assertEqual(self.member.default_shipping_address.city, 'Defaultcity')

    def test_confirm_place_order_updates_existing_default_shipping(self):
        """Test that save_defaults updates existing default shipping address"""
        from user.models import Defaultshippingaddress
        from unittest.mock import patch, MagicMock

        # Create existing default shipping address for member
        existing_default = Defaultshippingaddress.objects.create(
            name='Old Name',
            address_line1='Old Address',
            city='Old City',
            state='CA',
            zip='11111',
            country='United States',
            country_code='US'
        )
        self.member.default_shipping_address = existing_default
        self.member.save()

        # Mock email sending and Stripe API
        with patch('user.models.Email.objects.get') as mock_email_get, \
             patch('user.models.Emailtype.objects.get') as mock_emailtype_get, \
             patch('stripe.Customer.modify') as mock_stripe_modify:

            mock_email = MagicMock()
            mock_email.subject = 'Order Confirmation'
            mock_email.body_text = 'Thank you. Order info: {order_information}'
            mock_email.from_address = 'noreply@test.com'
            mock_email.bcc_address = ''
            mock_email.em_cd = 'order_confirmation_member'
            mock_email.email_type = MagicMock()
            mock_email.email_type.id = 999
            mock_email_get.return_value = mock_email

            def emailtype_side_effect(title):
                mock_type = MagicMock()
                mock_type.title = title
                mock_type.id = hash(title)
                return mock_type
            mock_emailtype_get.side_effect = emailtype_side_effect
            mock_stripe_modify.return_value = {'id': 'cus_test123'}

            with patch('django.core.mail.EmailMultiAlternatives.send') as mock_send_email:
                self.client.login(username='testuser', password='testpass123')

                response = self.client.post('/order/confirm-place-order', {
                    'agree_to_terms_of_sale': 'true',
                    'save_defaults': 'true',
                    'stripe_payment_info': json.dumps({
                        'email': 'testuser@test.com',
                        'payment_type': 'card',
                        'card_name': 'Test User',
                        'card_brand': 'Visa',
                        'card_last4': '4242',
                        'card_exp_month': '12',
                        'card_exp_year': '2025',
                        'card_zip': '12345'
                    }),
                    'stripe_shipping_addr': json.dumps({
                        'name': 'Updated Name',
                        'address_line1': 'Updated Address',
                        'address_city': 'Updated City',
                        'address_state': 'NY',
                        'address_zip': '99999',
                        'address_country': 'United States',
                        'address_country_code': 'US'
                    }),
                    'stripe_billing_addr': json.dumps({
                        'name': 'Test User',
                        'address_line1': '123 Main St',
                        'address_city': 'Anytown',
                        'address_state': 'CA',
                        'address_zip': '12345',
                        'address_country': 'United States',
                        'address_country_code': 'US'
                    })
                })

                unittest_utilities.validate_response_is_OK_and_JSON(self, response)

                data = json.loads(response.content.decode('utf8'))
                self.assertEqual(data['confirm_place_order'], 'success')

                # Refresh member from database
                self.member.refresh_from_db()

                # Verify existing default shipping address was updated (not replaced)
                self.assertEqual(self.member.default_shipping_address.id, existing_default.id)
                self.assertEqual(self.member.default_shipping_address.name, 'Updated Name')
                self.assertEqual(self.member.default_shipping_address.address_line1, 'Updated Address')
                self.assertEqual(self.member.default_shipping_address.city, 'Updated City')
                self.assertEqual(self.member.default_shipping_address.state, 'NY')
                self.assertEqual(self.member.default_shipping_address.zip, '99999')
                self.assertTrue(self.member.use_default_shipping_and_payment_info)

    def test_confirm_place_order_anonymous_with_newsletter_true(self):
        """Test anonymous order with newsletter subscription opted in"""
        from order.models import Order
        from unittest.mock import patch, MagicMock

        with patch('user.models.Email.objects.get') as mock_email_get, \
             patch('user.models.Emailtype.objects.get') as mock_emailtype_get:

            mock_email = MagicMock()
            mock_email.subject = 'Order Confirmation'
            mock_email.body_text = 'Thank you. Order info: {order_information}'
            mock_email.from_address = 'noreply@test.com'
            mock_email.bcc_address = ''
            mock_email.em_cd = 'order_confirmation_prospect'
            mock_email.email_type = MagicMock()
            mock_email.email_type.id = 999
            mock_email_get.return_value = mock_email

            def emailtype_side_effect(title):
                mock_type = MagicMock()
                mock_type.title = title
                mock_type.id = hash(title)
                return mock_type
            mock_emailtype_get.side_effect = emailtype_side_effect

            with patch('django.core.mail.EmailMultiAlternatives.send') as mock_send_email, \
                 patch('order.utilities.order_utils.look_up_cart') as mock_look_up_cart:

                # Create prospect for anonymous user
                prospect = Prospect.objects.create(
                    email='newsletter@test.com',
                    pr_cd='PROSPECT_NEWS',
                    email_unsubscribed=True,  # Start unsubscribed
                    email_unsubscribe_string_signed='test_signed_string_123',
                    created_date_time=timezone.now()
                )

                # Create anonymous cart
                anonymous_cart = Cart.objects.create(anonymous_cart_id='anon_newsletter_123')
                Cartsku.objects.create(cart=anonymous_cart, sku=self.sku, quantity=1)
                mock_look_up_cart.return_value = anonymous_cart

                # Add shipping method
                from order.models import Cartshippingmethod, Shippingmethod
                shipping_method = Shippingmethod.objects.get(identifier='standard')
                Cartshippingmethod.objects.create(
                    cart=anonymous_cart,
                    shippingmethod=shipping_method
                )

                response = self.client.post('/order/confirm-place-order', {
                    'agree_to_terms_of_sale': 'true',
                    'newsletter': 'true',  # User opts in to newsletter
                    'stripe_payment_info': json.dumps({
                        'email': 'newsletter@test.com',
                        'payment_type': 'card',
                        'card_name': 'Newsletter User',
                        'card_brand': 'Visa',
                        'card_last4': '4242',
                        'card_exp_month': '12',
                        'card_exp_year': '2025',
                        'card_zip': '12345'
                    }),
                    'stripe_shipping_addr': json.dumps({
                        'name': 'Newsletter User',
                        'address_line1': '123 News St',
                        'address_city': 'Newstown',
                        'address_state': 'CA',
                        'address_zip': '12345',
                        'address_country': 'United States',
                        'address_country_code': 'US'
                    }),
                    'stripe_billing_addr': json.dumps({
                        'name': 'Newsletter User',
                        'address_line1': '123 News St',
                        'address_city': 'Newstown',
                        'address_state': 'CA',
                        'address_zip': '12345',
                        'address_country': 'United States',
                        'address_country_code': 'US'
                    })
                })

                unittest_utilities.validate_response_is_OK_and_JSON(self, response)

                data = json.loads(response.content.decode('utf8'))
                self.assertEqual(data['confirm_place_order'], 'success')

                # Verify prospect was updated to be subscribed to newsletter
                prospect.refresh_from_db()
                self.assertFalse(prospect.email_unsubscribed)  # Should be subscribed now

    def test_confirm_place_order_anonymous_without_newsletter(self):
        """Test anonymous order without newsletter subscription"""
        from order.models import Order
        from unittest.mock import patch, MagicMock

        with patch('user.models.Email.objects.get') as mock_email_get, \
             patch('user.models.Emailtype.objects.get') as mock_emailtype_get:

            mock_email = MagicMock()
            mock_email.subject = 'Order Confirmation'
            mock_email.body_text = 'Thank you. Order info: {order_information}'
            mock_email.from_address = 'noreply@test.com'
            mock_email.bcc_address = ''
            mock_email.em_cd = 'order_confirmation_prospect'
            mock_email.email_type = MagicMock()
            mock_email.email_type.id = 999
            mock_email_get.return_value = mock_email

            def emailtype_side_effect(title):
                mock_type = MagicMock()
                mock_type.title = title
                mock_type.id = hash(title)
                return mock_type
            mock_emailtype_get.side_effect = emailtype_side_effect

            with patch('django.core.mail.EmailMultiAlternatives.send') as mock_send_email, \
                 patch('order.utilities.order_utils.look_up_cart') as mock_look_up_cart:

                # Create prospect for anonymous user
                prospect = Prospect.objects.create(
                    email='nonews@test.com',
                    pr_cd='PROSPECT_NONEWS',
                    email_unsubscribed=False,  # Start subscribed
                    email_unsubscribe_string_signed='test_signed_string_456',
                    created_date_time=timezone.now()
                )

                # Create anonymous cart
                anonymous_cart = Cart.objects.create(anonymous_cart_id='anon_nonews_123')
                Cartsku.objects.create(cart=anonymous_cart, sku=self.sku, quantity=1)
                mock_look_up_cart.return_value = anonymous_cart

                # Add shipping method
                from order.models import Cartshippingmethod, Shippingmethod
                shipping_method = Shippingmethod.objects.get(identifier='standard')
                Cartshippingmethod.objects.create(
                    cart=anonymous_cart,
                    shippingmethod=shipping_method
                )

                response = self.client.post('/order/confirm-place-order', {
                    'agree_to_terms_of_sale': 'true',
                    'newsletter': 'false',  # User opts out of newsletter
                    'stripe_payment_info': json.dumps({
                        'email': 'nonews@test.com',
                        'payment_type': 'card',
                        'card_name': 'No News User',
                        'card_brand': 'Mastercard',
                        'card_last4': '5555',
                        'card_exp_month': '06',
                        'card_exp_year': '2026',
                        'card_zip': '54321'
                    }),
                    'stripe_shipping_addr': json.dumps({
                        'name': 'No News User',
                        'address_line1': '456 Quiet Ave',
                        'address_city': 'Quiettown',
                        'address_state': 'NY',
                        'address_zip': '54321',
                        'address_country': 'United States',
                        'address_country_code': 'US'
                    }),
                    'stripe_billing_addr': json.dumps({
                        'name': 'No News User',
                        'address_line1': '456 Quiet Ave',
                        'address_city': 'Quiettown',
                        'address_state': 'NY',
                        'address_zip': '54321',
                        'address_country': 'United States',
                        'address_country_code': 'US'
                    })
                })

                unittest_utilities.validate_response_is_OK_and_JSON(self, response)

                data = json.loads(response.content.decode('utf8'))
                self.assertEqual(data['confirm_place_order'], 'success')

                # Verify prospect remains unsubscribed from newsletter
                prospect.refresh_from_db()
                self.assertTrue(prospect.email_unsubscribed)  # Should still be unsubscribed

    def test_confirm_place_order_with_discount_code(self):
        """Test order placement with discount code creates Orderdiscount record"""
        from order.models import Discountcode, Discounttype, Cartdiscount, Order, Orderdiscount
        from unittest.mock import patch, MagicMock
        from datetime import timedelta

        # Create discount type
        discount_type = Discounttype.objects.create(
            title='Percentage Off',
            description='Percentage off total',
            applies_to='order',
            action='subtract'
        )

        # Create a discount code
        now = timezone.now()
        discount_code = Discountcode.objects.create(
            code='TESTCODE10',
            description='10% off test code',
            start_date_time=now,
            end_date_time=now + timedelta(days=30),
            combinable=False,
            discounttype=discount_type,
            discount_amount=10.0,
            order_minimum=0.0
        )

        # Add discount code to cart
        Cartdiscount.objects.create(
            cart=self.cart,
            discountcode=discount_code
        )

        # Mock email sending
        with patch('user.models.Email.objects.get') as mock_email_get, \
             patch('user.models.Emailtype.objects.get') as mock_emailtype_get:

            mock_email = MagicMock()
            mock_email.subject = 'Order Confirmation'
            mock_email.body_text = 'Thank you. Order info: {order_information}'
            mock_email.from_address = 'noreply@test.com'
            mock_email.bcc_address = ''
            mock_email.em_cd = 'order_confirmation_member'
            mock_email.email_type = MagicMock()
            mock_email.email_type.id = 999
            mock_email_get.return_value = mock_email

            def emailtype_side_effect(title):
                mock_type = MagicMock()
                mock_type.title = title
                mock_type.id = hash(title)
                return mock_type
            mock_emailtype_get.side_effect = emailtype_side_effect

            with patch('django.core.mail.EmailMultiAlternatives.send') as mock_send_email:
                self.client.login(username='testuser', password='testpass123')

                response = self.client.post('/order/confirm-place-order', {
                    'agree_to_terms_of_sale': 'true',
                    'save_defaults': 'false',
                    'stripe_payment_info': json.dumps({
                        'email': 'testuser@test.com',
                        'payment_type': 'card',
                        'card_name': 'Test User',
                        'card_brand': 'Visa',
                        'card_last4': '4242',
                        'card_exp_month': '12',
                        'card_exp_year': '2025',
                        'card_zip': '12345'
                    }),
                    'stripe_shipping_addr': json.dumps({
                        'name': 'Test User',
                        'address_line1': '123 Main St',
                        'address_city': 'Anytown',
                        'address_state': 'CA',
                        'address_zip': '12345',
                        'address_country': 'United States',
                        'address_country_code': 'US'
                    }),
                    'stripe_billing_addr': json.dumps({
                        'name': 'Test User',
                        'address_line1': '123 Main St',
                        'address_city': 'Anytown',
                        'address_state': 'CA',
                        'address_zip': '12345',
                        'address_country': 'United States',
                        'address_country_code': 'US'
                    })
                })

                unittest_utilities.validate_response_is_OK_and_JSON(self, response)

                data = json.loads(response.content.decode('utf8'))
                self.assertEqual(data['confirm_place_order'], 'success')

                # Verify order was created
                order = Order.objects.get(identifier=data['order_identifier'])

                # Verify Orderdiscount record was created
                order_discounts = Orderdiscount.objects.filter(order=order)
                self.assertEqual(order_discounts.count(), 1)

                order_discount = order_discounts.first()
                self.assertEqual(order_discount.discountcode.code, 'TESTCODE10')
                self.assertTrue(order_discount.applied)  # Discount was applied
