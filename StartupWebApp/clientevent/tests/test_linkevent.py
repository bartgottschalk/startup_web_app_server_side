# Unit tests for linkevent endpoint

import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from clientevent.models import Configuration as ClientEventConfiguration, Linkevent
from user.models import Member, Prospect, Email, Emailtype, Emailstatus, Ad, Adtype, Adstatus, Termsofuse

from StartupWebApp.utilities import unittest_utilities


class LinkeventAPITest(TestCase):

    def setUp(self):
        # Setup necessary DB Objects
        ClientEventConfiguration.objects.create(id=1, log_client_events=True)
        Group.objects.create(name='Members')
        Termsofuse.objects.create(version='1', version_note='Test Terms', publication_date_time=timezone.now())

        # Create test user and member
        self.user = User.objects.create_user(username='testuser', email='test@test.com')
        self.member = Member.objects.create(user=self.user, mb_cd='MEMBER123')

        # Create test prospect
        self.prospect = Prospect.objects.create(
            email='prospect@test.com',
            pr_cd='PROSPECT456',
            created_date_time=timezone.now()
        )

        # Create test email
        email_type = Emailtype.objects.create(title='Newsletter')
        email_status = Emailstatus.objects.create(title='Sent')
        self.email = Email.objects.create(
            subject='Test Email',
            email_type=email_type,
            email_status=email_status,
            body_html='<p>Test</p>',
            body_text='Test',
            from_address='noreply@test.com',
            bcc_address='admin@test.com',
            em_cd='EMAIL789'
        )

        # Create test ad
        ad_type = Adtype.objects.create(title='Google AdWords')
        ad_status = Adstatus.objects.create(title='Running')
        self.ad = Ad.objects.create(
            headline_1='Test Ad',
            ad_type=ad_type,
            ad_status=ad_status,
            ad_cd='AD123XYZ'
        )

    def test_linkevent_with_member_code(self):
        """Test that link event with member code associates user correctly"""
        response = self.client.get('/clientevent/linkevent', {
            'mb_cd': 'MEMBER123',
            'url': 'https://example.com/from-email'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertEqual(response.content.decode('utf8'), '"thank you"')

        # Verify linkevent was created
        self.assertEqual(Linkevent.objects.count(), 1)

        linkevent = Linkevent.objects.first()
        self.assertEqual(linkevent.user, self.user,
                        'Link event should be associated with user')
        self.assertEqual(linkevent.url, 'https://example.com/from-email')
        self.assertIsNone(linkevent.prospect)
        self.assertIsNone(linkevent.email)
        self.assertIsNone(linkevent.ad)

    def test_linkevent_with_prospect_code(self):
        """Test that link event with prospect code associates prospect correctly"""
        response = self.client.get('/clientevent/linkevent', {
            'pr_cd': 'PROSPECT456',
            'url': 'https://example.com/from-prospect-email'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        linkevent = Linkevent.objects.first()
        self.assertIsNone(linkevent.user,
                         'User should be None when only prospect code provided')
        self.assertEqual(linkevent.prospect, self.prospect,
                        'Link event should be associated with prospect')

    def test_linkevent_with_email_code(self):
        """Test that link event with email code associates email correctly"""
        response = self.client.get('/clientevent/linkevent', {
            'em_cd': 'EMAIL789',
            'url': 'https://example.com/from-email-link'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        linkevent = Linkevent.objects.first()
        self.assertEqual(linkevent.email, self.email,
                        'Link event should be associated with email')

    def test_linkevent_with_ad_code(self):
        """Test that link event with ad code associates ad correctly"""
        response = self.client.get('/clientevent/linkevent', {
            'ad_cd': 'AD123XYZ',
            'url': 'https://example.com/from-ad'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        linkevent = Linkevent.objects.first()
        self.assertEqual(linkevent.ad, self.ad,
                        'Link event should be associated with ad')

    def test_linkevent_with_anonymous_id(self):
        """Test that link event with anonymous_id is saved"""
        response = self.client.get('/clientevent/linkevent', {
            'anonymous_id': 'anon_link_789',
            'url': 'https://example.com/anonymous-link'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        linkevent = Linkevent.objects.first()
        self.assertEqual(linkevent.anonymous_id, 'anon_link_789',
                        'Anonymous ID should be saved')
        self.assertIsNone(linkevent.user)
        self.assertIsNone(linkevent.prospect)

    def test_linkevent_with_multiple_codes(self):
        """Test that link event can have multiple associations"""
        response = self.client.get('/clientevent/linkevent', {
            'mb_cd': 'MEMBER123',
            'em_cd': 'EMAIL789',
            'ad_cd': 'AD123XYZ',
            'url': 'https://example.com/complex-link'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        linkevent = Linkevent.objects.first()
        self.assertEqual(linkevent.user, self.user,
                        'Should associate with user')
        self.assertEqual(linkevent.email, self.email,
                        'Should associate with email')
        self.assertEqual(linkevent.ad, self.ad,
                        'Should associate with ad')

    def test_linkevent_without_url_not_saved(self):
        """Test that link event without URL parameter is not saved"""
        response = self.client.get('/clientevent/linkevent', {
            'mb_cd': 'MEMBER123'
            # Missing url parameter
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertEqual(response.content.decode('utf8'), '"thank you"',
                        'Should still return thank you even without URL')

        # Verify no link event was created
        self.assertEqual(Linkevent.objects.count(), 0,
                        'Should not create link event without URL')

    def test_linkevent_with_invalid_member_code_handles_gracefully(self):
        """Test that invalid member code does not crash"""
        response = self.client.get('/clientevent/linkevent', {
            'mb_cd': 'INVALID_MEMBER_CODE',
            'url': 'https://example.com/link'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        # Should still create link event but with null user
        self.assertEqual(Linkevent.objects.count(), 1)
        linkevent = Linkevent.objects.first()
        self.assertIsNone(linkevent.user,
                         'User should be None for invalid member code')

    def test_linkevent_with_invalid_prospect_code_handles_gracefully(self):
        """Test that invalid prospect code does not crash"""
        response = self.client.get('/clientevent/linkevent', {
            'pr_cd': 'INVALID_PROSPECT_CODE',
            'url': 'https://example.com/link'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        linkevent = Linkevent.objects.first()
        self.assertIsNone(linkevent.prospect,
                         'Prospect should be None for invalid prospect code')

    def test_linkevent_with_invalid_email_code_handles_gracefully(self):
        """Test that invalid email code does not crash"""
        response = self.client.get('/clientevent/linkevent', {
            'em_cd': 'INVALID_EMAIL_CODE',
            'url': 'https://example.com/link'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        linkevent = Linkevent.objects.first()
        self.assertIsNone(linkevent.email,
                         'Email should be None for invalid email code')

    def test_linkevent_with_invalid_ad_code_handles_gracefully(self):
        """Test that invalid ad code does not crash"""
        response = self.client.get('/clientevent/linkevent', {
            'ad_cd': 'INVALID_AD_CODE',
            'url': 'https://example.com/link'
        })

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        linkevent = Linkevent.objects.first()
        self.assertIsNone(linkevent.ad,
                         'Ad should be None for invalid ad code')

    def test_linkevent_created_date_time_is_set(self):
        """Test that created_date_time is automatically set"""
        before_request = timezone.now()

        response = self.client.get('/clientevent/linkevent', {
            'mb_cd': 'MEMBER123',
            'url': 'https://example.com/link'
        })

        after_request = timezone.now()

        unittest_utilities.validate_response_is_OK_and_JSON(self, response)

        linkevent = Linkevent.objects.first()
        self.assertIsNotNone(linkevent.created_date_time,
                            'Created date time should be set')
        self.assertGreaterEqual(linkevent.created_date_time, before_request,
                               'Created time should be after request start')
        self.assertLessEqual(linkevent.created_date_time, after_request,
                            'Created time should be before request end')

    def test_existing_linkevent_test_still_works(self):
        """Test that the existing linkevent test scenario still works"""
        # This replicates the existing test in test_apis.py
        response = self.client.get('/clientevent/linkevent?mb_cd=&pr_cd=&anonymous_id=&em_cd=&ad_cd=AD123XYZ&url=/clientevent/linkevent?ad_cd=AD123XYZ')
        unittest_utilities.validate_response_is_OK_and_JSON(self, response)
        self.assertEqual(response.content.decode('utf8'), '"thank you"')
        self.assertEqual(Linkevent.objects.count(), 1)

        new_linkevent = Linkevent.objects.first()
        self.assertIn('/clientevent/linkevent?ad_cd=AD123XYZ', new_linkevent.url)
        self.assertEqual(new_linkevent.ad, self.ad)
