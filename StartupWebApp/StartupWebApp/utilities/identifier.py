from django.core.exceptions import ObjectDoesNotExist
from StartupWebApp.utilities import random
from user.models import Prospect, Member, Ad, Email
from order.models import Order


def getNewProspectCode():
    new_prospect_code = None
    code_available = False
    while (code_available == False):
        new_prospect_code = random.getRandomStringUpperLowerDigit(20, 20)
        try:
            prospect = Prospect.objects.get(pr_cd=new_prospect_code)
        except (ObjectDoesNotExist, ValueError):
            code_available = True
    return new_prospect_code


def getNewMemberCode():
    new_member_code = None
    code_available = False
    while (code_available == False):
        new_member_code = random.getRandomStringUpperLowerDigit(20, 20)
        try:
            member = Member.objects.get(mb_cd=new_member_code)
        except (ObjectDoesNotExist, ValueError):
            code_available = True
    return new_member_code


def getNewEmailCode():
    new_email_code = None
    code_available = False
    while (code_available == False):
        new_email_code = random.getRandomStringUpperLowerDigit(20, 20)
        try:
            email = Email.objects.get(em_cd=new_email_code)
        except (ObjectDoesNotExist, ValueError):
            code_available = True
    return new_email_code


def getNewAdCode():
    new_ad_code = None
    code_available = False
    while (code_available == False):
        new_ad_code = random.getRandomStringUpperLowerDigit(20, 20)
        try:
            ad = Ad.objects.get(ad_cd=new_ad_code)
        except (ObjectDoesNotExist, ValueError):
            code_available = True
    return new_ad_code


def getNewProspectEmailUnsubscribeString():
    new_prospect_email_unsubscribe_string = None
    string_available = False
    while (string_available == False):
        new_prospect_email_unsubscribe_string = random.getRandomString(20, 20)
        try:
            prospect = Prospect.objects.get(email_unsubscribe_string=new_prospect_email_unsubscribe_string)
        except (ObjectDoesNotExist, ValueError):
            string_available = True
    return new_prospect_email_unsubscribe_string


def getNewMemberEmailUnsubscribeString():
    new_member_email_unsubscribe_string = None
    string_available = False
    while (string_available == False):
        new_member_email_unsubscribe_string = random.getRandomString(20, 20)
        try:
            member = Member.objects.get(email_unsubscribe_string=new_member_email_unsubscribe_string)
        except (ObjectDoesNotExist, ValueError):
            string_available = True
    return new_member_email_unsubscribe_string


def getNewOrderIdentifier():
    new_identifier = None
    identifier_available = False
    while (identifier_available == False):
        new_identifier = random.getRandomStringUpperLowerDigit(10, 10)
        try:
            order = Order.objects.get(identifier=new_identifier)
        except (ObjectDoesNotExist, ValueError):
            identifier_available = True
    return new_identifier
