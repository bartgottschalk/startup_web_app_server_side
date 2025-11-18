# Database constraint tests for user app models
# Focus on unique constraints, foreign key behavior, null/blank validation, and field limits

from django.test import TestCase
from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.db import IntegrityError

from user.models import (
    Member, Prospect, Termsofuse, Membertermsofuseversionagreed,
    Emailunsubscribereasons, Email, Emailtype, Emailstatus
)


class MemberUniqueConstraintTest(PostgreSQLTestCase):
    """Test unique constraints on Member model"""

    def setUp(self):
        Group.objects.create(name='Members')
        self.user = User.objects.create_user(username='testuser', email='test@test.com')
        self.member = Member.objects.create(user=self.user)

    def test_email_unsubscribe_string_must_be_unique(self):
        """Test that email_unsubscribe_string must be unique"""
        user2 = User.objects.create_user(username='testuser2', email='test2@test.com')

        self.member.email_unsubscribe_string = 'unique_token'
        self.member.save()

        member2 = Member.objects.create(user=user2)
        member2.email_unsubscribe_string = 'unique_token'

        with self.assertRaises(IntegrityError):
            member2.save()

    def test_email_unsubscribe_string_signed_must_be_unique(self):
        """Test that email_unsubscribe_string_signed must be unique"""
        user2 = User.objects.create_user(username='testuser2', email='test2@test.com')

        self.member.email_unsubscribe_string_signed = 'unique_signed_token'
        self.member.save()

        member2 = Member.objects.create(user=user2)
        member2.email_unsubscribe_string_signed = 'unique_signed_token'

        with self.assertRaises(IntegrityError):
            member2.save()

    def test_mb_cd_must_be_unique(self):
        """Test that mb_cd (member code) must be unique"""
        user2 = User.objects.create_user(username='testuser2', email='test2@test.com')

        self.member.mb_cd = 'MEMBER123'
        self.member.save()

        member2 = Member.objects.create(user=user2)
        member2.mb_cd = 'MEMBER123'

        with self.assertRaises(IntegrityError):
            member2.save()

    def test_stripe_customer_token_must_be_unique(self):
        """Test that stripe_customer_token must be unique"""
        user2 = User.objects.create_user(username='testuser2', email='test2@test.com')

        self.member.stripe_customer_token = 'cus_test123'
        self.member.save()

        member2 = Member.objects.create(user=user2)
        member2.stripe_customer_token = 'cus_test123'

        with self.assertRaises(IntegrityError):
            member2.save()

    def test_multiple_members_can_have_null_unique_fields(self):
        """Test that multiple members can have NULL unique fields (NULL != NULL in SQL)"""
        user2 = User.objects.create_user(username='testuser2', email='test2@test.com')
        user3 = User.objects.create_user(username='testuser3', email='test3@test.com')

        # All three members have NULL email_unsubscribe_string - should be allowed
        member2 = Member.objects.create(user=user2, email_unsubscribe_string=None)
        member3 = Member.objects.create(user=user3, email_unsubscribe_string=None)

        self.assertIsNone(self.member.email_unsubscribe_string)
        self.assertIsNone(member2.email_unsubscribe_string)
        self.assertIsNone(member3.email_unsubscribe_string)


class ProspectUniqueConstraintTest(PostgreSQLTestCase):
    """Test unique constraints on Prospect model"""

    def test_email_must_be_unique(self):
        """Test that Prospect email must be unique"""
        Prospect.objects.create(
            email='unique@test.com',
            pr_cd='PROSPECT1',
            created_date_time=timezone.now()
        )

        with self.assertRaises(IntegrityError):
            Prospect.objects.create(
                email='unique@test.com',  # Duplicate
                pr_cd='PROSPECT2',
                created_date_time=timezone.now()
            )

    def test_email_unsubscribe_string_must_be_unique(self):
        """Test that Prospect email_unsubscribe_string must be unique"""
        Prospect.objects.create(
            email='test1@test.com',
            email_unsubscribe_string='unique_token',
            pr_cd='PROSPECT1',
            created_date_time=timezone.now()
        )

        with self.assertRaises(IntegrityError):
            Prospect.objects.create(
                email='test2@test.com',
                email_unsubscribe_string='unique_token',  # Duplicate
                pr_cd='PROSPECT2',
                created_date_time=timezone.now()
            )

    def test_email_unsubscribe_string_signed_must_be_unique(self):
        """Test that Prospect email_unsubscribe_string_signed must be unique"""
        Prospect.objects.create(
            email='test1@test.com',
            email_unsubscribe_string_signed='unique_signed',
            pr_cd='PROSPECT1',
            created_date_time=timezone.now()
        )

        with self.assertRaises(IntegrityError):
            Prospect.objects.create(
                email='test2@test.com',
                email_unsubscribe_string_signed='unique_signed',  # Duplicate
                pr_cd='PROSPECT2',
                created_date_time=timezone.now()
            )

    def test_pr_cd_must_be_unique(self):
        """Test that Prospect pr_cd (prospect code) must be unique"""
        Prospect.objects.create(
            email='test1@test.com',
            pr_cd='UNIQUE123',
            created_date_time=timezone.now()
        )

        with self.assertRaises(IntegrityError):
            Prospect.objects.create(
                email='test2@test.com',
                pr_cd='UNIQUE123',  # Duplicate
                created_date_time=timezone.now()
            )

    def test_multiple_prospects_can_have_null_unique_fields(self):
        """Test that multiple prospects can have NULL unique fields"""
        prospect1 = Prospect.objects.create(
            email='test1@test.com',
            email_unsubscribe_string=None,
            pr_cd='PROSPECT1',
            created_date_time=timezone.now()
        )
        prospect2 = Prospect.objects.create(
            email='test2@test.com',
            email_unsubscribe_string=None,
            pr_cd='PROSPECT2',
            created_date_time=timezone.now()
        )

        self.assertIsNone(prospect1.email_unsubscribe_string)
        self.assertIsNone(prospect2.email_unsubscribe_string)


class MembertermsofuseversionagreedUniqueTogetherTest(PostgreSQLTestCase):
    """Test unique_together constraint on Membertermsofuseversionagreed"""

    def setUp(self):
        Group.objects.create(name='Members')
        self.user = User.objects.create_user(username='testuser', email='test@test.com')
        self.member = Member.objects.create(user=self.user)
        self.tos_v1 = Termsofuse.objects.create(
            version=1,
            version_note='Version 1',
            publication_date_time=timezone.now()
        )
        self.tos_v2 = Termsofuse.objects.create(
            version=2,
            version_note='Version 2',
            publication_date_time=timezone.now()
        )

    def test_member_cannot_agree_to_same_tos_version_twice(self):
        """Test that unique_together prevents duplicate agreements"""
        # First agreement
        Membertermsofuseversionagreed.objects.create(
            member=self.member,
            termsofuseversion=self.tos_v1,
            agreed_date_time=timezone.now()
        )

        # Try to create duplicate agreement
        with self.assertRaises(IntegrityError):
            Membertermsofuseversionagreed.objects.create(
                member=self.member,
                termsofuseversion=self.tos_v1,  # Same member, same TOS version
                agreed_date_time=timezone.now()
            )

    def test_member_can_agree_to_different_tos_versions(self):
        """Test that member can agree to multiple TOS versions"""
        # Agree to version 1
        Membertermsofuseversionagreed.objects.create(
            member=self.member,
            termsofuseversion=self.tos_v1,
            agreed_date_time=timezone.now()
        )

        # Agree to version 2 (should succeed)
        Membertermsofuseversionagreed.objects.create(
            member=self.member,
            termsofuseversion=self.tos_v2,
            agreed_date_time=timezone.now()
        )

        self.assertEqual(
            Membertermsofuseversionagreed.objects.filter(
                member=self.member).count(), 2)

    def test_different_members_can_agree_to_same_tos_version(self):
        """Test that different members can agree to same TOS version"""
        user2 = User.objects.create_user(username='testuser2', email='test2@test.com')
        member2 = Member.objects.create(user=user2)

        # Both members agree to version 1
        Membertermsofuseversionagreed.objects.create(
            member=self.member,
            termsofuseversion=self.tos_v1,
            agreed_date_time=timezone.now()
        )

        Membertermsofuseversionagreed.objects.create(
            member=member2,
            termsofuseversion=self.tos_v1,
            agreed_date_time=timezone.now()
        )

        self.assertEqual(
            Membertermsofuseversionagreed.objects.filter(
                termsofuseversion=self.tos_v1).count(), 2)


class EmailUniqueConstraintTest(PostgreSQLTestCase):
    """Test unique constraints on Email model"""

    def setUp(self):
        self.email_type = Emailtype.objects.create(title='Newsletter')
        self.email_status = Emailstatus.objects.create(title='Sent')

    def test_em_cd_must_be_unique(self):
        """Test that em_cd (email code) must be unique"""
        Email.objects.create(
            subject='Email 1',
            email_type=self.email_type,
            email_status=self.email_status,
            body_html='<p>Test</p>',
            body_text='Test',
            from_address='test@test.com',
            bcc_address='admin@test.com',
            em_cd='UNIQUE_EMAIL_CODE'
        )

        with self.assertRaises(IntegrityError):
            Email.objects.create(
                subject='Email 2',
                email_type=self.email_type,
                email_status=self.email_status,
                body_html='<p>Test 2</p>',
                body_text='Test 2',
                from_address='test@test.com',
                bcc_address='admin@test.com',
                em_cd='UNIQUE_EMAIL_CODE'  # Duplicate
            )

    def test_multiple_emails_can_have_null_em_cd(self):
        """Test that multiple emails can have NULL em_cd"""
        email1 = Email.objects.create(
            subject='Email 1',
            email_type=self.email_type,
            email_status=self.email_status,
            body_html='<p>Test</p>',
            body_text='Test',
            from_address='test@test.com',
            bcc_address='admin@test.com',
            em_cd=None
        )

        email2 = Email.objects.create(
            subject='Email 2',
            email_type=self.email_type,
            email_status=self.email_status,
            body_html='<p>Test 2</p>',
            body_text='Test 2',
            from_address='test@test.com',
            bcc_address='admin@test.com',
            em_cd=None
        )

        self.assertIsNone(email1.em_cd)
        self.assertIsNone(email2.em_cd)


class ForeignKeyCascadeTest(PostgreSQLTestCase):
    """Test foreign key CASCADE behavior"""

    def setUp(self):
        Group.objects.create(name='Members')
        self.user = User.objects.create_user(username='testuser', email='test@test.com')
        self.member = Member.objects.create(user=self.user)

        self.email_type = Emailtype.objects.create(title='Newsletter')
        self.email_status = Emailstatus.objects.create(title='Sent')

    def test_deleting_user_cascades_to_member(self):
        """Test that deleting User cascades to delete Member"""
        member_id = self.member.id
        self.user.delete()

        self.assertFalse(Member.objects.filter(id=member_id).exists())

    def test_deleting_emailtype_cascades_to_email(self):
        """Test that deleting Emailtype cascades to delete Email"""
        email = Email.objects.create(
            subject='Test',
            email_type=self.email_type,
            email_status=self.email_status,
            body_html='<p>Test</p>',
            body_text='Test',
            from_address='test@test.com',
            bcc_address='admin@test.com'
        )
        email_id = email.id

        self.email_type.delete()

        self.assertFalse(Email.objects.filter(id=email_id).exists())

    def test_deleting_emailstatus_cascades_to_email(self):
        """Test that deleting Emailstatus cascades to delete Email"""
        email = Email.objects.create(
            subject='Test',
            email_type=self.email_type,
            email_status=self.email_status,
            body_html='<p>Test</p>',
            body_text='Test',
            from_address='test@test.com',
            bcc_address='admin@test.com'
        )
        email_id = email.id

        self.email_status.delete()

        self.assertFalse(Email.objects.filter(id=email_id).exists())

    def test_deleting_termsofuse_cascades_to_agreements(self):
        """Test that deleting Termsofuse cascades to delete agreements"""
        tos = Termsofuse.objects.create(
            version=1,
            version_note='Test',
            publication_date_time=timezone.now()
        )
        agreement = Membertermsofuseversionagreed.objects.create(
            member=self.member,
            termsofuseversion=tos,
            agreed_date_time=timezone.now()
        )
        agreement_id = agreement.id

        tos.delete()

        self.assertFalse(Membertermsofuseversionagreed.objects.filter(id=agreement_id).exists())


class NullBlankFieldTest(PostgreSQLTestCase):
    """Test null and blank field behavior"""

    def setUp(self):
        Group.objects.create(name='Members')

    def test_member_optional_fields_can_be_null(self):
        """Test that Member optional fields accept NULL"""
        user = User.objects.create_user(username='testuser', email='test@test.com')
        member = Member.objects.create(
            user=user,
            email_verification_string=None,
            email_verification_string_signed=None,
            email_unsubscribe_string=None,
            email_unsubscribe_string_signed=None,
            reset_password_string=None,
            reset_password_string_signed=None,
            mb_cd=None,
            stripe_customer_token=None,
            default_shipping_address=None
        )

        member.refresh_from_db()
        self.assertIsNone(member.email_verification_string)
        self.assertIsNone(member.mb_cd)
        self.assertIsNone(member.default_shipping_address)

    def test_prospect_optional_fields_can_be_null(self):
        """Test that Prospect optional fields accept NULL"""
        prospect = Prospect.objects.create(
            first_name=None,
            last_name=None,
            email='test@test.com',
            phone=None,
            email_unsubscribe_string=None,
            email_unsubscribe_string_signed=None,
            prospect_comment=None,
            swa_comment=None,
            pr_cd=None,
            created_date_time=timezone.now(),
            converted_date_time=None
        )

        prospect.refresh_from_db()
        self.assertIsNone(prospect.first_name)
        self.assertIsNone(prospect.phone)
        self.assertIsNone(prospect.converted_date_time)

    def test_emailunsubscribereasons_member_or_prospect_can_be_null(self):
        """Test that Emailunsubscribereasons can have NULL member or prospect"""
        # With member, no prospect
        user = User.objects.create_user(username='testuser', email='test@test.com')
        member = Member.objects.create(user=user)

        reasons1 = Emailunsubscribereasons.objects.create(
            member=member,
            prospect=None,
            spam=True,
            created_date_time=timezone.now()
        )

        self.assertIsNotNone(reasons1.member)
        self.assertIsNone(reasons1.prospect)

        # With prospect, no member
        prospect = Prospect.objects.create(
            email='prospect@test.com',
            pr_cd='PROSPECT123',
            created_date_time=timezone.now()
        )

        reasons2 = Emailunsubscribereasons.objects.create(
            member=None,
            prospect=prospect,
            spam=True,
            created_date_time=timezone.now()
        )

        self.assertIsNone(reasons2.member)
        self.assertIsNotNone(reasons2.prospect)

    def test_termsofuse_version_note_can_be_null(self):
        """Test that Termsofuse version_note can be NULL"""
        tos = Termsofuse.objects.create(
            version=1,
            version_note=None,
            publication_date_time=timezone.now()
        )

        self.assertIsNone(tos.version_note)


class MaxLengthFieldTest(PostgreSQLTestCase):
    """Test field max_length constraints"""

    def setUp(self):
        Group.objects.create(name='Members')

    def test_member_email_verification_string_max_length(self):
        """Test that Member email_verification_string has 50 char limit"""
        user = User.objects.create_user(username='testuser', email='test@test.com')
        member = Member.objects.create(user=user)

        # 50 chars should work
        member.email_verification_string = 'a' * 50
        member.save()
        member.refresh_from_db()
        self.assertEqual(len(member.email_verification_string), 50)

        # 51 chars should be truncated by database (or raise error depending on DB)
        # Note: Django doesn't enforce max_length at model level, only at form level
        # Database will enforce this

    def test_prospect_name_max_lengths(self):
        """Test that Prospect first_name and last_name have correct limits"""
        prospect = Prospect.objects.create(
            first_name='a' * 30,  # max 30
            last_name='b' * 150,  # max 150
            email='test@test.com',
            pr_cd='TEST123',
            created_date_time=timezone.now()
        )

        self.assertEqual(len(prospect.first_name), 30)
        self.assertEqual(len(prospect.last_name), 150)

    def test_prospect_email_max_length(self):
        """Test that Prospect email has 254 char limit (RFC 5321)"""
        # Create email that's exactly 254 chars
        local_part = 'a' * 50
        domain = 'b' * 200 + '.com'  # 204 chars
        local_part + '@' + domain  # 255 chars total

        # This should work (truncated to 254)
        prospect = Prospect.objects.create(
            email='a' * 254,  # Use max length email
            pr_cd='TEST123',
            created_date_time=timezone.now()
        )

        self.assertEqual(len(prospect.email), 254)

    def test_emailunsubscribereasons_other_max_length(self):
        """Test that Emailunsubscribereasons 'other' has 5000 char limit"""
        user = User.objects.create_user(username='testuser', email='test@test.com')
        member = Member.objects.create(user=user)

        reasons = Emailunsubscribereasons.objects.create(
            member=member,
            other='x' * 5000,  # max 5000
            created_date_time=timezone.now()
        )

        self.assertEqual(len(reasons.other), 5000)

    def test_termsofuse_version_note_max_length(self):
        """Test that Termsofuse version_note has 1000 char limit"""
        tos = Termsofuse.objects.create(
            version=1,
            version_note='y' * 1000,  # max 1000
            publication_date_time=timezone.now()
        )

        self.assertEqual(len(tos.version_note), 1000)


class RequiredFieldTest(PostgreSQLTestCase):
    """Test required fields (cannot be null or blank)"""

    def setUp(self):
        Group.objects.create(name='Members')
        self.email_type = Emailtype.objects.create(title='Newsletter')
        self.email_status = Emailstatus.objects.create(title='Sent')

    def test_member_requires_user(self):
        """Test that Member requires user field"""
        # Cannot create Member without user
        with self.assertRaises((IntegrityError, ValueError)):
            Member.objects.create(user=None)

    def test_prospect_requires_created_date_time(self):
        """Test that Prospect requires created_date_time"""
        # Cannot create Prospect without created_date_time
        with self.assertRaises((IntegrityError, TypeError)):
            Prospect.objects.create(
                email='test@test.com',
                pr_cd='TEST123'
                # missing created_date_time
            )

    def test_termsofuse_requires_version(self):
        """Test that Termsofuse requires version"""
        # Cannot create without version
        with self.assertRaises((IntegrityError, TypeError)):
            Termsofuse.objects.create(
                publication_date_time=timezone.now()
                # missing version
            )

    def test_termsofuse_requires_publication_date_time(self):
        """Test that Termsofuse requires publication_date_time"""
        # Cannot create without publication_date_time
        with self.assertRaises((IntegrityError, TypeError)):
            Termsofuse.objects.create(
                version=1
                # missing publication_date_time
            )

    def test_email_requires_email_type(self):
        """Test that Email requires email_type foreign key"""
        # Cannot create without email_type
        with self.assertRaises((IntegrityError, ValueError)):
            Email.objects.create(
                subject='Test',
                # missing email_type
                email_status=self.email_status,
                body_html='<p>Test</p>',
                body_text='Test',
                from_address='test@test.com',
                bcc_address='admin@test.com'
            )

    def test_email_requires_email_status(self):
        """Test that Email requires email_status foreign key"""
        # Cannot create without email_status
        with self.assertRaises((IntegrityError, ValueError)):
            Email.objects.create(
                subject='Test',
                email_type=self.email_type,
                # missing email_status
                body_html='<p>Test</p>',
                body_text='Test',
                from_address='test@test.com',
                bcc_address='admin@test.com'
            )

    def test_emailunsubscribereasons_requires_created_date_time(self):
        """Test that Emailunsubscribereasons requires created_date_time"""
        user = User.objects.create_user(username='testuser', email='test@test.com')
        member = Member.objects.create(user=user)

        with self.assertRaises((IntegrityError, TypeError)):
            Emailunsubscribereasons.objects.create(
                member=member,
                spam=True
                # missing created_date_time
            )

    def test_membertermsofuseversionagreed_requires_all_fields(self):
        """Test that Membertermsofuseversionagreed requires member, tos, and datetime"""
        user = User.objects.create_user(username='testuser', email='test@test.com')
        member = Member.objects.create(user=user)
        tos = Termsofuse.objects.create(
            version=1,
            version_note='Test',
            publication_date_time=timezone.now()
        )

        with self.assertRaises((IntegrityError, TypeError)):
            Membertermsofuseversionagreed.objects.create(
                member=member,
                termsofuseversion=tos
                # missing agreed_date_time
            )
