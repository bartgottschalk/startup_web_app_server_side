# Unit tests from the perspective of the programmer


from django.test import TestCase
from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.utils import timezone
from django.db.utils import IntegrityError
from django.contrib.auth.models import User
from django.core.signing import Signer

from user.models import Member, Prospect
from StartupWebApp.utilities import identifier


class MemberModelTests(PostgreSQLTestCase):

    def setUp(self):
        # Setup necessary DB Objects
        pass

    def test_cannot_save_empty_member(self):
        with self.assertRaises(IntegrityError):
            Member.objects.create(
                user=None,
                newsletter_subscriber=False,
                email_verified=False,
                email_unsubscribe_string=None,
                email_unsubscribe_string_signed=None,
                mb_cd=None)

    def test_saving_and_retreiving_member(self):

        user_new = User.objects.create_user('username', 'email_address@email.com', 'password')
        random_str = identifier.getNewMemberEmailUnsubscribeString()
        email_unsubscribe_signer = Signer(salt='email_unsubscribe')
        signed_string = email_unsubscribe_signer.sign(random_str)
        mb_cd = identifier.getNewMemberCode()
        Member.objects.create(
            user=user_new,
            newsletter_subscriber=True,
            email_verified=False,
            email_unsubscribe_string=random_str,
            email_unsubscribe_string_signed=signed_string.rsplit(
                ':',
                1)[1],
            mb_cd=mb_cd)

        user_new2 = User.objects.create_user('username2', 'email_address2@email.com', 'password2')
        random_str2 = identifier.getNewMemberEmailUnsubscribeString()
        signed_string2 = email_unsubscribe_signer.sign(random_str2)
        mb_cd2 = identifier.getNewMemberCode()
        Member.objects.create(
            user=user_new2,
            newsletter_subscriber=False,
            email_verified=False,
            email_unsubscribe_string=random_str2,
            email_unsubscribe_string_signed=signed_string2.rsplit(
                ':',
                1)[1],
            mb_cd=mb_cd2)

        saved_members = Member.objects.all()
        self.assertEqual(saved_members.count(), 2)
        self.assertEqual(
            Member.objects.get(
                email_unsubscribe_string=random_str).email_unsubscribe_string_signed,
            signed_string.rsplit(
                ':',
                1)[1])
        self.assertEqual(
            Member.objects.get(
                email_unsubscribe_string=random_str2).user.username,
            'username2')

    def test_saving_and_retreiving_prospect(self):

        random_str = identifier.getNewProspectEmailUnsubscribeString()
        email_unsubscribe_signer = Signer(salt='email_unsubscribe')
        signed_string = email_unsubscribe_signer.sign(random_str)
        pr_cd = identifier.getNewProspectCode()
        prospect1 = Prospect.objects.create(
            first_name='first',
            last_name='last',
            email='test@email.com',
            phone='1-800-800-8000 ext 800',
            email_unsubscribed=True,
            email_unsubscribe_string=random_str,
            email_unsubscribe_string_signed=signed_string.rsplit(
                ':',
                1)[1],
            prospect_comment='prospect_commented here',
            swa_comment='swa_commented here',
            pr_cd=pr_cd,
            created_date_time=timezone.now())
        prospect1.converted_date_time = timezone.now()
        prospect1.save()

        random_str2 = identifier.getNewProspectEmailUnsubscribeString()
        signed_string2 = email_unsubscribe_signer.sign(random_str2)
        pr_cd2 = identifier.getNewProspectCode()
        prospect2 = Prospect.objects.create(
            first_name='first2',
            last_name='last2',
            email='test2@email.com',
            phone='1-800-800-8000 ext 802',
            email_unsubscribed=False,
            email_unsubscribe_string=random_str2,
            email_unsubscribe_string_signed=signed_string2.rsplit(
                ':',
                1)[1],
            prospect_comment='prospect_commented here 2',
            swa_comment='swa_commented here 2',
            pr_cd=pr_cd2,
            created_date_time=timezone.now())
        prospect2.converted_date_time = timezone.now()
        prospect2.save()

        saved_prospects = Prospect.objects.all()
        self.assertEqual(saved_prospects.count(), 2)
        self.assertEqual(
            Prospect.objects.get(
                email_unsubscribe_string=random_str).email_unsubscribe_string_signed,
            signed_string.rsplit(
                ':',
                1)[1])
        self.assertEqual(
            Prospect.objects.get(
                email_unsubscribe_string=random_str2).last_name,
            'last2')

        random_str3 = identifier.getNewProspectEmailUnsubscribeString()
        signed_string3 = email_unsubscribe_signer.sign(random_str3)
        pr_cd3 = identifier.getNewProspectCode()
        try:
            Prospect.objects.create(
                first_name='first3',
                last_name='last3',
                email='test@email.com',
                phone='1-800-800-8000 ext 803',
                email_unsubscribed=False,
                email_unsubscribe_string=random_str3,
                email_unsubscribe_string_signed=signed_string3.rsplit(
                    ':',
                    1)[1],
                prospect_comment='prospect_commented here 2',
                swa_comment='swa_commented here 2',
                pr_cd=pr_cd3,
                created_date_time=timezone.now())
        except IntegrityError as e:
            print('Expected Error! Code: {c}, Message, {m}'.format(c=type(e).__name__, m=str(e)))
            self.assertEqual(type(e).__name__, 'IntegrityError')
