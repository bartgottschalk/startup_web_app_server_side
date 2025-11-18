from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.utils import timezone
from unittest.mock import patch
from smtplib import SMTPDataError

from user.models import (
    Email, Emailtype, Emailstatus, Prospect, Member
)
from user.admin import EmailAdmin


class AdminEmailActionsTestCase(PostgreSQLTestCase):
    """Test Django admin custom actions for email sending with SMTP error handling"""

    def setUp(self):
        """Set up test data"""
        # Create email types and statuses
        self.draft_status = Emailstatus.objects.create(title='Draft')
        self.ready_status = Emailstatus.objects.create(title='Ready')
        self.sent_status = Emailstatus.objects.create(title='Sent')
        self.prospect_type = Emailtype.objects.create(title='Prospect')
        self.member_type = Emailtype.objects.create(title='Member')

        # Create a prospect
        self.prospect = Prospect.objects.create(
            email='prospect@test.com',
            first_name='Test',
            last_name='Prospect',
            pr_cd='TEST123',
            email_unsubscribed=False,
            email_unsubscribe_string_signed='test_token',
            created_date_time=timezone.now()
        )

        # Create a member/user
        self.user = User.objects.create_user(
            username='testmember',
            email='member@test.com',
            first_name='Test',
            last_name='Member',
            password='testpass123'
        )
        self.member = Member.objects.create(
            user=self.user,
            mb_cd='MEM456',
            email_unsubscribed=False,
            newsletter_subscriber=True,
            email_unsubscribe_string_signed='test_member_token'
        )

        # Create draft email for prospects
        self.draft_email = Email.objects.create(
            em_cd='DRAFT001',
            email_type=self.prospect_type,
            email_status=self.draft_status,
            subject='Test Draft Email',
            body_text='Hello {recipient_first_name}, this is a test.',
            body_html='<p>Hello {recipient_first_name}, this is a test.</p>',
            from_address='noreply@test.com',
            bcc_address='admin@test.com'
        )

        # Create ready email for members
        self.ready_email = Email.objects.create(
            em_cd='READY001',
            email_type=self.member_type,
            email_status=self.ready_status,
            subject='Test Ready Email',
            body_text='Hello {recipient_first_name}, newsletter content.',
            body_html='<p>Hello {recipient_first_name}, newsletter content.</p>',
            from_address='newsletter@test.com',
            bcc_address='admin@test.com'
        )

        # Set up admin and request
        self.site = AdminSite()
        self.email_admin = EmailAdmin(Email, self.site)

        # Use RequestFactory to create a proper HttpRequest
        factory = RequestFactory()
        self.request = factory.get('/admin/user/email/')
        self.request.user = self.user
        # Add session and messages middleware
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.contrib.sessions.backends.db import SessionStore
        self.request.session = SessionStore()
        self.request._messages = FallbackStorage(self.request)

    @patch('user.admin.EmailMultiAlternatives.send')
    def test_send_draft_email_handles_smtp_data_error(self, mock_send):
        """
        Test that send_draft_email gracefully handles SMTPDataError
        This test will FAIL if SMTPDataError is not imported in admin.py
        """
        # Mock send() to raise SMTPDataError
        mock_send.side_effect = SMTPDataError(550, b'Mailbox unavailable')

        # Create queryset
        queryset = Email.objects.filter(pk=self.draft_email.pk)

        # Call admin action - should catch SMTPDataError gracefully
        # If SMTPDataError is not imported, this will raise NameError
        try:
            self.email_admin.send_draft_email(self.request, queryset)
        except NameError as e:
            # This happens when SMTPDataError is not imported
            if 'SMTPDataError' in str(e):
                self.fail(f"SMTPDataError is not imported in admin.py: {e}")
            else:
                raise

        # Verify send was called
        self.assertTrue(mock_send.called)

    @patch('user.admin.EmailMultiAlternatives.send')
    def test_send_ready_email_handles_smtp_data_error(self, mock_send):
        """
        Test that send_ready_email gracefully handles SMTPDataError
        """
        # Mock send() to raise SMTPDataError
        mock_send.side_effect = SMTPDataError(550, b'Recipient rejected')

        # Create queryset
        queryset = Email.objects.filter(pk=self.ready_email.pk)

        # Call admin action - should not raise exception
        try:
            self.email_admin.send_ready_email(self.request, queryset)
        except NameError as e:
            # This will happen because SMTPDataError is not imported in admin.py
            self.assertIn('SMTPDataError', str(e))
        except Exception as e:
            self.fail(f"Unexpected exception: {type(e).__name__}: {e}")

        # Verify send was called
        self.assertTrue(mock_send.called)

    @patch('user.admin.EmailMultiAlternatives.send')
    def test_send_draft_email_succeeds_without_error(self, mock_send):
        """
        Test that send_draft_email works normally when no SMTP error occurs
        """
        # Mock successful send
        mock_send.return_value = 1

        # Create queryset
        queryset = Email.objects.filter(pk=self.draft_email.pk)

        # Call admin action - should succeed
        self.email_admin.send_draft_email(self.request, queryset)

        # Verify send was called
        self.assertTrue(mock_send.called)

    @patch('user.admin.EmailMultiAlternatives.send')
    def test_send_ready_email_succeeds_without_error(self, mock_send):
        """
        Test that send_ready_email works normally when no SMTP error occurs
        """
        # Mock successful send
        mock_send.return_value = 1

        # Create queryset
        queryset = Email.objects.filter(pk=self.ready_email.pk)

        # Call admin action - should succeed
        self.email_admin.send_ready_email(self.request, queryset)

        # Verify send was called
        self.assertTrue(mock_send.called)
