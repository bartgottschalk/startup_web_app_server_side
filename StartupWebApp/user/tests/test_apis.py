# Unit tests from the perspective of the programmer

import json

from django.core import mail

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from clientevent.models import Configuration as ClientEventConfiguration

from order.models import Skutype, Skuinventory, Product, Sku, Skuprice, Productsku, Order
from user.models import Member, Termsofuse, Prospect, Chatmessage

from StartupWebApp.utilities import unittest_utilities


class UserAPITest(TestCase):

    def setUp(self):
        # Setup necessary DB Objects
        ClientEventConfiguration.objects.create(id=1, log_client_events=True)

        Skutype.objects.create(id=1, title='product')
        Skuinventory.objects.create(
            id=1, title='In Stock', identifier='in-stock', description='In Stock items are available to purchase.'
        )
        Skuinventory.objects.create(
            id=2,
            title='Back Ordered',
            identifier='back-ordered',
            description='Back Ordered items are not available to purchase at this time.',
        )
        Skuinventory.objects.create(
            id=3,
            title='Out of Stock',
            identifier='out-of-stock',
            description='Out of Stock items are not available to purchase.',
        )
        Product.objects.create(
            id=1,
            title='Paper Clips',
            title_url='PaperClips',
            identifier='bSusp6dBHm',
            headline='Paper clips can hold up to 20 pieces of paper together!',
            description_part_1='Made out of high quality metal and folded to exact specifications.',
            description_part_2='Use paperclips for all your paper binding needs!',
        )
        Sku.objects.create(
            id=1, color='Silver', size='Medium', sku_type_id=1, description='Left Sided Paperclip', sku_inventory_id=1
        )
        Skuprice.objects.create(id=1, price=3.5, created_date_time=timezone.now(), sku_id=1)
        Productsku.objects.create(id=1, product_id=1, sku_id=1)
        Group.objects.create(name='Members')
        Termsofuse.objects.create(
            version='1',
            version_note=(
                'Specifically, we\'ve modified our '
                '<a class="raw-link" href="/privacy-policy">Privacy Policy</a> and '
                '<a class="raw-link" href="/terms-of-sale">Terms of Sale</a>. '
                'Modifications include...'
            ),
            publication_date_time=timezone.now(),
        )

    def test_logged_in_for_anonymous_user(self):

        ##############
        # Empty Cart #
        ##############
        response = self.client.get('/user/logged-in')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(
            response.content.decode('utf8'),
            '{"logged_in": false, "log_client_events": true, "client_event_id": "null", '
            '"cart_item_count": 0, "user-api-version": "0.0.1"}',
            '/user/logged-in for anonymous user with empty cart failed json validation',
        )

        ##################
        # NOT Empty Cart #
        ##################
        self.client.post('/order/cart-add-product-sku', data={'sku_id': '1', 'quantity': '1'})
        response = self.client.get('/user/logged-in')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(
            response.content.decode('utf8'),
            '{"logged_in": false, "log_client_events": true, "client_event_id": "null", '
            '"cart_item_count": 1, "user-api-version": "0.0.1"}',
            '/user/logged-in for anonymous user with 1 item in cart failed json validation',
        )

    def test_logged_in_for_authenticated_user(self):

        # create user and login
        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'jest',
                'lastname': 'lser',
                'username': 'testuser_logged_in',
                'email_address': 'jestlser@test.com',
                'password': 'ThisIsValid1!',
                'confirm_password': 'ThisIsValid1!',
                'newsletter': 'true',
                'remember_me': 'false',
            },
        )

        ##############
        # Empty Cart #
        ##############
        response = self.client.get('/user/logged-in')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(
            response.content.decode('utf8'),
            '{"logged_in": true, "log_client_events": true, "client_event_id": '
            + str(User.objects.latest('id').id)
            + ', "member_initials": "'
            + User.objects.latest('id').first_name[:1]
            + User.objects.latest('id').last_name[:1]
            + '", "first_name": "'
            + User.objects.latest('id').first_name
            + '", "last_name": "'
            + User.objects.latest('id').last_name
            + '", "email_address": "'
            + User.objects.latest('id').email
            + '", "cart_item_count": 0, "user-api-version": "0.0.1"}',
            '/user/logged-in for authenticated user with empty cart failed json validation',
        )

        ##################
        # NOT Empty Cart #
        ##################
        self.client.post('/order/cart-add-product-sku', data={'sku_id': '1', 'quantity': '1'})
        response = self.client.get('/user/logged-in')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(
            response.content.decode('utf8'),
            '{"logged_in": true, "log_client_events": true, "client_event_id": '
            + str(User.objects.latest('id').id)
            + ', "member_initials": "'
            + User.objects.latest('id').first_name[:1]
            + User.objects.latest('id').last_name[:1]
            + '", "first_name": "'
            + User.objects.latest('id').first_name
            + '", "last_name": "'
            + User.objects.latest('id').last_name
            + '", "email_address": "'
            + User.objects.latest('id').email
            + '", "cart_item_count": 1, "user-api-version": "0.0.1"}',
            '/user/logged-in for authenticated user with 1 item in cart failed json validation',
        )

    def test_create_account(self):

        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'test',
                'lastname': 'user',
                'username': 'testuser',
                'email_address': 'testuser@test.com',
                'password': 'ThisIsValid1!',
                'confirm_password': 'ThisIsValid1',
                'newsletter': 'true',
                'remember_me': 'false',
            },
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(
            response.content.decode('utf8'),
            '{"create_account": "false", "errors": {"firstname": true, "lastname": true, '
            '"username": true, "email-address": true, "password": [{"type": '
            '"confirm_password_doesnt_match", "description": "Please make sure your passwords '
            'match."}]}, "user-api-version": "0.0.1"}',
            '/user/create-account passwords don\' match failed json validation',
        )

        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'test',
                'lastname': 'user',
                'username': 'testuser',
                'email_address': 'testuser@test.com',
                'password': 'ThisIsValid1!',
                'confirm_password': 'ThisIsValid1!',
                'newsletter': 'true',
                'remember_me': 'false',
            },
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(
            response.content.decode('utf8'),
            '{"create_account": "true", "user-api-version": "0.0.1"}',
            '/user/create-account successful registration failed json validation',
        )
        self.assertEqual(Member.objects.count(), 1)
        new_member = Member.objects.first()
        self.assertEqual(new_member.user.first_name, 'test')

        # self.assertEqual(1, 2)

    def test_create_account_duplicate_username(self):
        """Test that duplicate usernames are rejected"""
        # Create first account
        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'test',
                'lastname': 'user',
                'username': 'testuser',
                'email_address': 'testuser@test.com',
                'password': 'ThisIsValid1!',
                'confirm_password': 'ThisIsValid1!',
                'newsletter': 'false',
                'remember_me': 'false',
            },
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'), '{"create_account": "true", "user-api-version": "0.0.1"}')

        # Logout first user
        self.client.post('/user/logout')

        # Try to create second account with same username but different email
        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'another',
                'lastname': 'user',
                'username': 'testuser',  # Duplicate username
                'email_address': 'different@test.com',
                'password': 'ThisIsValid1!',
                'confirm_password': 'ThisIsValid1!',
                'newsletter': 'false',
                'remember_me': 'false',
            },
        )
        # Should fail validation due to duplicate username
        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['create_account'], 'false')
        self.assertIn('username', response_data['errors'])

    def test_create_account_invalid_email(self):
        """Test that invalid email format is rejected"""
        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'test',
                'lastname': 'user',
                'username': 'testuser',
                'email_address': 'notanemail',  # Invalid email format
                'password': 'ThisIsValid1!',
                'confirm_password': 'ThisIsValid1!',
                'newsletter': 'false',
                'remember_me': 'false',
            },
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['create_account'], 'false')
        self.assertIn('email-address', response_data['errors'])

    def test_create_account_weak_password(self):
        """Test that weak passwords are rejected"""
        # Password without special character
        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'test',
                'lastname': 'user',
                'username': 'testuser',
                'email_address': 'testuser@test.com',
                'password': 'WeakPass1',  # No special character
                'confirm_password': 'WeakPass1',
                'newsletter': 'false',
                'remember_me': 'false',
            },
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['create_account'], 'false')
        self.assertIn('password', response_data['errors'])

    def test_create_account_empty_fields(self):
        """Test that empty required fields are rejected"""
        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': '',  # Empty
                'lastname': '',
                'username': '',
                'email_address': '',
                'password': '',
                'confirm_password': '',
                'newsletter': 'false',
                'remember_me': 'false',
            },
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['create_account'], 'false')
        # All fields should have errors
        self.assertIn('firstname', response_data['errors'])
        self.assertIn('lastname', response_data['errors'])
        self.assertIn('username', response_data['errors'])
        self.assertIn('email-address', response_data['errors'])
        self.assertIn('password', response_data['errors'])

    def test_create_account_cart_merge(self):
        """Test that anonymous cart is merged on account creation"""
        # Add item to anonymous cart
        self.client.post('/order/cart-add-product-sku', data={'sku_id': '1', 'quantity': '2'})

        # Verify anonymous cart has item
        response = self.client.get('/user/logged-in')
        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['cart_item_count'], 1)

        # Create account
        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'test',
                'lastname': 'user',
                'username': 'testuser',
                'email_address': 'testuser@test.com',
                'password': 'ThisIsValid1!',
                'confirm_password': 'ThisIsValid1!',
                'newsletter': 'false',
                'remember_me': 'false',
            },
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'), '{"create_account": "true", "user-api-version": "0.0.1"}')

        # Verify member cart now has the item
        response = self.client.get('/user/logged-in')
        response_data = json.loads(response.content.decode('utf8'))
        self.assertTrue(response_data['logged_in'])
        self.assertEqual(response_data['cart_item_count'], 1, 'Member cart should have merged anonymous cart item')

    def test_create_account_newsletter_subscription(self):
        """Test newsletter subscription flag is saved correctly"""
        # Create account with newsletter=true
        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'test',
                'lastname': 'subscriber',
                'username': 'newsletter_user',
                'email_address': 'newsletter@test.com',
                'password': 'ThisIsValid1!',
                'confirm_password': 'ThisIsValid1!',
                'newsletter': 'true',  # Subscribe to newsletter
                'remember_me': 'false',
            },
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'), '{"create_account": "true", "user-api-version": "0.0.1"}')

        # Verify member has newsletter_subscriber=True
        member = Member.objects.get(user__username='newsletter_user')
        self.assertTrue(member.newsletter_subscriber, 'Member should be subscribed to newsletter')

    def test_create_account_no_newsletter(self):
        """Test account creation without newsletter subscription"""
        # Create account with newsletter=false
        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'test',
                'lastname': 'nonsubscriber',
                'username': 'no_newsletter_user',
                'email_address': 'nonewsletter@test.com',
                'password': 'ThisIsValid1!',
                'confirm_password': 'ThisIsValid1!',
                'newsletter': 'false',  # Don't subscribe
                'remember_me': 'false',
            },
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'), '{"create_account": "true", "user-api-version": "0.0.1"}')

        # Verify member has newsletter_subscriber=False
        member = Member.objects.get(user__username='no_newsletter_user')
        self.assertFalse(member.newsletter_subscriber, 'Member should not be subscribed to newsletter')

    def test_create_account_terms_of_use_agreement(self):
        """Test that terms of use agreement is created on registration"""
        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'test',
                'lastname': 'user',
                'username': 'testuser',
                'email_address': 'testuser@test.com',
                'password': 'ThisIsValid1!',
                'confirm_password': 'ThisIsValid1!',
                'newsletter': 'false',
                'remember_me': 'false',
            },
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'), '{"create_account": "true", "user-api-version": "0.0.1"}')

        # Verify terms of use agreement was created
        from user.models import Membertermsofuseversionagreed

        member = Member.objects.get(user__username='testuser')
        agreements = Membertermsofuseversionagreed.objects.filter(member=member)
        self.assertEqual(agreements.count(), 1, 'Should have one terms of use agreement')

        # Verify it's the latest version
        latest_terms = Termsofuse.objects.first()
        self.assertEqual(agreements.first().termsofuseversion, latest_terms)

    def test_create_account_prospect_conversion(self):
        """Test that existing Prospect is converted to Member on account creation"""
        # Create a prospect first
        prospect_email = 'prospect@test.com'
        Prospect.objects.create(
            first_name='Prospect',
            last_name='User',
            email=prospect_email,
            phone='555-1234',
            email_unsubscribed=False,
            email_unsubscribe_string='test_string',
            email_unsubscribe_string_signed='test_signed',
            pr_cd='PR123',
            created_date_time=timezone.now(),
        )

        # Create account with same email as prospect
        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'test',
                'lastname': 'user',
                'username': 'converted_prospect',
                'email_address': prospect_email,  # Same as prospect email
                'password': 'ThisIsValid1!',
                'confirm_password': 'ThisIsValid1!',
                'newsletter': 'false',
                'remember_me': 'false',
            },
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'), '{"create_account": "true", "user-api-version": "0.0.1"}')

        # Verify prospect was converted
        prospect = Prospect.objects.get(email=prospect_email)
        self.assertIsNotNone(prospect.converted_date_time, 'Prospect should have conversion date')
        self.assertTrue(prospect.email_unsubscribed, 'Prospect email should be unsubscribed after conversion')
        self.assertIn('converted by creating user', prospect.swa_comment.lower())

    def test_create_account_auto_login(self):
        """Test that user is automatically logged in after account creation"""
        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'test',
                'lastname': 'user',
                'username': 'autologin_user',
                'email_address': 'autologin@test.com',
                'password': 'ThisIsValid1!',
                'confirm_password': 'ThisIsValid1!',
                'newsletter': 'false',
                'remember_me': 'false',
            },
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'), '{"create_account": "true", "user-api-version": "0.0.1"}')

        # Verify user is logged in
        response = self.client.get('/user/logged-in')
        response_data = json.loads(response.content.decode('utf8'))
        self.assertTrue(response_data['logged_in'], 'User should be automatically logged in after account creation')
        self.assertEqual(response_data['first_name'], 'test')
        self.assertEqual(response_data['email_address'], 'autologin@test.com')

    def test_create_account_remember_me_flag(self):
        """Test remember_me flag affects session expiry on account creation"""
        # Test with remember_me=false (session should expire at browser close)
        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'test',
                'lastname': 'user',
                'username': 'testuser_browser_session',
                'email_address': 'browser@test.com',
                'password': 'ThisIsValid1!',
                'confirm_password': 'ThisIsValid1!',
                'newsletter': 'false',
                'remember_me': 'false',
            },
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'), '{"create_account": "true", "user-api-version": "0.0.1"}')

        # Check session expiry (should expire at browser close)
        expire_at_browser_close = self.client.session.get_expire_at_browser_close()
        self.assertTrue(expire_at_browser_close, 'Session should expire at browser close when remember_me=false')

        # Logout for next test
        self.client.post('/user/logout')

        # Test with remember_me=true (session should persist)
        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'test',
                'lastname': 'user',
                'username': 'testuser_persistent',
                'email_address': 'persistent@test.com',
                'password': 'ThisIsValid1!',
                'confirm_password': 'ThisIsValid1!',
                'newsletter': 'false',
                'remember_me': 'true',
            },
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'), '{"create_account": "true", "user-api-version": "0.0.1"}')

        # Check session expiry (should NOT expire at browser close)
        expire_at_browser_close = self.client.session.get_expire_at_browser_close()
        self.assertFalse(expire_at_browser_close, 'Session should not expire at browser close when remember_me=true')

    def test_create_account_member_group_assignment(self):
        """Test that new user is added to Members group"""
        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'test',
                'lastname': 'user',
                'username': 'group_user',
                'email_address': 'group@test.com',
                'password': 'ThisIsValid1!',
                'confirm_password': 'ThisIsValid1!',
                'newsletter': 'false',
                'remember_me': 'false',
            },
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'), '{"create_account": "true", "user-api-version": "0.0.1"}')

        # Verify user is in Members group
        user = User.objects.get(username='group_user')
        members_group = Group.objects.get(name='Members')
        self.assertTrue(user.groups.filter(name='Members').exists(), 'User should be in Members group')
        self.assertIn(members_group, user.groups.all())

    def test_create_account_email_verification_string(self):
        """Test that email verification string is generated and signed"""
        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'test',
                'lastname': 'user',
                'username': 'verify_user',
                'email_address': 'verify@test.com',
                'password': 'ThisIsValid1!',
                'confirm_password': 'ThisIsValid1!',
                'newsletter': 'false',
                'remember_me': 'false',
            },
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'), '{"create_account": "true", "user-api-version": "0.0.1"}')

        # Verify email verification strings are created
        member = Member.objects.get(user__username='verify_user')
        self.assertIsNotNone(member.email_verification_string, 'Email verification string should be generated')
        self.assertIsNotNone(member.email_verification_string_signed, 'Signed verification string should be generated')
        self.assertGreater(len(member.email_verification_string), 0)
        self.assertGreater(len(member.email_verification_string_signed), 0)
        self.assertFalse(member.email_verified, 'Email should not be verified initially')

    def test_create_account_unsubscribe_string(self):
        """Test that email unsubscribe string is generated and signed"""
        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'test',
                'lastname': 'user',
                'username': 'unsub_user',
                'email_address': 'unsub@test.com',
                'password': 'ThisIsValid1!',
                'confirm_password': 'ThisIsValid1!',
                'newsletter': 'false',
                'remember_me': 'false',
            },
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'), '{"create_account": "true", "user-api-version": "0.0.1"}')

        # Verify email unsubscribe strings are created
        member = Member.objects.get(user__username='unsub_user')
        self.assertIsNotNone(member.email_unsubscribe_string, 'Unsubscribe string should be generated')
        self.assertIsNotNone(member.email_unsubscribe_string_signed, 'Signed unsubscribe string should be generated')
        self.assertGreater(len(member.email_unsubscribe_string), 0)
        self.assertGreater(len(member.email_unsubscribe_string_signed), 0)
        self.assertFalse(member.email_unsubscribed, 'Email should not be unsubscribed initially')

    def test_create_account_member_code(self):
        """Test that unique member code (mb_cd) is generated"""
        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'test',
                'lastname': 'user',
                'username': 'mbcd_user',
                'email_address': 'mbcd@test.com',
                'password': 'ThisIsValid1!',
                'confirm_password': 'ThisIsValid1!',
                'newsletter': 'false',
                'remember_me': 'false',
            },
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'), '{"create_account": "true", "user-api-version": "0.0.1"}')

        # Verify member code is created and unique
        member = Member.objects.get(user__username='mbcd_user')
        self.assertIsNotNone(member.mb_cd, 'Member code should be generated')
        self.assertGreater(len(member.mb_cd), 0)

        # Create another account and verify different mb_cd
        self.client.post('/user/logout')
        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'test2',
                'lastname': 'user2',
                'username': 'mbcd_user2',
                'email_address': 'mbcd2@test.com',
                'password': 'ThisIsValid1!',
                'confirm_password': 'ThisIsValid1!',
                'newsletter': 'false',
                'remember_me': 'false',
            },
        )
        member2 = Member.objects.get(user__username='mbcd_user2')
        self.assertNotEqual(member.mb_cd, member2.mb_cd, 'Member codes should be unique')

    def test_create_account_prospect_with_orders(self):
        """Test that prospect orders are transferred to member on conversion"""
        # Create prospect with an order
        prospect_email = 'prospect_with_order@test.com'
        prospect = Prospect.objects.create(
            first_name='Prospect',
            last_name='WithOrder',
            email=prospect_email,
            phone='555-1234',
            email_unsubscribed=False,
            email_unsubscribe_string='test_string',
            email_unsubscribe_string_signed='test_signed',
            pr_cd='PR456',
            created_date_time=timezone.now(),
        )

        # Create an order for this prospect
        order = Order.objects.create(prospect=prospect, order_date_time=timezone.now())

        # Create account with same email
        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'test',
                'lastname': 'user',
                'username': 'converted_with_order',
                'email_address': prospect_email,
                'password': 'ThisIsValid1!',
                'confirm_password': 'ThisIsValid1!',
                'newsletter': 'false',
                'remember_me': 'false',
            },
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'), '{"create_account": "true", "user-api-version": "0.0.1"}')

        # Verify order was transferred to member
        member = Member.objects.get(user__username='converted_with_order')
        order.refresh_from_db()
        self.assertEqual(order.member, member, 'Order should be transferred to member')
        self.assertEqual(order.prospect, prospect, 'Original prospect reference should remain')

    def test_create_account_multiple_chat_messages(self):
        """Test that multiple chat messages are linked to member on account creation"""
        email = 'chatuser@test.com'

        # Create a prospect first (chat messages only link if prospect exists)
        Prospect.objects.create(
            first_name='Chat',
            last_name='User',
            email=email,
            phone='555-9999',
            email_unsubscribed=False,
            email_unsubscribe_string='chat_string',
            email_unsubscribe_string_signed='chat_signed',
            pr_cd='PR789',
            created_date_time=timezone.now(),
        )

        # Create multiple chat messages with this email
        Chatmessage.objects.create(email_address=email, message='First message', created_date_time=timezone.now())
        Chatmessage.objects.create(email_address=email, message='Second message', created_date_time=timezone.now())

        # Verify chat messages exist without member link
        self.assertEqual(Chatmessage.objects.filter(email_address=email, member__isnull=True).count(), 2)

        # Create account
        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'test',
                'lastname': 'user',
                'username': 'chat_user',
                'email_address': email,
                'password': 'ThisIsValid1!',
                'confirm_password': 'ThisIsValid1!',
                'newsletter': 'false',
                'remember_me': 'false',
            },
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'), '{"create_account": "true", "user-api-version": "0.0.1"}')

        # Verify all chat messages are linked to member
        member = Member.objects.get(user__username='chat_user')
        linked_messages = Chatmessage.objects.filter(email_address=email, member=member)
        self.assertEqual(linked_messages.count(), 2, 'Both chat messages should be linked to member')

    def test_create_account_sends_welcome_email(self):
        """Test that welcome email is sent on account creation"""
        # Clear mail outbox
        mail.outbox = []

        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'test',
                'lastname': 'user',
                'username': 'email_user',
                'email_address': 'emailtest@test.com',
                'password': 'ThisIsValid1!',
                'confirm_password': 'ThisIsValid1!',
                'newsletter': 'false',
                'remember_me': 'false',
            },
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'), '{"create_account": "true", "user-api-version": "0.0.1"}')

        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1, 'Welcome email should be sent')
        self.assertEqual(mail.outbox[0].to, ['emailtest@test.com'], 'Email should be sent to user email')
        self.assertIn('welcome', mail.outbox[0].subject.lower(), 'Email subject should contain "welcome"')

    def test_create_account_member_field_initialization(self):
        """Test that all Member model fields are properly initialized"""
        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'test',
                'lastname': 'user',
                'username': 'fields_user',
                'email_address': 'fields@test.com',
                'password': 'ThisIsValid1!',
                'confirm_password': 'ThisIsValid1!',
                'newsletter': 'false',
                'remember_me': 'false',
            },
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertJSONEqual(response.content.decode('utf8'), '{"create_account": "true", "user-api-version": "0.0.1"}')

        # Verify member fields are initialized
        member = Member.objects.get(user__username='fields_user')

        # Stripe customer token should be None/empty initially
        self.assertTrue(
            member.stripe_customer_token is None or member.stripe_customer_token == '',
            'Stripe customer token should be None or empty initially',
        )

        # Default shipping address should be None initially
        self.assertIsNone(member.default_shipping_address, 'Default shipping address should be None initially')

        # Reset password strings should be None/empty initially
        self.assertTrue(
            member.reset_password_string is None or member.reset_password_string == '',
            'Reset password string should be None or empty initially',
        )
        self.assertTrue(
            member.reset_password_string_signed is None or member.reset_password_string_signed == '',
            'Reset password string signed should be None or empty initially',
        )

        # Use default shipping and payment info should be False initially
        self.assertFalse(
            member.use_default_shipping_and_payment_info, 'Use default shipping/payment should be False initially'
        )

    def test_create_account_with_invalid_data_preserves_database(self):
        """Test that failed account creation doesn't leave partial data"""
        # Get initial counts
        initial_user_count = User.objects.count()
        initial_member_count = Member.objects.count()

        # Try to create account with mismatched passwords
        response = self.client.post(
            '/user/create-account',
            data={
                'firstname': 'test',
                'lastname': 'user',
                'username': 'failed_user',
                'email_address': 'failed@test.com',
                'password': 'ThisIsValid1!',
                'confirm_password': 'DifferentPassword1!',  # Mismatch
                'newsletter': 'false',
                'remember_me': 'false',
            },
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        response_data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response_data['create_account'], 'false')

        # Verify no User or Member was created
        self.assertEqual(User.objects.count(), initial_user_count, 'No User should be created on validation failure')
        self.assertEqual(
            Member.objects.count(), initial_member_count, 'No Member should be created on validation failure'
        )

    def test_pythonabot_notify_me(self):

        response = self.client.post('/user/pythonabot-notify-me', data={'email_address': '', 'how_excited': '1'})
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        # print(response.content.decode('utf8'))
        self.assertJSONEqual(
            response.content.decode('utf8'),
            '{"pythonabot_notify_me": "validation_error", "errors": {"email_address": [{"type": '
            '"required", "description": "This is a required field."}], "how_excited": true}, '
            '"user-api-version": "0.0.1"}',
            '/user/pythonabot-notify-me email required failed validation',
        )

        response = self.client.post('/user/pythonabot-notify-me', data={'email_address': 'asdf', 'how_excited': '2'})
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        # print(response.content.decode('utf8'))
        self.assertJSONEqual(
            response.content.decode('utf8'),
            '{"pythonabot_notify_me": "validation_error", "errors": {"email_address": [{"type": '
            '"not_valid", "description": "Please enter a valid email address. For example '
            'johndoe@domain.com."}], "how_excited": true}, "user-api-version": "0.0.1"}',
            '/user/pythonabot-notify-me email valid failed validation',
        )

        response = self.client.post(
            '/user/pythonabot-notify-me', data={'email_address': 'asdf@asdf.com', 'how_excited': ''}
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        # print(response.content.decode('utf8'))
        self.assertJSONEqual(
            response.content.decode('utf8'),
            '{"pythonabot_notify_me": "validation_error", "errors": {"email_address": true, '
            '"how_excited": [{"type": "required", "description": "This is a required field."}]}, '
            '"user-api-version": "0.0.1"}',
            '/user/pythonabot-notify-me how_excited valid failed validation',
        )

        response = self.client.post(
            '/user/pythonabot-notify-me', data={'email_address': 'asdf@asdf.com', 'how_excited': '6'}
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        # print(response.content.decode('utf8'))
        self.assertJSONEqual(
            response.content.decode('utf8'),
            '{"pythonabot_notify_me": "validation_error", "errors": {"email_address": true, '
            '"how_excited": [{"type": "out_of_range", "description": "The value provided is out of '
            'range."}]}, "user-api-version": "0.0.1"}',
            '/user/pythonabot-notify-me how_excited valid failed validation',
        )

        response = self.client.post(
            '/user/pythonabot-notify-me', data={'email_address': 'asdf@asdf.com', 'how_excited': '3'}
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        # print(response.content.decode('utf8'))
        self.assertJSONEqual(
            response.content.decode('utf8'),
            '{"pythonabot_notify_me": "success", "user-api-version": "0.0.1"}',
            '/user/create-account successful registration failed json validation',
        )
        self.assertEqual(Prospect.objects.count(), 1)
        new_prospect = Prospect.objects.first()
        self.assertEqual(
            new_prospect.swa_comment,
            'This prospect would like to be notified when PythonABot is ready to be purchased.',
        )

        response = self.client.post(
            '/user/pythonabot-notify-me', data={'email_address': 'asdf@asdf.com', 'how_excited': '4'}
        )
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        # print(response.content.decode('utf8'))
        self.assertJSONEqual(
            response.content.decode('utf8'),
            '{"pythonabot_notify_me": "duplicate_prospect", "errors": {"email_address": [{"type": '
            '"duplicate", "description": "I already know about this email address. Please enter a '
            'different email address."}], "how_excited": true}, "user-api-version": "0.0.1"}',
            '/user/pythonabot-notify-me duplicate prospect failed validation',
        )
