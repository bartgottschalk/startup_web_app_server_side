from django.core.signing import Signer
from api_refrigeratorgames.utilities import random
from user.models import Member

email_unsubscribe_signer = Signer(salt='email_unsubscribe')

members = Member.objects.all()
for member in members:
	if member.email_unsubscribe_string is None:
		print('member email_unsubscribe_string is None')
		random_str = random.getRandomString(20, 20)
		member.email_unsubscribe_string = random_str
		signed_string = email_unsubscribe_signer.sign(random_str)
		member.email_unsubscribe_string_signed = signed_string.rsplit(':', 1)[1]
		member.save()
	else:
		print('member email_unsubscribe_string is NOT NONE: ' + str(member.email_unsubscribe_string))
