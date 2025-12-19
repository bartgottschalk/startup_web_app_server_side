from django.contrib import admin

# Register your models here.

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.core.signing import Signer
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from smtplib import SMTPDataError
import logging

from user.models import (
    Defaultshippingaddress, Member, Prospect, Emailunsubscribereasons,
    EmailunsubscribereasonsAdmin, Termsofuse, Membertermsofuseversionagreed,
    Emailtype, Emailstatus, Email, Emailsent, Ad, Adtype, Adstatus, Chatmessage
)
from StartupWebApp.utilities import identifier

from import_export import resources
from import_export.admin import ImportExportModelAdmin

logger = logging.getLogger(__name__)

email_unsubscribe_signer = Signer(salt='email_unsubscribe')

# Define an inline admin descriptor for Member model
# which acts a bit like a singleton


class MemberInline(admin.StackedInline):
    model = Member
    can_delete = False
    verbose_name_plural = 'member'

# Define a new User admin


class UserAdmin(BaseUserAdmin):
    inlines = (MemberInline, )


class ProspectResource(resources.ModelResource):
    class Meta:
        model = Prospect

# Define a new Prospect admin


class ProspectAdmin(ImportExportModelAdmin):
    resource_class = ProspectResource
    actions = ['populate_prospect_codes']
    list_display = (
        'first_name',
        'last_name',
        'email',
        'phone',
        'pr_cd',
        'email_unsubscribed',
        'prospect_comment',
        'swa_comment',
        'created_date_time',
        'converted_date_time')

    def populate_prospect_codes(self, request, queryset):
        prospect_counter = 0
        for prospect in queryset:
            logger.debug(f"Processing prospect: {prospect}")

            # pr_cd
            if prospect.pr_cd is None:
                logger.info(f"pr_cd empty for prospect {prospect.email}, setting new code")
                new_pr_cd = identifier.getNewProspectCode()
                prospect.pr_cd = new_pr_cd
            else:
                logger.debug(f"pr_cd already set for prospect {prospect.email}, skipping")

            # email_unsubscribe_string
            if prospect.email_unsubscribe_string is None:
                logger.info(
                    f"email_unsubscribe_string empty for prospect {
                        prospect.email}, setting new string")
                new_email_unsubscribe_string = identifier.getNewProspectEmailUnsubscribeString()
                prospect.email_unsubscribe_string = new_email_unsubscribe_string
                signed_string = email_unsubscribe_signer.sign(new_email_unsubscribe_string)
                prospect.email_unsubscribe_string_signed = signed_string.rsplit(':', 1)[1]
            else:
                logger.debug(
                    f"email_unsubscribe_string already set for prospect {
                        prospect.email}, skipping")

            prospect.save()
            prospect_counter += 1
        if prospect_counter == 1:
            message_bit = "1 prospect."
        else:
            message_bit = "%s prospects." % prospect_counter
        self.message_user(request, "Codes were successfully generated for %s" % message_bit)
        logger.info(f"Populated codes for {prospect_counter} prospect(s)")
    populate_prospect_codes.short_description = "Populate Prospect Codes"

# Define a new Defaultshippingaddress admin


class DefaultshippingaddressAdmin(admin.ModelAdmin):
    list_display = ('name', 'address_line1', 'city', 'state', 'zip', 'country_code')

# Define a new Email admin


class EmailAdmin(admin.ModelAdmin):
    actions = ['populate_email_codes', 'send_draft_email', 'send_ready_email']
    list_display = ('subject', 'email_type', 'email_status', 'em_cd')

    def populate_email_codes(self, request, queryset):
        email_counter = 0
        for email in queryset:
            logger.debug(f"Processing email: {email}")

            # em_cd
            if email.em_cd is None:
                logger.info(f"em_cd empty for email '{email.subject}', setting new code")
                new_em_cd = identifier.getNewAdCode()
                email.em_cd = new_em_cd
            else:
                logger.debug(f"em_cd already set for email '{email.subject}', skipping")

            email.save()
            email_counter += 1
        if email_counter == 1:
            message_bit = "1 email."
        else:
            message_bit = "%s emails." % email_counter
        self.message_user(request, "Codes were successfully generated for %s" % message_bit)
        logger.info(f"Populated codes for {email_counter} email(s)")
    populate_email_codes.short_description = "Populate Email Codes"

    def send_draft_email(self, request, queryset):
        email_counter = 0
        for email in queryset:
            logger.debug(f"Processing email: {email}")

            logger.debug(f"email.email_status is {email.email_status}")
            if email.email_status == Emailstatus.objects.get(title='Draft'):
                logger.info(f"Email '{email.subject}' is Draft, proceeding with send")
                if email.email_type == Emailtype.objects.get(title='Prospect'):
                    recipients = Prospect.objects.filter(email_unsubscribed=False)
                    recipient_list = '<br/><br/>Notes:<br/>Prospects who would receive this email:<br/>'
                elif email.email_type == Emailtype.objects.get(title='Member'):
                    recipients = User.objects.filter(
                        member__email_unsubscribed=False,
                        member__newsletter_subscriber=True)
                    recipient_list = '<br/><br/>Notes:<br/>Members who would receive this email:<br/>'
                for recipient in recipients:
                    recipient_list += str(recipient.first_name) + ' ' + \
                        str(recipient.last_name) + ' ' + recipient.email + '<br/>'

                for recipient in recipients:
                    if email.email_type == Emailtype.objects.get(title='Prospect'):
                        draft_email_namespace = {
                            'draft_text': '*** DRAFT ***',
                            'draft_html': '*** DRAFT ***<br/><br/>',
                            'msg_subject': email.subject,
                            'ENVIRONMENT_DOMAIN': settings.ENVIRONMENT_DOMAIN,
                            'recipient_first_name': recipient.first_name,
                            'em_cd': email.em_cd,
                            'mb_cd': None,
                            'pr_cd': recipient.pr_cd,
                            'token': None,
                            'pr_token': recipient.email_unsubscribe_string_signed}
                    elif email.email_type == Emailtype.objects.get(title='Member'):
                        draft_email_namespace = {
                            'draft_text': '*** DRAFT ***',
                            'draft_html': '*** DRAFT ***<br/><br/>',
                            'msg_subject': email.subject,
                            'ENVIRONMENT_DOMAIN': settings.ENVIRONMENT_DOMAIN,
                            'recipient_first_name': recipient.first_name,
                            'em_cd': email.em_cd,
                            'mb_cd': recipient.member.mb_cd,
                            'pr_cd': None,
                            'token': recipient.member.email_unsubscribe_string_signed,
                            'pr_token': None}
                    formatted_body_text = (
                        email.body_text +
                        recipient_list).format(
                        **draft_email_namespace)
                    formatted_body_html = (
                        email.body_html +
                        recipient_list).format(
                        **draft_email_namespace)
                    msg = EmailMultiAlternatives(
                        subject=email.subject,
                        body=formatted_body_text,
                        from_email=email.from_address,
                        to=['bart+startupwebapp@mosaicmeshai.com'],
                        bcc=[email.bcc_address],
                        reply_to=[email.from_address],
                    )
                    msg.attach_alternative(formatted_body_html, "text/html")
                    try:
                        msg.send(fail_silently=False)
                    except SMTPDataError:
                        logger.exception(
                            f"SMTPDataError while sending draft email '{
                                email.subject}'")
            else:
                logger.warning(f"Email '{email.subject}' is NOT Draft, skipping")
            email_counter += 1
        if email_counter == 1:
            message_bit = "1 email."
        else:
            message_bit = "%s emails." % email_counter
        self.message_user(request, "Draft emails were successfully sent for %s" % message_bit)
    send_draft_email.short_description = "Send Draft Email"

    def send_ready_email(self, request, queryset):
        email_counter = 0
        for email in queryset:
            logger.debug(f"Processing email: {email}")
            logger.debug(f"email.email_status is {email.email_status}")
            if email.email_status == Emailstatus.objects.get(title='Ready'):
                logger.info(f"Email '{email.subject}' is Ready, proceeding with send to recipients")
                if email.email_type == Emailtype.objects.get(title='Prospect'):
                    recipients = Prospect.objects.filter(email_unsubscribed=False)
                elif email.email_type == Emailtype.objects.get(title='Member'):
                    recipients = User.objects.filter(
                        member__email_unsubscribed=False,
                        member__newsletter_subscriber=True)
                for recipient in recipients:

                    if email.email_type == Emailtype.objects.get(title='Prospect'):
                        ready_email_namespace = {
                            'draft_text': '',
                            'draft_html': '',
                            'msg_subject': email.subject,
                            'ENVIRONMENT_DOMAIN': settings.ENVIRONMENT_DOMAIN,
                            'recipient_first_name': recipient.first_name,
                            'em_cd': email.em_cd,
                            'mb_cd': None,
                            'pr_cd': recipient.pr_cd,
                            'token': None,
                            'pr_token': recipient.email_unsubscribe_string_signed}
                    elif email.email_type == Emailtype.objects.get(title='Member'):
                        ready_email_namespace = {
                            'draft_text': '',
                            'draft_html': '',
                            'msg_subject': email.subject,
                            'ENVIRONMENT_DOMAIN': settings.ENVIRONMENT_DOMAIN,
                            'recipient_first_name': recipient.first_name,
                            'em_cd': email.em_cd,
                            'mb_cd': recipient.member.mb_cd,
                            'pr_cd': None,
                            'token': recipient.member.email_unsubscribe_string_signed,
                            'pr_token': None}
                    formatted_body_text = email.body_text.format(**ready_email_namespace)
                    formatted_body_html = email.body_html.format(**ready_email_namespace)
                    msg = EmailMultiAlternatives(
                        subject=email.subject,
                        body=formatted_body_text,
                        from_email=email.from_address,
                        to=[recipient.email],
                        bcc=[email.bcc_address],
                        reply_to=[email.from_address],
                    )
                    msg.attach_alternative(formatted_body_html, "text/html")
                    try:
                        msg.send(fail_silently=False)
                        now = timezone.now()
                        if email.email_type == Emailtype.objects.get(title='Prospect'):
                            emailsent = Emailsent.objects.create(
                                member=None, prospect=recipient, email=email, sent_date_time=now)
                        elif email.email_type == Emailtype.objects.get(title='Member'):
                            emailsent = Emailsent.objects.create(
                                member=recipient.member, prospect=None, email=email, sent_date_time=now)
                        logger.info(f"Email sent successfully: {emailsent}")
                    except SMTPDataError:
                        logger.exception(
                            f"SMTPDataError while sending email '{
                                email.subject}' to recipient {
                                recipient.email}")
                email.email_status = Emailstatus.objects.get(title='Sent')
                email.save()
            else:
                logger.warning(f"Email '{email.subject}' is NOT Ready, skipping")
            email_counter += 1
        if email_counter == 1:
            message_bit = "1 email."
        else:
            message_bit = "%s emails." % email_counter
        self.message_user(request, "Draft emails were successfully sent for %s" % message_bit)
    send_ready_email.short_description = "Send Ready Email to Recipients"

# Define a new Emailsent admin


class EmailsentAdmin(admin.ModelAdmin):
    list_display = ('member', 'prospect', 'email', 'sent_date_time')

# Define a new Ad admin


class AdAdmin(admin.ModelAdmin):
    actions = ['populate_ad_codes']
    list_display = (
        'campaignid',
        'adgroupid',
        'adid',
        'final_url',
        'headline_1',
        'headline_2',
        'headline_3',
        'description_1',
        'description_2',
        'final_url_suffix',
        'ad_type',
        'ad_status',
        'ad_cd')

    def populate_ad_codes(self, request, queryset):
        ad_counter = 0
        for ad in queryset:
            logger.debug(f"Processing ad: {ad}")

            # ad_cd
            if ad.ad_cd is None:
                logger.info(f"ad_cd empty for ad {ad.adid}, setting new code")
                new_ad_cd = identifier.getNewAdCode()
                ad.ad_cd = new_ad_cd
            else:
                logger.debug(f"ad_cd already set for ad {ad.adid}, skipping")

            ad.save()
            ad_counter += 1
        if ad_counter == 1:
            message_bit = "1 ad."
        else:
            message_bit = "%s ads." % ad_counter
        self.message_user(request, "Codes were successfully generated for %s" % message_bit)
        logger.info(f"Populated codes for {ad_counter} ad(s)")
    populate_ad_codes.short_description = "Populate Ad Codes"

# Define a new Chatmessage admin


class ChatmessageAdmin(admin.ModelAdmin):
    list_display = ('email_address', 'member', 'prospect', 'name', 'message', 'created_date_time')


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(Prospect, ProspectAdmin)
admin.site.register(Defaultshippingaddress, DefaultshippingaddressAdmin)

admin.site.register(Emailunsubscribereasons, EmailunsubscribereasonsAdmin)

admin.site.register(Termsofuse)
admin.site.register(Membertermsofuseversionagreed)

admin.site.register(Email, EmailAdmin)
admin.site.register(Emailsent, EmailsentAdmin)
admin.site.register(Emailtype)
admin.site.register(Emailstatus)

admin.site.register(Ad, AdAdmin)
admin.site.register(Adtype)
admin.site.register(Adstatus)

admin.site.register(Chatmessage, ChatmessageAdmin)
