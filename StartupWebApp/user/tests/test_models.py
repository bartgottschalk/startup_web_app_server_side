# Unit tests from the perspective of the programmer

import json

from django.test import TestCase
from django.db.utils import IntegrityError
from django.contrib.auth.models import User, Group
from django.core.signing import TimestampSigner, Signer, SignatureExpired, BadSignature

from user.models import Member
from StartupWebApp.utilities import identifier

class MemberModelTests(TestCase):

	def setUp(self):
		# Setup necessary DB Objects
		pass

	def test_cannot_save_empty_member(self):
		with self.assertRaises(IntegrityError):
			Member.objects.create(user=None, newsletter_subscriber=False, email_verified=False, email_unsubscribe_string=None, email_unsubscribe_string_signed=None, mb_cd=None)

	def test_saving_and_retreiving_member(self):

		user_new = User.objects.create_user('username', 'email_address@email.com', 'password')
		random_str = identifier.getNewMemberEmailUnsubscribeString()
		email_unsubscribe_signer = Signer(salt='email_unsubscribe')
		signed_string = email_unsubscribe_signer.sign(random_str)
		mb_cd = identifier.getNewMemberCode()
		member = Member.objects.create(user=user_new, newsletter_subscriber=True, email_verified=False, email_unsubscribe_string=random_str, email_unsubscribe_string_signed=signed_string.rsplit(':', 1)[1], mb_cd=mb_cd)

		user_new2 = User.objects.create_user('username2', 'email_address2@email.com', 'password2')
		random_str2 = identifier.getNewMemberEmailUnsubscribeString()
		signed_string2 = email_unsubscribe_signer.sign(random_str2)
		mb_cd2 = identifier.getNewMemberCode()
		member2 = Member.objects.create(user=user_new2, newsletter_subscriber=False, email_verified=False, email_unsubscribe_string=random_str2, email_unsubscribe_string_signed=signed_string2.rsplit(':', 1)[1], mb_cd=mb_cd2)

		saved_members = Member.objects.all()
		self.assertEqual(saved_members.count(), 2)
		self.assertEqual(Member.objects.get(email_unsubscribe_string=random_str).email_unsubscribe_string_signed, signed_string.rsplit(':', 1)[1])
		self.assertEqual(Member.objects.get(email_unsubscribe_string=random_str2).user.username, 'username2')


