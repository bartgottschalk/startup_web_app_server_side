# Unit tests for pageview endpoint


from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from django.contrib.auth.models import User

from clientevent.models import Configuration as ClientEventConfiguration, Pageview

from StartupWebApp.utilities import unittest_utilities


class PageviewAPITest(PostgreSQLTestCase):

    def setUp(self):
        # Setup necessary DB Objects
        ClientEventConfiguration.objects.create(id=1, log_client_events=True)

        # Create test user
        self.user = User.objects.create_user(username='testuser', email='test@test.com')

    def test_authenticated_user_pageview_saved(self):
        """Test that authenticated user pageview is saved with user reference"""
        response = self.client.get('/clientevent/pageview', {
            'client_event_id': self.user.id,
            'url': 'https://example.com/test-page'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertEqual(response.content.decode('utf8'), '"thank you"',
                         'Pageview should return "thank you"')

        # Verify pageview was created
        self.assertEqual(Pageview.objects.count(), 1,
                         'Should create one pageview record')

        pageview = Pageview.objects.first()
        self.assertEqual(pageview.user, self.user,
                         'Pageview should be associated with user')
        self.assertEqual(pageview.url, 'https://example.com/test-page',
                         'URL should be saved correctly')
        self.assertIsNone(pageview.anonymous_id,
                          'Anonymous ID should be None for authenticated user')

    def test_anonymous_user_pageview_saved(self):
        """Test that anonymous user pageview is saved with anonymous_id"""
        response = self.client.get('/clientevent/pageview', {
            'anonymous_id': 'anon_12345',
            'url': 'https://example.com/test-page'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertEqual(response.content.decode('utf8'), '"thank you"')

        # Verify pageview was created
        self.assertEqual(Pageview.objects.count(), 1)

        pageview = Pageview.objects.first()
        self.assertIsNone(pageview.user,
                          'User should be None for anonymous pageview')
        self.assertEqual(pageview.anonymous_id, 'anon_12345',
                         'Anonymous ID should be saved')
        self.assertEqual(pageview.url, 'https://example.com/test-page')

    def test_pageview_without_url_not_saved(self):
        """Test that pageview without URL parameter is not saved"""
        response = self.client.get('/clientevent/pageview', {
            'client_event_id': self.user.id
            # Missing url parameter
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertEqual(response.content.decode('utf8'), '"thank you"',
                         'Should still return thank you even without URL')

        # Verify no pageview was created
        self.assertEqual(Pageview.objects.count(), 0,
                         'Should not create pageview without URL')

    def test_pageview_with_page_width_saved(self):
        """Test that page width is saved when provided"""
        response = self.client.get('/clientevent/pageview', {
            'client_event_id': self.user.id,
            'url': 'https://example.com/test-page',
            'pageWidth': '1920'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        pageview = Pageview.objects.first()
        self.assertEqual(pageview.page_width, 1920,
                         'Page width should be saved as integer')

    def test_pageview_saves_remote_addr_and_user_agent(self):
        """Test that remote IP address and user agent are saved"""
        response = self.client.get(
            '/clientevent/pageview',
            {
                'client_event_id': self.user.id,
                'url': 'https://example.com/test-page'
            },
            HTTP_USER_AGENT='Mozilla/5.0 Test Browser',
            REMOTE_ADDR='192.168.1.1'
        )

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        pageview = Pageview.objects.first()
        self.assertEqual(pageview.http_user_agent, 'Mozilla/5.0 Test Browser',
                         'User agent should be saved')
        self.assertEqual(pageview.remote_addr, '192.168.1.1',
                         'Remote address should be saved')

    def test_pageview_with_invalid_user_id_handles_gracefully(self):
        """Test that invalid user ID does not crash, saves with null user"""
        response = self.client.get('/clientevent/pageview', {
            'client_event_id': '99999',  # Non-existent user ID
            'url': 'https://example.com/test-page'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        # Should still create pageview with null user
        self.assertEqual(Pageview.objects.count(), 1)
        pageview = Pageview.objects.first()
        self.assertIsNone(pageview.user,
                          'User should be None for invalid user ID')

    def test_pageview_with_null_client_event_id(self):
        """Test that 'null' string for client_event_id is handled correctly"""
        response = self.client.get('/clientevent/pageview', {
            'client_event_id': 'null',
            'url': 'https://example.com/test-page'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        pageview = Pageview.objects.first()
        self.assertIsNone(pageview.user,
                          'User should be None when client_event_id is "null"')

    def test_pageview_created_date_time_is_set(self):
        """Test that created_date_time is automatically set"""
        before_request = timezone.now()

        response = self.client.get('/clientevent/pageview', {
            'client_event_id': self.user.id,
            'url': 'https://example.com/test-page'
        })

        after_request = timezone.now()

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        pageview = Pageview.objects.first()
        self.assertIsNotNone(pageview.created_date_time,
                             'Created date time should be set')
        self.assertGreaterEqual(pageview.created_date_time, before_request,
                                'Created time should be after request start')
        self.assertLessEqual(pageview.created_date_time, after_request,
                             'Created time should be before request end')

    def test_pageview_with_x_forwarded_for_header(self):
        """Test that X-Forwarded-For header is used for remote address if present"""
        response = self.client.get(
            '/clientevent/pageview',
            {
                'client_event_id': self.user.id,
                'url': 'https://example.com/test-page'
            },
            HTTP_X_FORWARDED_FOR='10.0.0.1',
            REMOTE_ADDR='192.168.1.1'
        )

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        pageview = Pageview.objects.first()
        self.assertEqual(pageview.remote_addr, '10.0.0.1',
                         'Should use X-Forwarded-For when present')
