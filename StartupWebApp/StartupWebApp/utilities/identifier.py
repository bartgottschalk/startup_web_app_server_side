from StartupWebApp.utilities import random
from user.models import Prospect, Member, Ad, Email
from order.models import Order


def getNewProspectCode():
    while True:
        new_prospect_code = random.getRandomStringUpperLowerDigit(20, 20)
        if not Prospect.objects.filter(pr_cd=new_prospect_code).exists():
            break
    return new_prospect_code


def getNewMemberCode():
    while True:
        new_member_code = random.getRandomStringUpperLowerDigit(20, 20)
        if not Member.objects.filter(mb_cd=new_member_code).exists():
            break
    return new_member_code


def getNewEmailCode():
    while True:
        new_email_code = random.getRandomStringUpperLowerDigit(20, 20)
        if not Email.objects.filter(em_cd=new_email_code).exists():
            break
    return new_email_code


def getNewAdCode():
    while True:
        new_ad_code = random.getRandomStringUpperLowerDigit(20, 20)
        if not Ad.objects.filter(ad_cd=new_ad_code).exists():
            break
    return new_ad_code


def getNewProspectEmailUnsubscribeString():
    while True:
        new_prospect_email_unsubscribe_string = random.getRandomString(20, 20)
        if not Prospect.objects.filter(
                email_unsubscribe_string=new_prospect_email_unsubscribe_string).exists():
            break
    return new_prospect_email_unsubscribe_string


def getNewMemberEmailUnsubscribeString():
    while True:
        new_member_email_unsubscribe_string = random.getRandomString(20, 20)
        if not Member.objects.filter(
                email_unsubscribe_string=new_member_email_unsubscribe_string).exists():
            break
    return new_member_email_unsubscribe_string


def getNewOrderIdentifier():
    while True:
        new_identifier = random.getRandomStringUpperLowerDigit(10, 10)
        if not Order.objects.filter(identifier=new_identifier).exists():
            break
    return new_identifier
