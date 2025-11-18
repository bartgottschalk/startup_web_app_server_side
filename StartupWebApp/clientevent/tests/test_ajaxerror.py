# Unit tests for ajaxerror endpoint


from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from django.contrib.auth.models import User

from clientevent.models import Configuration as ClientEventConfiguration, AJAXError

from StartupWebApp.utilities import unittest_utilities


class AJAXErrorAPITest(PostgreSQLTestCase):

    def setUp(self):
        # Setup necessary DB Objects
        ClientEventConfiguration.objects.create(id=1, log_client_events=True)

        # Create test user
        self.user = User.objects.create_user(username='testuser', email='test@test.com')

    def test_authenticated_user_ajax_error_saved(self):
        """Test that authenticated user AJAX error is saved with user reference"""
        response = self.client.get('/clientevent/ajaxerror', {
            'client_event_id': self.user.id,
            'url': 'https://example.com/page-with-error',
            'error_id': 'ERR_NETWORK_TIMEOUT'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertEqual(response.content.decode('utf8'), '"thank you"',
                         'AJAX error should return "thank you"')

        # Verify AJAX error was created
        self.assertEqual(AJAXError.objects.count(), 1,
                         'Should create one AJAX error record')

        ajax_error = AJAXError.objects.first()
        self.assertEqual(ajax_error.user, self.user,
                         'AJAX error should be associated with user')
        self.assertEqual(ajax_error.url, 'https://example.com/page-with-error',
                         'URL should be saved correctly')
        self.assertEqual(ajax_error.error_id, 'ERR_NETWORK_TIMEOUT',
                         'Error ID should be saved')
        self.assertIsNone(ajax_error.anonymous_id,
                          'Anonymous ID should be None for authenticated user')

    def test_anonymous_user_ajax_error_saved(self):
        """Test that anonymous user AJAX error is saved with anonymous_id"""
        response = self.client.get('/clientevent/ajaxerror', {
            'anonymous_id': 'anon_67890',
            'url': 'https://example.com/page-with-error',
            'error_id': 'ERR_API_FAILED'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertEqual(response.content.decode('utf8'), '"thank you"')

        # Verify AJAX error was created
        self.assertEqual(AJAXError.objects.count(), 1)

        ajax_error = AJAXError.objects.first()
        self.assertIsNone(ajax_error.user,
                          'User should be None for anonymous AJAX error')
        self.assertEqual(ajax_error.anonymous_id, 'anon_67890',
                         'Anonymous ID should be saved')
        self.assertEqual(ajax_error.error_id, 'ERR_API_FAILED')

    def test_ajax_error_without_url_not_saved(self):
        """Test that AJAX error without URL parameter is not saved"""
        response = self.client.get('/clientevent/ajaxerror', {
            'client_event_id': self.user.id,
            'error_id': 'ERR_SOMETHING'
            # Missing url parameter
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertEqual(response.content.decode('utf8'), '"thank you"',
                         'Should still return thank you even without URL')

        # Verify no AJAX error was created
        self.assertEqual(AJAXError.objects.count(), 0,
                         'Should not create AJAX error without URL')

    def test_ajax_error_with_invalid_user_id_handles_gracefully(self):
        """Test that invalid user ID does not crash, saves with null user"""
        response = self.client.get('/clientevent/ajaxerror', {
            'client_event_id': '99999',  # Non-existent user ID
            'url': 'https://example.com/page-with-error',
            'error_id': 'ERR_TEST'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        # Should still create AJAX error with null user
        self.assertEqual(AJAXError.objects.count(), 1)
        ajax_error = AJAXError.objects.first()
        self.assertIsNone(ajax_error.user,
                          'User should be None for invalid user ID')

    def test_ajax_error_id_saved_correctly(self):
        """Test that error_id is saved correctly"""
        response = self.client.get('/clientevent/ajaxerror', {
            'client_event_id': self.user.id,
            'url': 'https://example.com/error',
            'error_id': 'ERR_CUSTOM_12345'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        ajax_error = AJAXError.objects.first()
        self.assertEqual(ajax_error.error_id, 'ERR_CUSTOM_12345',
                         'Error ID should match exactly what was sent')

    def test_ajax_error_created_date_time_is_set(self):
        """Test that created_date_time is automatically set"""
        before_request = timezone.now()

        response = self.client.get('/clientevent/ajaxerror', {
            'client_event_id': self.user.id,
            'url': 'https://example.com/error',
            'error_id': 'ERR_TEST'
        })

        after_request = timezone.now()

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        ajax_error = AJAXError.objects.first()
        self.assertIsNotNone(ajax_error.created_date_time,
                             'Created date time should be set')
        self.assertGreaterEqual(ajax_error.created_date_time, before_request,
                                'Created time should be after request start')
        self.assertLessEqual(ajax_error.created_date_time, after_request,
                             'Created time should be before request end')

    def test_multiple_ajax_errors_can_be_tracked(self):
        """Test that multiple AJAX errors can be tracked independently"""
        # Create first error
        self.client.get('/clientevent/ajaxerror', {
            'client_event_id': self.user.id,
            'url': 'https://example.com/page1',
            'error_id': 'ERR_FIRST'
        })

        # Create second error
        self.client.get('/clientevent/ajaxerror', {
            'anonymous_id': 'anon_123',
            'url': 'https://example.com/page2',
            'error_id': 'ERR_SECOND'
        })

        self.assertEqual(AJAXError.objects.count(), 2,
                         'Should track multiple AJAX errors')

        error_ids = list(AJAXError.objects.values_list('error_id', flat=True))
        self.assertIn('ERR_FIRST', error_ids)
        self.assertIn('ERR_SECOND', error_ids)
