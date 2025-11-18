# Database constraint tests for clientevent models
# Focus on null/blank validation, max_length, and required fields

from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.db import IntegrityError

from clientevent.models import Pageview, AJAXError, Buttonclick, Linkevent
from user.models import Member, Prospect, Email, Emailtype, Emailstatus, Ad, Adtype, Adstatus, Termsofuse


class PageviewFieldConstraintTest(PostgreSQLTestCase):
    """Test Pageview model field constraints"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@test.com')

    def test_pageview_url_allows_empty_string(self):
        """Test that Pageview url allows empty string (CharField default behavior)"""
        # Django CharField allows empty strings by default
        pageview = Pageview.objects.create(
            user=self.user,
            url='',  # Empty string allowed
            created_date_time=timezone.now()
        )

        self.assertEqual(pageview.url, '')

    def test_pageview_created_date_time_is_required(self):
        """Test that Pageview requires created_date_time"""
        with self.assertRaises((IntegrityError, TypeError)):
            Pageview.objects.create(
                user=self.user,
                url='https://example.com/test'
                # missing created_date_time (required field)
            )

    def test_pageview_user_is_nullable(self):
        """Test that Pageview user field is nullable"""
        pageview = Pageview.objects.create(
            user=None,  # Nullable
            anonymous_id='anon_123',
            url='https://example.com/test',
            created_date_time=timezone.now()
        )

        self.assertIsNone(pageview.user)

    def test_pageview_anonymous_id_is_nullable(self):
        """Test that Pageview anonymous_id is nullable"""
        pageview = Pageview.objects.create(
            user=self.user,
            anonymous_id=None,  # Nullable
            url='https://example.com/test',
            created_date_time=timezone.now()
        )

        self.assertIsNone(pageview.anonymous_id)

    def test_pageview_page_width_is_nullable(self):
        """Test that Pageview page_width is nullable and blank"""
        pageview = Pageview.objects.create(
            user=self.user,
            url='https://example.com/test',
            page_width=None,  # Nullable, blank=True
            created_date_time=timezone.now()
        )

        self.assertIsNone(pageview.page_width)

    def test_pageview_remote_addr_is_nullable(self):
        """Test that Pageview remote_addr is nullable and blank"""
        pageview = Pageview.objects.create(
            user=self.user,
            url='https://example.com/test',
            remote_addr=None,  # Nullable, blank=True
            created_date_time=timezone.now()
        )

        self.assertIsNone(pageview.remote_addr)

    def test_pageview_http_user_agent_is_nullable(self):
        """Test that Pageview http_user_agent is nullable and blank"""
        pageview = Pageview.objects.create(
            user=self.user,
            url='https://example.com/test',
            http_user_agent=None,  # Nullable, blank=True
            created_date_time=timezone.now()
        )

        self.assertIsNone(pageview.http_user_agent)


class PageviewMaxLengthTest(PostgreSQLTestCase):
    """Test Pageview model max_length constraints"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@test.com')

    def test_pageview_anonymous_id_max_length(self):
        """Test that Pageview anonymous_id has 100 char limit"""
        pageview = Pageview.objects.create(
            user=self.user,
            anonymous_id='a' * 100,  # max 100
            url='https://example.com/test',
            created_date_time=timezone.now()
        )

        self.assertEqual(len(pageview.anonymous_id), 100)

    def test_pageview_url_max_length(self):
        """Test that Pageview url has 1000 char limit"""
        long_url = 'https://example.com/' + 'x' * 980  # Total 1000 chars
        pageview = Pageview.objects.create(
            user=self.user,
            url=long_url,
            created_date_time=timezone.now()
        )

        self.assertEqual(len(pageview.url), 1000)

    def test_pageview_remote_addr_max_length(self):
        """Test that Pageview remote_addr has 100 char limit"""
        pageview = Pageview.objects.create(
            user=self.user,
            url='https://example.com/test',
            remote_addr='b' * 100,  # max 100
            created_date_time=timezone.now()
        )

        self.assertEqual(len(pageview.remote_addr), 100)

    def test_pageview_http_user_agent_max_length(self):
        """Test that Pageview http_user_agent has 1000 char limit"""
        long_user_agent = 'Mozilla/' + 'y' * 992  # Total 1000 chars (8 + 992)
        pageview = Pageview.objects.create(
            user=self.user,
            url='https://example.com/test',
            http_user_agent=long_user_agent,
            created_date_time=timezone.now()
        )

        self.assertEqual(len(pageview.http_user_agent), 1000)


class AJAXErrorFieldConstraintTest(PostgreSQLTestCase):
    """Test AJAXError model field constraints"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@test.com')

    def test_ajaxerror_url_allows_empty_string(self):
        """Test that AJAXError url allows empty string (CharField default behavior)"""
        ajax_error = AJAXError.objects.create(
            user=self.user,
            url='',  # Empty string allowed
            error_id='ERR_TEST',
            created_date_time=timezone.now()
        )

        self.assertEqual(ajax_error.url, '')

    def test_ajaxerror_error_id_allows_empty_string(self):
        """Test that AJAXError error_id allows empty string (CharField default behavior)"""
        ajax_error = AJAXError.objects.create(
            user=self.user,
            url='https://example.com/test',
            error_id='',  # Empty string allowed
            created_date_time=timezone.now()
        )

        self.assertEqual(ajax_error.error_id, '')

    def test_ajaxerror_created_date_time_is_required(self):
        """Test that AJAXError requires created_date_time"""
        with self.assertRaises((IntegrityError, TypeError)):
            AJAXError.objects.create(
                user=self.user,
                url='https://example.com/test',
                error_id='ERR_TEST'
                # missing created_date_time (required field)
            )

    def test_ajaxerror_user_is_nullable(self):
        """Test that AJAXError user field is nullable"""
        ajax_error = AJAXError.objects.create(
            user=None,  # Nullable
            anonymous_id='anon_456',
            url='https://example.com/error',
            error_id='ERR_TEST',
            created_date_time=timezone.now()
        )

        self.assertIsNone(ajax_error.user)

    def test_ajaxerror_anonymous_id_is_nullable(self):
        """Test that AJAXError anonymous_id is nullable"""
        ajax_error = AJAXError.objects.create(
            user=self.user,
            anonymous_id=None,  # Nullable
            url='https://example.com/error',
            error_id='ERR_TEST',
            created_date_time=timezone.now()
        )

        self.assertIsNone(ajax_error.anonymous_id)


class AJAXErrorMaxLengthTest(PostgreSQLTestCase):
    """Test AJAXError model max_length constraints"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@test.com')

    def test_ajaxerror_anonymous_id_max_length(self):
        """Test that AJAXError anonymous_id has 100 char limit"""
        ajax_error = AJAXError.objects.create(
            user=self.user,
            anonymous_id='c' * 100,  # max 100
            url='https://example.com/error',
            error_id='ERR_TEST',
            created_date_time=timezone.now()
        )

        self.assertEqual(len(ajax_error.anonymous_id), 100)

    def test_ajaxerror_url_max_length(self):
        """Test that AJAXError url has 1000 char limit"""
        long_url = 'https://example.com/error/' + 'x' * 974  # Total 1000 chars (26 + 974)
        ajax_error = AJAXError.objects.create(
            user=self.user,
            url=long_url,
            error_id='ERR_TEST',
            created_date_time=timezone.now()
        )

        self.assertEqual(len(ajax_error.url), 1000)

    def test_ajaxerror_error_id_max_length(self):
        """Test that AJAXError error_id has 100 char limit"""
        ajax_error = AJAXError.objects.create(
            user=self.user,
            url='https://example.com/error',
            error_id='d' * 100,  # max 100
            created_date_time=timezone.now()
        )

        self.assertEqual(len(ajax_error.error_id), 100)


class ButtonclickFieldConstraintTest(PostgreSQLTestCase):
    """Test Buttonclick model field constraints"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@test.com')

    def test_buttonclick_url_allows_empty_string(self):
        """Test that Buttonclick url allows empty string (CharField default behavior)"""
        buttonclick = Buttonclick.objects.create(
            user=self.user,
            url='',  # Empty string allowed
            button_id='test-btn',
            created_date_time=timezone.now()
        )

        self.assertEqual(buttonclick.url, '')

    def test_buttonclick_button_id_allows_empty_string(self):
        """Test that Buttonclick button_id allows empty string (CharField default behavior)"""
        buttonclick = Buttonclick.objects.create(
            user=self.user,
            url='https://example.com/test',
            button_id='',  # Empty string allowed
            created_date_time=timezone.now()
        )

        self.assertEqual(buttonclick.button_id, '')

    def test_buttonclick_created_date_time_is_required(self):
        """Test that Buttonclick requires created_date_time"""
        with self.assertRaises((IntegrityError, TypeError)):
            Buttonclick.objects.create(
                user=self.user,
                url='https://example.com/test',
                button_id='test-btn'
                # missing created_date_time (required field)
            )

    def test_buttonclick_user_is_nullable(self):
        """Test that Buttonclick user field is nullable"""
        buttonclick = Buttonclick.objects.create(
            user=None,  # Nullable
            anonymous_id='anon_789',
            url='https://example.com/test',
            button_id='test-btn',
            created_date_time=timezone.now()
        )

        self.assertIsNone(buttonclick.user)

    def test_buttonclick_anonymous_id_is_nullable(self):
        """Test that Buttonclick anonymous_id is nullable"""
        buttonclick = Buttonclick.objects.create(
            user=self.user,
            anonymous_id=None,  # Nullable
            url='https://example.com/test',
            button_id='test-btn',
            created_date_time=timezone.now()
        )

        self.assertIsNone(buttonclick.anonymous_id)


class ButtonclickMaxLengthTest(PostgreSQLTestCase):
    """Test Buttonclick model max_length constraints"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@test.com')

    def test_buttonclick_anonymous_id_max_length(self):
        """Test that Buttonclick anonymous_id has 100 char limit"""
        buttonclick = Buttonclick.objects.create(
            user=self.user,
            anonymous_id='e' * 100,  # max 100
            url='https://example.com/test',
            button_id='test-btn',
            created_date_time=timezone.now()
        )

        self.assertEqual(len(buttonclick.anonymous_id), 100)

    def test_buttonclick_url_max_length(self):
        """Test that Buttonclick url has 1000 char limit"""
        long_url = 'https://example.com/page/' + 'x' * 975  # Total 1000 chars
        buttonclick = Buttonclick.objects.create(
            user=self.user,
            url=long_url,
            button_id='test-btn',
            created_date_time=timezone.now()
        )

        self.assertEqual(len(buttonclick.url), 1000)

    def test_buttonclick_button_id_max_length(self):
        """Test that Buttonclick button_id has 100 char limit"""
        buttonclick = Buttonclick.objects.create(
            user=self.user,
            url='https://example.com/test',
            button_id='f' * 100,  # max 100
            created_date_time=timezone.now()
        )

        self.assertEqual(len(buttonclick.button_id), 100)


class LinkeventFieldConstraintTest(PostgreSQLTestCase):
    """Test Linkevent model field constraints"""

    def setUp(self):
        Group.objects.create(name='Members')
        Termsofuse.objects.create(
            version='1',
            version_note='Test',
            publication_date_time=timezone.now())

        self.user = User.objects.create_user(username='testuser', email='test@test.com')
        self.member = Member.objects.create(user=self.user, mb_cd='MEMBER123')

        self.prospect = Prospect.objects.create(
            email='prospect@test.com',
            pr_cd='PROSPECT456',
            created_date_time=timezone.now()
        )

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

        ad_type = Adtype.objects.create(title='Google AdWords')
        ad_status = Adstatus.objects.create(title='Running')
        self.ad = Ad.objects.create(
            headline_1='Test Ad',
            ad_type=ad_type,
            ad_status=ad_status,
            ad_cd='AD123'
        )

    def test_linkevent_url_allows_empty_string(self):
        """Test that Linkevent url allows empty string (CharField default behavior)"""
        linkevent = Linkevent.objects.create(
            user=self.user,
            url='',  # Empty string allowed
            created_date_time=timezone.now()
        )

        self.assertEqual(linkevent.url, '')

    def test_linkevent_created_date_time_is_required(self):
        """Test that Linkevent requires created_date_time"""
        with self.assertRaises((IntegrityError, TypeError)):
            Linkevent.objects.create(
                user=self.user,
                url='https://example.com/link'
                # missing created_date_time (required field)
            )

    def test_linkevent_user_is_nullable(self):
        """Test that Linkevent user field is nullable"""
        linkevent = Linkevent.objects.create(
            user=None,  # Nullable
            url='https://example.com/link',
            created_date_time=timezone.now()
        )

        self.assertIsNone(linkevent.user)

    def test_linkevent_prospect_is_nullable(self):
        """Test that Linkevent prospect field is nullable"""
        linkevent = Linkevent.objects.create(
            user=self.user,
            prospect=None,  # Nullable
            url='https://example.com/link',
            created_date_time=timezone.now()
        )

        self.assertIsNone(linkevent.prospect)

    def test_linkevent_anonymous_id_is_nullable(self):
        """Test that Linkevent anonymous_id is nullable"""
        linkevent = Linkevent.objects.create(
            user=self.user,
            anonymous_id=None,  # Nullable
            url='https://example.com/link',
            created_date_time=timezone.now()
        )

        self.assertIsNone(linkevent.anonymous_id)

    def test_linkevent_email_is_nullable(self):
        """Test that Linkevent email field is nullable"""
        linkevent = Linkevent.objects.create(
            user=self.user,
            email=None,  # Nullable
            url='https://example.com/link',
            created_date_time=timezone.now()
        )

        self.assertIsNone(linkevent.email)

    def test_linkevent_ad_is_nullable(self):
        """Test that Linkevent ad field is nullable"""
        linkevent = Linkevent.objects.create(
            user=self.user,
            ad=None,  # Nullable
            url='https://example.com/link',
            created_date_time=timezone.now()
        )

        self.assertIsNone(linkevent.ad)


class LinkeventMaxLengthTest(PostgreSQLTestCase):
    """Test Linkevent model max_length constraints"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@test.com')

    def test_linkevent_anonymous_id_max_length(self):
        """Test that Linkevent anonymous_id has 100 char limit"""
        linkevent = Linkevent.objects.create(
            user=self.user,
            anonymous_id='g' * 100,  # max 100
            url='https://example.com/link',
            created_date_time=timezone.now()
        )

        self.assertEqual(len(linkevent.anonymous_id), 100)

    def test_linkevent_url_max_length(self):
        """Test that Linkevent url has 1000 char limit"""
        long_url = 'https://example.com/link/' + 'x' * 975  # Total 1000 chars
        linkevent = Linkevent.objects.create(
            user=self.user,
            url=long_url,
            created_date_time=timezone.now()
        )

        self.assertEqual(len(linkevent.url), 1000)
