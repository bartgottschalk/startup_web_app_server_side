# Extended model tests for user app models
# Focus on model instance creation, __str__ methods, field behavior, and relationships


from django.test import TestCase
from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.db import IntegrityError

from user.models import (
    Member, Prospect, Termsofuse, Membertermsofuseversionagreed,
    Emailunsubscribereasons, Chatmessage, Defaultshippingaddress,
    Email, Emailtype, Emailstatus, Emailsent
)


class MemberModelTest(PostgreSQLTestCase):
    """Test Member model creation, fields, and relationships"""

    def setUp(self):
        Group.objects.create(name='Members')

    def test_member_creation_with_user(self):
        """Test that Member can be created with User relationship"""
        user = User.objects.create_user(username='testuser', email='test@test.com')
        member = Member.objects.create(user=user)

        self.assertEqual(member.user.username, 'testuser')
        self.assertEqual(member.user.email, 'test@test.com')
        self.assertIsNotNone(member.id)

    def test_member_default_values(self):
        """Test that Member model applies correct default values"""
        user = User.objects.create_user(username='testuser', email='test@test.com')
        member = Member.objects.create(user=user)

        self.assertFalse(member.newsletter_subscriber,
                         'newsletter_subscriber should default to False')
        self.assertFalse(member.email_verified, 'email_verified should default to False')
        self.assertFalse(member.email_unsubscribed, 'email_unsubscribed should default to False')
        self.assertFalse(member.use_default_shipping_and_payment_info,
                         'use_default_shipping_and_payment_info should default to False')

    def test_member_str_representation(self):
        """Test that Member __str__ returns expected format"""
        user = User.objects.create_user(username='testuser', email='test@test.com')
        member = Member.objects.create(user=user)

        expected = "testuser, Email: test@test.com"
        self.assertEqual(str(member), expected)

    def test_member_one_to_one_relationship_with_user(self):
        """Test that Member has OneToOne relationship with User (can't create duplicate)"""
        user = User.objects.create_user(username='testuser', email='test@test.com')
        Member.objects.create(user=user)

        # Try to create another Member with same User
        with self.assertRaises(IntegrityError):
            Member.objects.create(user=user)

    def test_member_cascade_delete_with_user(self):
        """Test that Member is deleted when User is deleted (CASCADE)"""
        user = User.objects.create_user(username='testuser', email='test@test.com')
        member = Member.objects.create(user=user)
        member_id = member.id

        # Delete user
        user.delete()

        # Verify member was also deleted
        self.assertFalse(Member.objects.filter(id=member_id).exists())

    def test_member_with_default_shipping_address(self):
        """Test that Member can have optional default shipping address"""
        user = User.objects.create_user(username='testuser', email='test@test.com')
        address = Defaultshippingaddress.objects.create(
            name='John Doe',
            address_line1='123 Main St',
            city='San Francisco',
            state='CA',
            zip='94102',
            country='United States',
            country_code='US'
        )
        member = Member.objects.create(user=user, default_shipping_address=address)

        self.assertEqual(member.default_shipping_address.city, 'San Francisco')
        self.assertEqual(member.default_shipping_address.state, 'CA')

    def test_member_token_fields_can_be_set(self):
        """Test that Member token fields can be set and retrieved"""
        user = User.objects.create_user(username='testuser', email='test@test.com')
        member = Member.objects.create(
            user=user,
            email_verification_string='test_verification',
            email_verification_string_signed='test_signed_verification',
            email_unsubscribe_string='test_unsubscribe',
            email_unsubscribe_string_signed='test_signed_unsubscribe',
            reset_password_string='test_reset',
            reset_password_string_signed='test_signed_reset',
            mb_cd='TEST123',
            stripe_customer_token='cus_test123'
        )

        self.assertEqual(member.email_verification_string, 'test_verification')
        self.assertEqual(member.email_unsubscribe_string, 'test_unsubscribe')
        self.assertEqual(member.reset_password_string, 'test_reset')
        self.assertEqual(member.mb_cd, 'TEST123')
        self.assertEqual(member.stripe_customer_token, 'cus_test123')


class ProspectModelTest(PostgreSQLTestCase):
    """Test Prospect model creation, fields, and uniqueness"""

    def test_prospect_creation(self):
        """Test that Prospect can be created with required fields"""
        prospect = Prospect.objects.create(
            first_name='Jane',
            last_name='Smith',
            email='jane@test.com',
            pr_cd='PROSPECT123',
            created_date_time=timezone.now()
        )

        self.assertEqual(prospect.first_name, 'Jane')
        self.assertEqual(prospect.last_name, 'Smith')
        self.assertEqual(prospect.email, 'jane@test.com')
        self.assertIsNotNone(prospect.id)

    def test_prospect_default_values(self):
        """Test that Prospect model applies correct default values"""
        prospect = Prospect.objects.create(
            email='test@test.com',
            pr_cd='TEST123',
            created_date_time=timezone.now()
        )

        self.assertFalse(prospect.email_unsubscribed, 'email_unsubscribed should default to False')

    def test_prospect_str_representation(self):
        """Test that Prospect __str__ returns expected format"""
        prospect = Prospect.objects.create(
            first_name='Jane',
            last_name='Smith',
            email='jane@test.com',
            pr_cd='PROSPECT123',
            created_date_time=timezone.now()
        )

        expected = "Jane Smith, Email: jane@test.com"
        self.assertEqual(str(prospect), expected)

    def test_prospect_str_with_none_values(self):
        """Test that Prospect __str__ handles None values gracefully"""
        prospect = Prospect.objects.create(
            email='test@test.com',
            pr_cd='TEST123',
            created_date_time=timezone.now()
        )

        # Should handle None first_name and last_name
        result = str(prospect)
        self.assertIn('test@test.com', result)

    def test_prospect_with_all_fields(self):
        """Test that Prospect can be created with all optional fields"""
        prospect = Prospect.objects.create(
            first_name='Jane',
            last_name='Smith',
            email='jane@test.com',
            phone='555-1234',
            email_unsubscribed=True,
            email_unsubscribe_string='unsubscribe_token',
            email_unsubscribe_string_signed='signed_token',
            prospect_comment='5 on a scale of 1-5 for how excited they are',
            swa_comment='Captured from lead form',
            pr_cd='PROSPECT123',
            created_date_time=timezone.now()
        )

        self.assertEqual(prospect.phone, '555-1234')
        self.assertTrue(prospect.email_unsubscribed)
        self.assertEqual(prospect.prospect_comment, '5 on a scale of 1-5 for how excited they are')
        self.assertEqual(prospect.swa_comment, 'Captured from lead form')

    def test_prospect_converted_date_time_nullable(self):
        """Test that Prospect converted_date_time can be null"""
        prospect = Prospect.objects.create(
            email='test@test.com',
            pr_cd='TEST123',
            created_date_time=timezone.now()
        )

        self.assertIsNone(prospect.converted_date_time)

        # Set converted_date_time
        prospect.converted_date_time = timezone.now()
        prospect.save()
        prospect.refresh_from_db()

        self.assertIsNotNone(prospect.converted_date_time)


class TermsofuseModelTest(PostgreSQLTestCase):
    """Test Termsofuse model creation and versioning"""

    def test_termsofuse_creation(self):
        """Test that Termsofuse can be created"""
        tos = Termsofuse.objects.create(
            version=1,
            version_note='Initial terms',
            publication_date_time=timezone.now()
        )

        self.assertEqual(tos.version, 1)
        self.assertEqual(tos.version_note, 'Initial terms')
        self.assertIsNotNone(tos.id)

    def test_termsofuse_str_representation(self):
        """Test that Termsofuse __str__ returns expected format"""
        tos = Termsofuse.objects.create(
            version=2,
            version_note='Updated privacy policy',
            publication_date_time=timezone.now()
        )

        expected = "2:Updated privacy policy"
        self.assertEqual(str(tos), expected)

    def test_termsofuse_custom_table_name(self):
        """Test that Termsofuse uses custom table name"""
        tos = Termsofuse.objects.create(
            version=1,
            version_note='Test',
            publication_date_time=timezone.now()
        )

        self.assertEqual(tos._meta.db_table, 'user_terms_of_use_version')

    def test_termsofuse_multiple_versions(self):
        """Test that multiple TOS versions can exist"""
        tos1 = Termsofuse.objects.create(
            version=1,
            version_note='Version 1',
            publication_date_time=timezone.now()
        )
        tos2 = Termsofuse.objects.create(
            version=2,
            version_note='Version 2',
            publication_date_time=timezone.now()
        )

        self.assertEqual(Termsofuse.objects.count(), 2)
        self.assertNotEqual(tos1.id, tos2.id)


class MembertermsofuseversionagreedModelTest(PostgreSQLTestCase):
    """Test Membertermsofuseversionagreed model and unique constraint"""

    def setUp(self):
        Group.objects.create(name='Members')
        self.user = User.objects.create_user(username='testuser', email='test@test.com')
        self.member = Member.objects.create(user=self.user)
        self.tos = Termsofuse.objects.create(
            version=1,
            version_note='Test TOS',
            publication_date_time=timezone.now()
        )

    def test_membertermsofuseversionagreed_creation(self):
        """Test that Membertermsofuseversionagreed can be created"""
        agreement = Membertermsofuseversionagreed.objects.create(
            member=self.member,
            termsofuseversion=self.tos,
            agreed_date_time=timezone.now()
        )

        self.assertEqual(agreement.member, self.member)
        self.assertEqual(agreement.termsofuseversion, self.tos)
        self.assertIsNotNone(agreement.id)

    def test_membertermsofuseversionagreed_str_representation(self):
        """Test that Membertermsofuseversionagreed __str__ returns expected format"""
        agreement = Membertermsofuseversionagreed.objects.create(
            member=self.member,
            termsofuseversion=self.tos,
            agreed_date_time=timezone.now()
        )

        expected = "testuser:1"
        self.assertEqual(str(agreement), expected)

    def test_membertermsofuseversionagreed_custom_table_name(self):
        """Test that Membertermsofuseversionagreed uses custom table name"""
        agreement = Membertermsofuseversionagreed.objects.create(
            member=self.member,
            termsofuseversion=self.tos,
            agreed_date_time=timezone.now()
        )

        self.assertEqual(agreement._meta.db_table, 'user_member_terms_of_use_version_agreed')

    def test_membertermsofuseversionagreed_cascade_delete_member(self):
        """Test that agreement is deleted when member is deleted"""
        agreement = Membertermsofuseversionagreed.objects.create(
            member=self.member,
            termsofuseversion=self.tos,
            agreed_date_time=timezone.now()
        )
        agreement_id = agreement.id

        # Delete member (and user)
        self.user.delete()

        # Verify agreement was deleted
        self.assertFalse(Membertermsofuseversionagreed.objects.filter(id=agreement_id).exists())

    def test_membertermsofuseversionagreed_cascade_delete_tos(self):
        """Test that agreement is deleted when TOS version is deleted"""
        agreement = Membertermsofuseversionagreed.objects.create(
            member=self.member,
            termsofuseversion=self.tos,
            agreed_date_time=timezone.now()
        )
        agreement_id = agreement.id

        # Delete TOS version
        self.tos.delete()

        # Verify agreement was deleted
        self.assertFalse(Membertermsofuseversionagreed.objects.filter(id=agreement_id).exists())


class EmailunsubscribereasonsModelTest(PostgreSQLTestCase):
    """Test Emailunsubscribereasons model creation and relationships"""

    def setUp(self):
        Group.objects.create(name='Members')
        self.user = User.objects.create_user(username='testuser', email='test@test.com')
        self.member = Member.objects.create(user=self.user)
        self.prospect = Prospect.objects.create(
            email='prospect@test.com',
            pr_cd='PROSPECT123',
            created_date_time=timezone.now()
        )

    def test_emailunsubscribereasons_creation_with_member(self):
        """Test that Emailunsubscribereasons can be created with member"""
        reasons = Emailunsubscribereasons.objects.create(
            member=self.member,
            no_longer_want_to_receive=True,
            created_date_time=timezone.now()
        )

        self.assertEqual(reasons.member, self.member)
        self.assertIsNone(reasons.prospect)
        self.assertTrue(reasons.no_longer_want_to_receive)

    def test_emailunsubscribereasons_creation_with_prospect(self):
        """Test that Emailunsubscribereasons can be created with prospect"""
        reasons = Emailunsubscribereasons.objects.create(
            prospect=self.prospect,
            spam=True,
            created_date_time=timezone.now()
        )

        self.assertIsNone(reasons.member)
        self.assertEqual(reasons.prospect, self.prospect)
        self.assertTrue(reasons.spam)

    def test_emailunsubscribereasons_default_values(self):
        """Test that Emailunsubscribereasons boolean fields default to False"""
        reasons = Emailunsubscribereasons.objects.create(
            member=self.member,
            created_date_time=timezone.now()
        )

        self.assertFalse(reasons.no_longer_want_to_receive)
        self.assertFalse(reasons.never_signed_up)
        self.assertFalse(reasons.inappropriate)
        self.assertFalse(reasons.spam)

    def test_emailunsubscribereasons_str_representation_member(self):
        """Test that Emailunsubscribereasons __str__ works with member"""
        reasons = Emailunsubscribereasons.objects.create(
            member=self.member,
            spam=True,
            created_date_time=timezone.now()
        )

        result = str(reasons)
        self.assertIn('testuser', result)
        self.assertIn('True', result)  # spam=True

    def test_emailunsubscribereasons_str_representation_prospect(self):
        """Test that Emailunsubscribereasons __str__ works with prospect"""
        reasons = Emailunsubscribereasons.objects.create(
            prospect=self.prospect,
            spam=True,
            created_date_time=timezone.now()
        )

        result = str(reasons)
        self.assertIn('prospect@test.com', result)

    def test_emailunsubscribereasons_with_other_text(self):
        """Test that Emailunsubscribereasons can store 'other' text reason"""
        reasons = Emailunsubscribereasons.objects.create(
            member=self.member,
            other='Too many emails',
            created_date_time=timezone.now()
        )

        self.assertEqual(reasons.other, 'Too many emails')

    def test_emailunsubscribereasons_cascade_delete_member(self):
        """Test that reasons are deleted when member is deleted"""
        reasons = Emailunsubscribereasons.objects.create(
            member=self.member,
            created_date_time=timezone.now()
        )
        reasons_id = reasons.id

        # Delete member
        self.user.delete()

        # Verify reasons were deleted
        self.assertFalse(Emailunsubscribereasons.objects.filter(id=reasons_id).exists())

    def test_emailunsubscribereasons_cascade_delete_prospect(self):
        """Test that reasons are deleted when prospect is deleted"""
        reasons = Emailunsubscribereasons.objects.create(
            prospect=self.prospect,
            created_date_time=timezone.now()
        )
        reasons_id = reasons.id

        # Delete prospect
        self.prospect.delete()

        # Verify reasons were deleted
        self.assertFalse(Emailunsubscribereasons.objects.filter(id=reasons_id).exists())


class ChatmessageModelTest(PostgreSQLTestCase):
    """Test Chatmessage model creation and relationships"""

    def setUp(self):
        Group.objects.create(name='Members')
        self.user = User.objects.create_user(username='testuser', email='test@test.com')
        self.member = Member.objects.create(user=self.user)
        self.prospect = Prospect.objects.create(
            email='prospect@test.com',
            pr_cd='PROSPECT123',
            created_date_time=timezone.now()
        )

    def test_chatmessage_creation_with_member(self):
        """Test that Chatmessage can be created with member"""
        message = Chatmessage.objects.create(
            member=self.member,
            name='Test User',
            email_address='test@test.com',
            message='Test message',
            created_date_time=timezone.now()
        )

        self.assertEqual(message.member, self.member)
        self.assertIsNone(message.prospect)
        self.assertEqual(message.message, 'Test message')

    def test_chatmessage_creation_with_prospect(self):
        """Test that Chatmessage can be created with prospect"""
        message = Chatmessage.objects.create(
            prospect=self.prospect,
            name='Prospect User',
            email_address='prospect@test.com',
            message='Prospect message',
            created_date_time=timezone.now()
        )

        self.assertIsNone(message.member)
        self.assertEqual(message.prospect, self.prospect)
        self.assertEqual(message.message, 'Prospect message')

    def test_chatmessage_str_representation_member(self):
        """Test that Chatmessage __str__ works with member"""
        message = Chatmessage.objects.create(
            member=self.member,
            name='Test User',
            email_address='test@test.com',
            message='Test message',
            created_date_time=timezone.now()
        )

        result = str(message)
        self.assertIn('testuser', result)
        self.assertIn('test@test.com', result)
        self.assertIn('Test message', result)

    def test_chatmessage_str_representation_prospect(self):
        """Test that Chatmessage __str__ works with prospect"""
        message = Chatmessage.objects.create(
            prospect=self.prospect,
            name='Prospect User',
            email_address='prospect@test.com',
            message='Prospect message',
            created_date_time=timezone.now()
        )

        result = str(message)
        self.assertIn('prospect@test.com', result)

    def test_chatmessage_custom_table_name(self):
        """Test that Chatmessage uses custom table name"""
        message = Chatmessage.objects.create(
            member=self.member,
            name='Test',
            email_address='test@test.com',
            message='Test',
            created_date_time=timezone.now()
        )

        self.assertEqual(message._meta.db_table, 'user_chat_message')

    def test_chatmessage_cascade_delete_member(self):
        """Test that chat message is deleted when member is deleted"""
        message = Chatmessage.objects.create(
            member=self.member,
            name='Test',
            email_address='test@test.com',
            message='Test',
            created_date_time=timezone.now()
        )
        message_id = message.id

        # Delete member
        self.user.delete()

        # Verify message was deleted
        self.assertFalse(Chatmessage.objects.filter(id=message_id).exists())

    def test_chatmessage_cascade_delete_prospect(self):
        """Test that chat message is deleted when prospect is deleted"""
        message = Chatmessage.objects.create(
            prospect=self.prospect,
            name='Test',
            email_address='prospect@test.com',
            message='Test',
            created_date_time=timezone.now()
        )
        message_id = message.id

        # Delete prospect
        self.prospect.delete()

        # Verify message was deleted
        self.assertFalse(Chatmessage.objects.filter(id=message_id).exists())


class DefaultshippingaddressModelTest(PostgreSQLTestCase):
    """Test Defaultshippingaddress model"""

    def test_defaultshippingaddress_creation(self):
        """Test that Defaultshippingaddress can be created"""
        address = Defaultshippingaddress.objects.create(
            name='John Doe',
            address_line1='123 Main St',
            city='San Francisco',
            state='CA',
            zip='94102',
            country='United States',
            country_code='US'
        )

        self.assertEqual(address.name, 'John Doe')
        self.assertEqual(address.city, 'San Francisco')
        self.assertEqual(address.state, 'CA')
        self.assertEqual(address.country_code, 'US')

    def test_defaultshippingaddress_str_representation(self):
        """Test that Defaultshippingaddress __str__ returns formatted address"""
        address = Defaultshippingaddress.objects.create(
            name='John Doe',
            address_line1='123 Main St',
            city='San Francisco',
            state='CA',
            zip='94102',
            country='United States',
            country_code='US'
        )

        result = str(address)
        self.assertIn('John Doe', result)
        self.assertIn('123 Main St', result)
        self.assertIn('San Francisco', result)
        self.assertIn('CA', result)
        self.assertIn('94102', result)
        self.assertIn('US', result)

    def test_defaultshippingaddress_all_fields_optional(self):
        """Test that all Defaultshippingaddress fields are optional"""
        address = Defaultshippingaddress.objects.create()

        self.assertIsNone(address.name)
        self.assertIsNone(address.address_line1)
        self.assertIsNone(address.city)
        self.assertIsNone(address.state)
        self.assertIsNone(address.zip)
        self.assertIsNone(address.country)
        self.assertIsNone(address.country_code)


class EmailModelsTest(PostgreSQLTestCase):
    """Test Email-related models (Emailtype, Emailstatus, Email, Emailsent)"""

    def setUp(self):
        self.email_type = Emailtype.objects.create(title='Newsletter')
        self.email_status = Emailstatus.objects.create(title='Sent')

        Group.objects.create(name='Members')
        self.user = User.objects.create_user(username='testuser', email='test@test.com')
        self.member = Member.objects.create(user=self.user)
        self.prospect = Prospect.objects.create(
            email='prospect@test.com',
            pr_cd='PROSPECT123',
            created_date_time=timezone.now()
        )

    def test_emailtype_creation(self):
        """Test that Emailtype can be created"""
        email_type = Emailtype.objects.create(title='Welcome')

        self.assertEqual(email_type.title, 'Welcome')

    def test_emailtype_str_representation(self):
        """Test that Emailtype __str__ returns title"""
        self.assertEqual(str(self.email_type), 'Newsletter')

    def test_emailtype_custom_table_name(self):
        """Test that Emailtype uses custom table name"""
        self.assertEqual(self.email_type._meta.db_table, 'user_email_type')

    def test_emailstatus_creation(self):
        """Test that Emailstatus can be created"""
        email_status = Emailstatus.objects.create(title='Draft')

        self.assertEqual(email_status.title, 'Draft')

    def test_emailstatus_str_representation(self):
        """Test that Emailstatus __str__ returns title"""
        self.assertEqual(str(self.email_status), 'Sent')

    def test_emailstatus_custom_table_name(self):
        """Test that Emailstatus uses custom table name"""
        self.assertEqual(self.email_status._meta.db_table, 'user_email_status')

    def test_email_creation(self):
        """Test that Email can be created"""
        email = Email.objects.create(
            subject='Test Email',
            email_type=self.email_type,
            email_status=self.email_status,
            body_html='<p>Test HTML</p>',
            body_text='Test text',
            from_address='noreply@test.com',
            bcc_address='admin@test.com',
            em_cd='EMAIL123'
        )

        self.assertEqual(email.subject, 'Test Email')
        self.assertEqual(email.email_type, self.email_type)
        self.assertEqual(email.em_cd, 'EMAIL123')

    def test_email_str_representation(self):
        """Test that Email __str__ returns expected format"""
        email = Email.objects.create(
            subject='Welcome Email',
            email_type=self.email_type,
            email_status=self.email_status,
            body_html='<p>Welcome</p>',
            body_text='Welcome',
            from_address='noreply@test.com',
            bcc_address='admin@test.com'
        )

        result = str(email)
        self.assertIn('Welcome Email', result)
        self.assertIn('Newsletter', result)
        self.assertIn('Sent', result)

    def test_email_custom_table_name(self):
        """Test that Email uses custom table name"""
        email = Email.objects.create(
            subject='Test',
            email_type=self.email_type,
            email_status=self.email_status,
            body_html='<p>Test</p>',
            body_text='Test',
            from_address='test@test.com',
            bcc_address='admin@test.com'
        )

        self.assertEqual(email._meta.db_table, 'user_email')

    def test_emailsent_creation_with_member(self):
        """Test that Emailsent can be created with member"""
        email = Email.objects.create(
            subject='Test',
            email_type=self.email_type,
            email_status=self.email_status,
            body_html='<p>Test</p>',
            body_text='Test',
            from_address='test@test.com',
            bcc_address='admin@test.com'
        )

        email_sent = Emailsent.objects.create(
            member=self.member,
            email=email,
            sent_date_time=timezone.now()
        )

        self.assertEqual(email_sent.member, self.member)
        self.assertIsNone(email_sent.prospect)
        self.assertEqual(email_sent.email, email)

    def test_emailsent_creation_with_prospect(self):
        """Test that Emailsent can be created with prospect"""
        email = Email.objects.create(
            subject='Test',
            email_type=self.email_type,
            email_status=self.email_status,
            body_html='<p>Test</p>',
            body_text='Test',
            from_address='test@test.com',
            bcc_address='admin@test.com'
        )

        email_sent = Emailsent.objects.create(
            prospect=self.prospect,
            email=email,
            sent_date_time=timezone.now()
        )

        self.assertIsNone(email_sent.member)
        self.assertEqual(email_sent.prospect, self.prospect)

    def test_emailsent_str_representation_member(self):
        """Test that Emailsent __str__ works with member"""
        email = Email.objects.create(
            subject='Test Email',
            email_type=self.email_type,
            email_status=self.email_status,
            body_html='<p>Test</p>',
            body_text='Test',
            from_address='test@test.com',
            bcc_address='admin@test.com'
        )

        email_sent = Emailsent.objects.create(
            member=self.member,
            email=email,
            sent_date_time=timezone.now()
        )

        result = str(email_sent)
        self.assertIn('testuser', result)
        self.assertIn('Test Email', result)

    def test_emailsent_str_representation_prospect(self):
        """Test that Emailsent __str__ works with prospect"""
        email = Email.objects.create(
            subject='Test Email',
            email_type=self.email_type,
            email_status=self.email_status,
            body_html='<p>Test</p>',
            body_text='Test',
            from_address='test@test.com',
            bcc_address='admin@test.com'
        )

        email_sent = Emailsent.objects.create(
            prospect=self.prospect,
            email=email,
            sent_date_time=timezone.now()
        )

        result = str(email_sent)
        self.assertIn('prospect@test.com', result)

    def test_emailsent_custom_table_name(self):
        """Test that Emailsent uses custom table name"""
        email = Email.objects.create(
            subject='Test',
            email_type=self.email_type,
            email_status=self.email_status,
            body_html='<p>Test</p>',
            body_text='Test',
            from_address='test@test.com',
            bcc_address='admin@test.com'
        )

        email_sent = Emailsent.objects.create(
            member=self.member,
            email=email,
            sent_date_time=timezone.now()
        )

        self.assertEqual(email_sent._meta.db_table, 'user_email_sent')

    def test_emailsent_cascade_delete_email(self):
        """Test that Emailsent is deleted when Email is deleted"""
        email = Email.objects.create(
            subject='Test',
            email_type=self.email_type,
            email_status=self.email_status,
            body_html='<p>Test</p>',
            body_text='Test',
            from_address='test@test.com',
            bcc_address='admin@test.com'
        )

        email_sent = Emailsent.objects.create(
            member=self.member,
            email=email,
            sent_date_time=timezone.now()
        )
        email_sent_id = email_sent.id

        # Delete email
        email.delete()

        # Verify email_sent was deleted
        self.assertFalse(Emailsent.objects.filter(id=email_sent_id).exists())
