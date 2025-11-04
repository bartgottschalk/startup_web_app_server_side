# Unit tests for buttonclick endpoint

import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User

from clientevent.models import Configuration as ClientEventConfiguration, Buttonclick

from StartupWebApp.utilities import unittest_utilities


class ButtonclickAPITest(TestCase):

    def setUp(self):
        # Setup necessary DB Objects
        ClientEventConfiguration.objects.create(id=1, log_client_events=True)

        # Create test user
        self.user = User.objects.create_user(username='testuser', email='test@test.com')

    def test_authenticated_user_button_click_saved(self):
        """Test that authenticated user button click is saved with user reference"""
        response = self.client.get('/clientevent/buttonclick', {
            'client_event_id': self.user.id,
            'url': 'https://example.com/products',
            'button_id': 'add-to-cart-btn'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertEqual(response.content.decode('utf8'), '"thank you"',
                        'Button click should return "thank you"')

        # Verify button click was created
        self.assertEqual(Buttonclick.objects.count(), 1,
                        'Should create one button click record')

        buttonclick = Buttonclick.objects.first()
        self.assertEqual(buttonclick.user, self.user,
                        'Button click should be associated with user')
        self.assertEqual(buttonclick.url, 'https://example.com/products',
                        'URL should be saved correctly')
        self.assertEqual(buttonclick.button_id, 'add-to-cart-btn',
                        'Button ID should be saved')
        self.assertIsNone(buttonclick.anonymous_id,
                         'Anonymous ID should be None for authenticated user')

    def test_anonymous_user_button_click_saved(self):
        """Test that anonymous user button click is saved with anonymous_id"""
        response = self.client.get('/clientevent/buttonclick', {
            'anonymous_id': 'anon_click_123',
            'url': 'https://example.com/checkout',
            'button_id': 'checkout-now-btn'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertEqual(response.content.decode('utf8'), '"thank you"')

        # Verify button click was created
        self.assertEqual(Buttonclick.objects.count(), 1)

        buttonclick = Buttonclick.objects.first()
        self.assertIsNone(buttonclick.user,
                         'User should be None for anonymous button click')
        self.assertEqual(buttonclick.anonymous_id, 'anon_click_123',
                        'Anonymous ID should be saved')
        self.assertEqual(buttonclick.button_id, 'checkout-now-btn')

    def test_button_click_without_url_not_saved(self):
        """Test that button click without URL parameter is not saved"""
        response = self.client.get('/clientevent/buttonclick', {
            'client_event_id': self.user.id,
            'button_id': 'some-button'
            # Missing url parameter
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertEqual(response.content.decode('utf8'), '"thank you"',
                        'Should still return thank you even without URL')

        # Verify no button click was created
        self.assertEqual(Buttonclick.objects.count(), 0,
                        'Should not create button click without URL')

    def test_button_click_with_invalid_user_id_handles_gracefully(self):
        """Test that invalid user ID does not crash, saves with null user"""
        response = self.client.get('/clientevent/buttonclick', {
            'client_event_id': '99999',  # Non-existent user ID
            'url': 'https://example.com/page',
            'button_id': 'test-btn'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        # Should still create button click with null user
        self.assertEqual(Buttonclick.objects.count(), 1)
        buttonclick = Buttonclick.objects.first()
        self.assertIsNone(buttonclick.user,
                         'User should be None for invalid user ID')

    def test_button_id_saved_correctly(self):
        """Test that button_id is saved correctly"""
        response = self.client.get('/clientevent/buttonclick', {
            'client_event_id': self.user.id,
            'url': 'https://example.com/home',
            'button_id': 'subscribe-newsletter-btn-123'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        buttonclick = Buttonclick.objects.first()
        self.assertEqual(buttonclick.button_id, 'subscribe-newsletter-btn-123',
                        'Button ID should match exactly what was sent')

    def test_button_click_created_date_time_is_set(self):
        """Test that created_date_time is automatically set"""
        before_request = timezone.now()

        response = self.client.get('/clientevent/buttonclick', {
            'client_event_id': self.user.id,
            'url': 'https://example.com/page',
            'button_id': 'test-btn'
        })

        after_request = timezone.now()

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        buttonclick = Buttonclick.objects.first()
        self.assertIsNotNone(buttonclick.created_date_time,
                            'Created date time should be set')
        self.assertGreaterEqual(buttonclick.created_date_time, before_request,
                               'Created time should be after request start')
        self.assertLessEqual(buttonclick.created_date_time, after_request,
                            'Created time should be before request end')

    def test_multiple_button_clicks_can_be_tracked(self):
        """Test that multiple button clicks can be tracked independently"""
        # Create first button click
        self.client.get('/clientevent/buttonclick', {
            'client_event_id': self.user.id,
            'url': 'https://example.com/home',
            'button_id': 'btn-1'
        })

        # Create second button click
        self.client.get('/clientevent/buttonclick', {
            'anonymous_id': 'anon_456',
            'url': 'https://example.com/products',
            'button_id': 'btn-2'
        })

        self.assertEqual(Buttonclick.objects.count(), 2,
                        'Should track multiple button clicks')

        button_ids = list(Buttonclick.objects.values_list('button_id', flat=True))
        self.assertIn('btn-1', button_ids)
        self.assertIn('btn-2', button_ids)

    def test_button_click_on_same_button_multiple_times(self):
        """Test that same button can be clicked multiple times"""
        # First click
        self.client.get('/clientevent/buttonclick', {
            'client_event_id': self.user.id,
            'url': 'https://example.com/page',
            'button_id': 'same-button'
        })

        # Second click on same button
        self.client.get('/clientevent/buttonclick', {
            'client_event_id': self.user.id,
            'url': 'https://example.com/page',
            'button_id': 'same-button'
        })

        self.assertEqual(Buttonclick.objects.count(), 2,
                        'Should track each click separately')

        # Both should have same button_id
        button_ids = list(Buttonclick.objects.values_list('button_id', flat=True))
        self.assertEqual(button_ids, ['same-button', 'same-button'],
                        'Both clicks should have same button_id')
