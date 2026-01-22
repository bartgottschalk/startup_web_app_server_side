# Unit tests for order utility functions

from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from order.utilities import order_utils


class LookUpMemberCartTest(PostgreSQLTestCase):
    """Test the look_up_member_cart utility function"""

    def setUp(self):
        from django.contrib.auth.models import User, Group
        from user.models import Member, Termsofuse
        from django.utils import timezone

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

    def test_returns_member_cart_when_exists(self):
        """Test that member's cart is returned when it exists"""
        from django.test import RequestFactory
        from order.models import Cart

        # Create cart for member
        cart = Cart.objects.create(member=self.member)

        # Create request with authenticated user
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user

        result = order_utils.look_up_member_cart(request)

        self.assertIsNotNone(result)
        self.assertEqual(result.id, cart.id)
        self.assertEqual(result.member, self.member)

    def test_returns_none_when_no_cart_exists(self):
        """Test that None is returned when member has no cart"""
        from django.test import RequestFactory

        # Don't create any cart for member

        # Create request with authenticated user
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user

        result = order_utils.look_up_member_cart(request)

        self.assertIsNone(result)


class LookUpAnonymousCartTest(PostgreSQLTestCase):
    """Test the look_up_anonymous_cart utility function"""

    def test_returns_anonymous_cart_when_exists(self):
        """Test that anonymous cart is returned when cookie and cart exist"""
        from django.test import RequestFactory
        from order.models import Cart

        # Create anonymous cart
        anonymous_cart_id = 'anon_cart_123'
        cart = Cart.objects.create(anonymous_cart_id=anonymous_cart_id)

        # Create request with signed cookie
        factory = RequestFactory()
        request = factory.get('/')
        request.user = type('AnonymousUser', (), {'is_authenticated': False})()

        # Mock get_signed_cookie to return our anonymous cart ID
        request.get_signed_cookie = lambda key, default=None, salt=None: anonymous_cart_id

        result = order_utils.look_up_anonymous_cart(request)

        self.assertIsNotNone(result)
        self.assertEqual(result.id, cart.id)
        self.assertEqual(result.anonymous_cart_id, anonymous_cart_id)

    def test_returns_none_when_no_cart_exists(self):
        """Test that None is returned when cookie exists but no cart"""
        from django.test import RequestFactory

        # Don't create any cart

        # Create request with signed cookie
        factory = RequestFactory()
        request = factory.get('/')
        request.user = type('AnonymousUser', (), {'is_authenticated': False})()

        # Mock get_signed_cookie to return a cart ID that doesn't exist
        request.get_signed_cookie = lambda key, default=None, salt=None: 'nonexistent_cart'

        result = order_utils.look_up_anonymous_cart(request)

        self.assertIsNone(result)

    def test_returns_none_when_cookie_is_false(self):
        """Test that None is returned when cookie is False (default)"""
        from django.test import RequestFactory

        # Create request without signed cookie (returns False)
        factory = RequestFactory()
        request = factory.get('/')
        request.user = type('AnonymousUser', (), {'is_authenticated': False})()

        # Mock get_signed_cookie to return False (default when cookie doesn't exist)
        request.get_signed_cookie = lambda key, default=None, salt=None: False

        result = order_utils.look_up_anonymous_cart(request)

        self.assertIsNone(result)
