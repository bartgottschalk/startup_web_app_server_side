# Unit tests for clientevent models


from django.test import TestCase
from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group

from clientevent.models import Configuration, Pageview, AJAXError, Buttonclick, Linkevent
from user.models import Member, Prospect, Email, Emailtype, Emailstatus, Ad, Adtype, Adstatus, Termsofuse


class ConfigurationModelTest(PostgreSQLTestCase):
    """Test Configuration model creation and behavior"""

    def test_configuration_creation(self):
        """Test that Configuration can be created"""
        config = Configuration.objects.create(log_client_events=True)

        self.assertTrue(config.log_client_events)
        self.assertIsNotNone(config.id)

    def test_configuration_default_value(self):
        """Test that Configuration has correct default value"""
        config = Configuration.objects.create()

        self.assertTrue(config.log_client_events,
                        'log_client_events should default to True')

    def test_configuration_str_representation(self):
        """Test that Configuration __str__ returns expected format"""
        config = Configuration.objects.create(log_client_events=True)

        expected = 'log_client_events: True'
        self.assertEqual(str(config), expected)

        config.log_client_events = False
        config.save()

        expected = 'log_client_events: False'
        self.assertEqual(str(config), expected)

    def test_configuration_custom_table_name(self):
        """Test that Configuration uses custom table name"""
        config = Configuration.objects.create(log_client_events=True)

        self.assertEqual(config._meta.db_table, 'clientevent_configuration')


class PageviewModelTest(PostgreSQLTestCase):
    """Test Pageview model creation and relationships"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@test.com')

    def test_pageview_creation_with_user(self):
        """Test that Pageview can be created with user"""
        pageview = Pageview.objects.create(
            user=self.user,
            url='https://example.com/test',
            page_width=1920,
            remote_addr='192.168.1.1',
            http_user_agent='Mozilla/5.0',
            created_date_time=timezone.now()
        )

        self.assertEqual(pageview.user, self.user)
        self.assertEqual(pageview.url, 'https://example.com/test')
        self.assertEqual(pageview.page_width, 1920)
        self.assertIsNotNone(pageview.id)

    def test_pageview_creation_with_anonymous_id(self):
        """Test that Pageview can be created with anonymous_id"""
        pageview = Pageview.objects.create(
            user=None,
            anonymous_id='anon_123',
            url='https://example.com/page',
            created_date_time=timezone.now()
        )

        self.assertIsNone(pageview.user)
        self.assertEqual(pageview.anonymous_id, 'anon_123')

    def test_pageview_str_representation(self):
        """Test that Pageview __str__ returns expected format"""
        pageview = Pageview.objects.create(
            user=self.user,
            anonymous_id='anon_456',
            url='https://example.com/test',
            remote_addr='192.168.1.1',
            created_date_time=timezone.now()
        )

        result = str(pageview)
        self.assertIn(str(self.user.id), result)
        self.assertIn('anon_456', result)
        self.assertIn('https://example.com/test', result)
        self.assertIn('192.168.1.1', result)

    def test_pageview_custom_table_name(self):
        """Test that Pageview uses custom table name"""
        pageview = Pageview.objects.create(
            user=self.user,
            url='https://example.com/test',
            created_date_time=timezone.now()
        )

        self.assertEqual(pageview._meta.db_table, 'clientevent_pageview')

    def test_pageview_set_null_on_user_deletion(self):
        """Test that pageview.user is set to NULL when user is deleted"""
        pageview = Pageview.objects.create(
            user=self.user,
            url='https://example.com/test',
            created_date_time=timezone.now()
        )
        pageview_id = pageview.id

        # Delete user
        self.user.delete()

        # Verify pageview still exists but user is NULL
        pageview.refresh_from_db()
        self.assertIsNone(pageview.user,
                          'User should be set to NULL after user deletion')
        self.assertTrue(Pageview.objects.filter(id=pageview_id).exists(),
                        'Pageview should not be deleted')


class AJAXErrorModelTest(PostgreSQLTestCase):
    """Test AJAXError model creation and relationships"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@test.com')

    def test_ajaxerror_creation_with_user(self):
        """Test that AJAXError can be created with user"""
        ajax_error = AJAXError.objects.create(
            user=self.user,
            url='https://example.com/error-page',
            error_id='ERR_TIMEOUT',
            created_date_time=timezone.now()
        )

        self.assertEqual(ajax_error.user, self.user)
        self.assertEqual(ajax_error.error_id, 'ERR_TIMEOUT')
        self.assertIsNotNone(ajax_error.id)

    def test_ajaxerror_creation_with_anonymous_id(self):
        """Test that AJAXError can be created with anonymous_id"""
        ajax_error = AJAXError.objects.create(
            user=None,
            anonymous_id='anon_error_789',
            url='https://example.com/error',
            error_id='ERR_NETWORK',
            created_date_time=timezone.now()
        )

        self.assertIsNone(ajax_error.user)
        self.assertEqual(ajax_error.anonymous_id, 'anon_error_789')

    def test_ajaxerror_str_representation(self):
        """Test that AJAXError __str__ returns expected format"""
        ajax_error = AJAXError.objects.create(
            user=self.user,
            anonymous_id='anon_err',
            url='https://example.com/error',
            error_id='ERR_TEST',
            created_date_time=timezone.now()
        )

        result = str(ajax_error)
        self.assertIn(str(self.user.id), result)
        self.assertIn('anon_err', result)
        self.assertIn('https://example.com/error', result)
        self.assertIn('ERR_TEST', result)

    def test_ajaxerror_custom_table_name(self):
        """Test that AJAXError uses custom table name"""
        ajax_error = AJAXError.objects.create(
            user=self.user,
            url='https://example.com/error',
            error_id='ERR_TEST',
            created_date_time=timezone.now()
        )

        self.assertEqual(ajax_error._meta.db_table, 'clientevent_ajax_error')

    def test_ajaxerror_set_null_on_user_deletion(self):
        """Test that ajaxerror.user is set to NULL when user is deleted"""
        ajax_error = AJAXError.objects.create(
            user=self.user,
            url='https://example.com/error',
            error_id='ERR_TEST',
            created_date_time=timezone.now()
        )
        ajax_error_id = ajax_error.id

        # Delete user
        self.user.delete()

        # Verify ajax_error still exists but user is NULL
        ajax_error.refresh_from_db()
        self.assertIsNone(ajax_error.user,
                          'User should be set to NULL after user deletion')
        self.assertTrue(AJAXError.objects.filter(id=ajax_error_id).exists(),
                        'AJAXError should not be deleted')


class ButtonclickModelTest(PostgreSQLTestCase):
    """Test Buttonclick model creation and relationships"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@test.com')

    def test_buttonclick_creation_with_user(self):
        """Test that Buttonclick can be created with user"""
        buttonclick = Buttonclick.objects.create(
            user=self.user,
            url='https://example.com/page',
            button_id='checkout-btn',
            created_date_time=timezone.now()
        )

        self.assertEqual(buttonclick.user, self.user)
        self.assertEqual(buttonclick.button_id, 'checkout-btn')
        self.assertIsNotNone(buttonclick.id)

    def test_buttonclick_creation_with_anonymous_id(self):
        """Test that Buttonclick can be created with anonymous_id"""
        buttonclick = Buttonclick.objects.create(
            user=None,
            anonymous_id='anon_click_999',
            url='https://example.com/product',
            button_id='add-to-cart-btn',
            created_date_time=timezone.now()
        )

        self.assertIsNone(buttonclick.user)
        self.assertEqual(buttonclick.anonymous_id, 'anon_click_999')

    def test_buttonclick_str_representation(self):
        """Test that Buttonclick __str__ returns expected format"""
        buttonclick = Buttonclick.objects.create(
            user=self.user,
            anonymous_id='anon_btn',
            url='https://example.com/page',
            button_id='test-button',
            created_date_time=timezone.now()
        )

        result = str(buttonclick)
        self.assertIn(str(self.user.id), result)
        self.assertIn('anon_btn', result)
        self.assertIn('https://example.com/page', result)
        self.assertIn('test-button', result)

    def test_buttonclick_custom_table_name(self):
        """Test that Buttonclick uses custom table name"""
        buttonclick = Buttonclick.objects.create(
            user=self.user,
            url='https://example.com/page',
            button_id='test-btn',
            created_date_time=timezone.now()
        )

        self.assertEqual(buttonclick._meta.db_table, 'clientevent_button_click')

    def test_buttonclick_set_null_on_user_deletion(self):
        """Test that buttonclick.user is set to NULL when user is deleted"""
        buttonclick = Buttonclick.objects.create(
            user=self.user,
            url='https://example.com/page',
            button_id='test-btn',
            created_date_time=timezone.now()
        )
        buttonclick_id = buttonclick.id

        # Delete user
        self.user.delete()

        # Verify buttonclick still exists but user is NULL
        buttonclick.refresh_from_db()
        self.assertIsNone(buttonclick.user,
                          'User should be set to NULL after user deletion')
        self.assertTrue(Buttonclick.objects.filter(id=buttonclick_id).exists(),
                        'Buttonclick should not be deleted')


class LinkeventModelTest(PostgreSQLTestCase):
    """Test Linkevent model creation and relationships"""

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

    def test_linkevent_creation_with_all_relationships(self):
        """Test that Linkevent can be created with all foreign keys"""
        linkevent = Linkevent.objects.create(
            user=self.user,
            prospect=self.prospect,
            anonymous_id='anon_link_123',
            email=self.email,
            ad=self.ad,
            url='https://example.com/link',
            created_date_time=timezone.now()
        )

        self.assertEqual(linkevent.user, self.user)
        self.assertEqual(linkevent.prospect, self.prospect)
        self.assertEqual(linkevent.email, self.email)
        self.assertEqual(linkevent.ad, self.ad)
        self.assertEqual(linkevent.anonymous_id, 'anon_link_123')
        self.assertIsNotNone(linkevent.id)

    def test_linkevent_str_representation(self):
        """Test that Linkevent __str__ returns expected format"""
        linkevent = Linkevent.objects.create(
            user=self.user,
            prospect=self.prospect,
            anonymous_id='anon_999',
            url='https://example.com/link',
            created_date_time=timezone.now()
        )

        result = str(linkevent)
        self.assertIn(str(self.user.id), result)
        self.assertIn(str(self.prospect), result)
        self.assertIn('anon_999', result)
        self.assertIn('https://example.com/link', result)

    def test_linkevent_custom_table_name(self):
        """Test that Linkevent uses custom table name"""
        linkevent = Linkevent.objects.create(
            user=self.user,
            url='https://example.com/link',
            created_date_time=timezone.now()
        )

        self.assertEqual(linkevent._meta.db_table, 'clientevent_linkevent')

    def test_linkevent_set_null_on_user_deletion(self):
        """Test that linkevent.user is set to NULL when user is deleted"""
        linkevent = Linkevent.objects.create(
            user=self.user,
            url='https://example.com/link',
            created_date_time=timezone.now()
        )
        linkevent_id = linkevent.id

        # Delete user (and member)
        self.user.delete()

        # Verify linkevent still exists but user is NULL
        linkevent.refresh_from_db()
        self.assertIsNone(linkevent.user,
                          'User should be set to NULL after user deletion')
        self.assertTrue(Linkevent.objects.filter(id=linkevent_id).exists(),
                        'Linkevent should not be deleted')

    def test_linkevent_set_null_on_prospect_deletion(self):
        """Test that linkevent.prospect is set to NULL when prospect is deleted"""
        linkevent = Linkevent.objects.create(
            prospect=self.prospect,
            url='https://example.com/link',
            created_date_time=timezone.now()
        )
        linkevent_id = linkevent.id

        # Delete prospect
        self.prospect.delete()

        # Verify linkevent still exists but prospect is NULL
        linkevent.refresh_from_db()
        self.assertIsNone(linkevent.prospect,
                          'Prospect should be set to NULL after prospect deletion')
        self.assertTrue(Linkevent.objects.filter(id=linkevent_id).exists(),
                        'Linkevent should not be deleted')

    def test_linkevent_set_null_on_email_deletion(self):
        """Test that linkevent.email is set to NULL when email is deleted"""
        linkevent = Linkevent.objects.create(
            email=self.email,
            url='https://example.com/link',
            created_date_time=timezone.now()
        )
        linkevent_id = linkevent.id

        # Delete email
        self.email.delete()

        # Verify linkevent still exists but email is NULL
        linkevent.refresh_from_db()
        self.assertIsNone(linkevent.email,
                          'Email should be set to NULL after email deletion')
        self.assertTrue(Linkevent.objects.filter(id=linkevent_id).exists(),
                        'Linkevent should not be deleted')

    def test_linkevent_set_null_on_ad_deletion(self):
        """Test that linkevent.ad is set to NULL when ad is deleted"""
        linkevent = Linkevent.objects.create(
            ad=self.ad,
            url='https://example.com/link',
            created_date_time=timezone.now()
        )
        linkevent_id = linkevent.id

        # Delete ad
        self.ad.delete()

        # Verify linkevent still exists but ad is NULL
        linkevent.refresh_from_db()
        self.assertIsNone(linkevent.ad,
                          'Ad should be set to NULL after ad deletion')
        self.assertTrue(Linkevent.objects.filter(id=linkevent_id).exists(),
                        'Linkevent should not be deleted')
