# Data migration to seed User app data
# Based on db_inserts.sql and load_sample_data.py

from django.db import migrations
from django.utils import timezone
from datetime import datetime, UTC


def create_user_seed_data(apps, schema_editor):
    """
    Create seed data for User app:
    - Auth Group (Members)
    - Terms of Use
    - Email Types and Statuses
    - Ad Types and Statuses
    - Email Templates (for order confirmations)

    Based on db_inserts.sql lines 3, 5-9, 22-26
    """
    # Skip during test runs - tests create their own data
    db_name = schema_editor.connection.settings_dict.get('NAME', '')
    if 'memory' in db_name.lower() or db_name.startswith('test_'):
        return

    # Get models
    Group = apps.get_model('auth', 'Group')
    Termsofuse = apps.get_model('user', 'Termsofuse')
    Emailtype = apps.get_model('user', 'Emailtype')
    Emailstatus = apps.get_model('user', 'Emailstatus')
    Adtype = apps.get_model('user', 'Adtype')
    Adstatus = apps.get_model('user', 'Adstatus')
    Email = apps.get_model('user', 'Email')

    # Auth Group - Members (line 3)
    Group.objects.get_or_create(id=1, defaults={'name': 'Members'})

    # Terms of Use (line 5)
    Termsofuse.objects.get_or_create(
        id=1,
        defaults={
            'version': '1',
            'version_note': (
                'Specifically, we\'ve modified our '
                '<a class="raw-link" href="/privacy-policy">Privacy Policy</a> '
                'and <a class="raw-link" href="/terms-of-sale">Terms of Sale</a>. '
                'Modifications include...'
            ),
            'publication_date_time': datetime(2019, 4, 20, 0, 0, 0, tzinfo=UTC)
        }
    )

    # Email Types (line 6)
    Emailtype.objects.get_or_create(id=1, defaults={'title': 'Member'})
    Emailtype.objects.get_or_create(id=2, defaults={'title': 'Prospect'})

    # Email Statuses (line 7)
    Emailstatus.objects.get_or_create(id=1, defaults={'title': 'Draft'})
    Emailstatus.objects.get_or_create(id=2, defaults={'title': 'Ready'})
    Emailstatus.objects.get_or_create(id=3, defaults={'title': 'Sent'})

    # Ad Types (line 8)
    Adtype.objects.get_or_create(id=1, defaults={'title': 'Google AdWords'})
    Adtype.objects.get_or_create(id=2, defaults={'title': 'Facebook'})

    # Ad Statuses (line 9)
    Adstatus.objects.get_or_create(id=1, defaults={'title': 'Draft'})
    Adstatus.objects.get_or_create(id=2, defaults={'title': 'Ready'})
    Adstatus.objects.get_or_create(id=3, defaults={'title': 'Running'})
    Adstatus.objects.get_or_create(id=4, defaults={'title': 'Stopped'})

    # Email Templates (lines 22-26)
    # These are required for order confirmation emails
    # Note: {ENVIRONMENT_DOMAIN} and other placeholders are replaced at runtime

    # Email 1: Order confirmation for Members (Ready status)
    Email.objects.get_or_create(
        id=1,
        defaults={
            'subject': 'StartUpWebApp.com Order Confirmation',
            'body_html': 'test',
            'body_text': (
                'Hi {recipient_first_name}, {line_break}'
                'Thank you for your order! {line_break}'
                'ORDER INFORMATION {short_line_break}{order_information} {short_line_break}'
                'View your order here: {ENVIRONMENT_DOMAIN}/account/order?identifier={identifier}&em_cd={em_cd}&mb_cd={mb_cd} {line_break}'
                'PRODUCTS {short_line_break}{product_information} {line_break}'
                'SHIPPING METHOD {short_line_break}{shipping_information} {line_break}'
                'DISCOUNT CODES {short_line_break}{discount_information} {line_break}'
                'ORDER TOTAL {short_line_break}{order_total_information} {line_break}'
                'SHIPPING ADDRESS {short_line_break}{shipping_address_information} {line_break}'
                'BILLING ADDRESS {short_line_break}{billing_address_information} {line_break}'
                'PAYMENT INFORMATION {short_line_break}{payment_information} {line_break}'
                'Note: If you did NOT place an order at {ENVIRONMENT_DOMAIN}, do not click on the link. '
                'Instead, please forward this notification to contact@startupwebapp.com and let us know '
                'that you did not place this order and we\'ll dig in further to figure out what is going on. {line_break}'
                'We\'ll send you further emails with updates on your order along with shipping tracking '
                'information once it\'s available. {line_break}'
                'Thank you for being part of the StartUp Web App community! {line_break}'
                'By placing this order you agreed to the StartUpWebApp.com Terms of Sale: '
                '{ENVIRONMENT_DOMAIN}/terms-of-sale {line_break}'
                '© 2018 StartUp Web App LLC, All rights reserved.'
            ),
            'from_address': 'contact@startupwebapp.com',
            'bcc_address': 'contact@startupwebapp.com',
            'email_status_id': 2,  # Ready
            'email_type_id': 1,    # Member
            'em_cd': 'gvREoqen93ffZsmBIc8zl'
        }
    )

    # Email 2: Order confirmation for Prospects (Ready status)
    Email.objects.get_or_create(
        id=2,
        defaults={
            'subject': 'StartUpWebApp.com Order Confirmation',
            'body_html': 'test prospect',
            'body_text': (
                'Hi {recipient_first_name}, {line_break}'
                'Thank you for your order! {line_break}'
                'ORDER INFORMATION {short_line_break}{order_information} {short_line_break}'
                'View your order here: {ENVIRONMENT_DOMAIN}/account/order?identifier={identifier}&em_cd={em_cd}&pr_cd={pr_cd} {line_break}'
                'PRODUCTS {short_line_break}{product_information} {line_break}'
                'SHIPPING METHOD {short_line_break}{shipping_information} {line_break}'
                'DISCOUNT CODES {short_line_break}{discount_information} {line_break}'
                'ORDER TOTAL {short_line_break}{order_total_information} {line_break}'
                'SHIPPING ADDRESS {short_line_break}{shipping_address_information} {line_break}'
                'BILLING ADDRESS {short_line_break}{billing_address_information} {line_break}'
                'PAYMENT INFORMATION {short_line_break}{payment_information} {line_break}'
                'Note: If you did NOT place an order at {ENVIRONMENT_DOMAIN}, do not click on the link. '
                'Instead, please forward this notification to contact@startupwebapp.com and let us know '
                'that you did not place this order and we\'ll dig in further to figure out what is going on. {line_break}'
                'We\'ll send you further emails with updates on your order along with shipping tracking '
                'information once it\'s available. {line_break}'
                'Thank you for being part of the StartUp Web App community! {line_break}'
                'By placing this order you agreed to the StartUpWebApp.com Terms of Sale: '
                '{ENVIRONMENT_DOMAIN}/terms-of-sale {line_break}'
                '© 2018 StartUp Web App LLC, All rights reserved. {line_break}'
                '{prosepct_email_unsubscribe_str}'
            ),
            'from_address': 'contact@startupwebapp.com',
            'bcc_address': 'contact@startupwebapp.com',
            'email_status_id': 2,  # Ready
            'email_type_id': 2,    # Prospect
            'em_cd': 'FpGyZy6kld9R2XTjqvBQN'
        }
    )

    # Email 3: Example Prospect marketing email (Draft status)
    Email.objects.get_or_create(
        id=3,
        defaults={
            'subject': 'Example Prospect Email',
            'body_html': (
                '<!DOCTYPE html> <html lang="en"> <head> '
                '<meta http-equiv="Content-Type" content="text/html; charset=utf-8" /> '
                '<title>{msg_subject}</title> </head> <body> '
                '{draft_html} '
                '<div class="greeting">Hi {recipient_first_name},</div> '
                '<p>I\'m excited to let you know that with the latest updates to the '
                '<a href="{ENVIRONMENT_DOMAIN}?em_cd={em_cd}&pr_cd={pr_cd}" title="StartUp Web App Home Page">'
                'StartUpWebApp.com</a> website you can now <b>'
                '<a href="{ENVIRONMENT_DOMAIN}/about?em_cd={em_cd}&pr_cd={pr_cd}" title="See It">do more!</a></b></p> '
                '<p>You can <a href="{ENVIRONMENT_DOMAIN}/create-account?em_cd={em_cd}&pr_cd={pr_cd}" '
                'title="Create a StartUpWebApp Account">create a StartUpWebApp.com account</a> to make '
                '<a href="{ENVIRONMENT_DOMAIN}/products?em_cd={em_cd}&pr_cd={pr_cd}" title="Products">shopping</a> easier.</p> '
                '<p>Thank you for your continued interest in StartUpWebApp!</p> '
                '<p>The Team<br/> '
                '<a href="mailto:Team@StartUpWebApp.com?Subject=Email%20Question" title="Email Team@StartUpWebApp.com">'
                'Team@StartUpWebApp.com</a><br/> '
                '<a href="{ENVIRONMENT_DOMAIN}?em_cd={em_cd}&pr_cd={pr_cd}" title="StartUpWebApp Home Page">'
                'StartUpWebApp.com</a></p> '
                '<div class="footer"> '
                '<div class="copyright">© 2019 StartUpWebApp LLC, All rights reserved.</div> '
                '<div class="unsubscribe">You are receiving this email because you\'ve expressed interest in '
                '<a href="{ENVIRONMENT_DOMAIN}?em_cd={em_cd}&pr_cd={pr_cd}" title="StartUpWebApp Home Page">'
                'StartUpWebApp.com</a> and have been added to our mailing list. If you no longer wish to receive '
                'these email messages please follow this link to '
                '<a href="{ENVIRONMENT_DOMAIN}/account/email-unsubscribe?em_cd={em_cd}&pr_cd={pr_cd}&pr_token={pr_token}" '
                'title="Email Unsubscribe">unsubscribe</a>.</div> '
                '</div> </body> </html>'
            ),
            'body_text': (
                '{draft_text} Hi {recipient_first_name}, '
                'I\'m excited to let you know that with the latest updates to the StartUpWebApp.com website '
                'you can now do more! '
                'Go to this link to view this feature: {ENVIRONMENT_DOMAIN}/about?em_cd={em_cd}&pr_cd={pr_cd} '
                'You can create a StartUpWebApp.com account to make shopping easier. '
                'Thank you for your continued interest in StartUpWebApp! '
                'The Team Team@StartUpWebApp.com '
                '© 2019 StartUpWebApp LLC, All rights reserved. '
                'You are receiving this email because you\'ve expressed interest in StartUpWebApp.com '
                'and have been added to our mailing list. If you no longer wish to receive these email messages '
                'please follow this link to unsubscribe: '
                '{ENVIRONMENT_DOMAIN}/account/email-unsubscribe?em_cd={em_cd}&pr_cd={pr_cd}&pr_token={pr_token}'
            ),
            'from_address': 'contact@startupwebapp.com',
            'bcc_address': 'contact@startupwebapp.com',
            'email_status_id': 1,  # Draft
            'email_type_id': 2,    # Prospect
            'em_cd': 'A1jAqhMyLVpBVgxjuknq'
        }
    )

    # Email 4: Example Member marketing email (Draft status)
    Email.objects.get_or_create(
        id=4,
        defaults={
            'subject': 'Example Member Email',
            'body_html': (
                '<!DOCTYPE html> <html lang="en"> <head> '
                '<meta http-equiv="Content-Type" content="text/html; charset=utf-8" /> '
                '<title>{msg_subject}</title> </head> <body> '
                '{draft_html} '
                '<div class="greeting">Hi {recipient_first_name},</div> '
                '<p>I\'m excited to let you know that with the latest updates to the '
                '<a href="{ENVIRONMENT_DOMAIN}?em_cd={em_cd}&mb_cd={mb_cd}" title="StartUpWebApp Home Page">'
                'StartUpWebApp.com</a> website you can now <b>'
                '<a href="{ENVIRONMENT_DOMAIN}/about?em_cd={em_cd}&mb_cd={mb_cd}" title="See It">do more!</a></b></p> '
                '<p>After you sign in shopping will be easier.</p> '
                '<p>Thank you for being part of the StartUpWebApp community!</p> '
                '<p>The Team<br/> '
                '<a href="mailto:Team@StartUpWebApp.com?Subject=Email%20Question" title="Email Team@StartUpWebApp.com">'
                'Team@StartUpWebApp.com</a><br/> '
                '<a href="{ENVIRONMENT_DOMAIN}?em_cd={em_cd}&mb_cd={mb_cd}" title="StartUpWebApp Home Page">'
                'StartUpWebApp.com</a></p> '
                '<div class="footer"> '
                '<div class="copyright">© 2019 StartUpWebApp LLC, All rights reserved.</div> '
                '<div class="unsubscribe">You are receiving this email because you created a StartUpWebApp account at '
                '<a href="{ENVIRONMENT_DOMAIN}?em_cd={em_cd}&mb_cd={mb_cd}" title="StartUpWebApp Home Page">'
                '{ENVIRONMENT_DOMAIN}</a> and subscribed to newsletters. If you no longer wish to receive email '
                'newsletters please update your StartUpWebApp '
                '<a href="{ENVIRONMENT_DOMAIN}/account/edit-communication-preferences?em_cd={em_cd}&mb_cd={mb_cd}" '
                'title="Email Settings">email settings</a> or '
                '<a href="{ENVIRONMENT_DOMAIN}/account/email-unsubscribe?em_cd={em_cd}&mb_cd={mb_cd}&token={token}" '
                'title="Email Unsubscribe">unsubscribe</a>.</div> '
                '</div> </body> </html>'
            ),
            'body_text': (
                '{draft_text} Hi {recipient_first_name}, '
                'I\'m excited to let you know that with the latest updates to the StartUpWebApp.com website '
                'you can now do more! '
                'Go to this link to view this feature: {ENVIRONMENT_DOMAIN}/about?em_cd={em_cd}&mb_cd={mb_cd} '
                'After you sign in shopping will be easier. '
                'Thank you for your continued interest in StartUpWebApp! '
                'The Team Team@StartUpWebApp.com '
                '© 2019 StartUpWebApp LLC, All rights reserved. '
                'You are receiving this email because you created a StartUpWebApp account at {ENVIRONMENT_DOMAIN} '
                'and subscribed to newsletters. If you no longer wish to receive email newsletters please '
                'choose one of the following options: '
                'Update your StartUpWebApp email settings by following this link: '
                '{ENVIRONMENT_DOMAIN}/account/edit-communication-preferences?em_cd={em_cd}&mb_cd={mb_cd} '
                'Unsubscribe by following this link: '
                '{ENVIRONMENT_DOMAIN}/account/email-unsubscribe?em_cd={em_cd}&mb_cd={mb_cd}&token={token}'
            ),
            'from_address': 'contact@startupwebapp.com',
            'bcc_address': 'contact@startupwebapp.com',
            'email_status_id': 1,  # Draft
            'email_type_id': 1,    # Member
            'em_cd': 'P0Ps5FLIfUUiMpdV3HOB'
        }
    )


def reverse_create_user_seed_data(apps, schema_editor):
    """Reverse migration - delete seed data."""
    Group = apps.get_model('auth', 'Group')
    Termsofuse = apps.get_model('user', 'Termsofuse')
    Emailtype = apps.get_model('user', 'Emailtype')
    Emailstatus = apps.get_model('user', 'Emailstatus')
    Adtype = apps.get_model('user', 'Adtype')
    Adstatus = apps.get_model('user', 'Adstatus')
    Email = apps.get_model('user', 'Email')

    # Delete in reverse order of dependencies
    Email.objects.filter(id__in=[1, 2, 3, 4]).delete()
    Adstatus.objects.filter(id__in=[1, 2, 3, 4]).delete()
    Adtype.objects.filter(id__in=[1, 2]).delete()
    Emailstatus.objects.filter(id__in=[1, 2, 3]).delete()
    Emailtype.objects.filter(id__in=[1, 2]).delete()
    Termsofuse.objects.filter(id=1).delete()
    Group.objects.filter(id=1).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),  # Django auth dependency
    ]

    operations = [
        migrations.RunPython(
            create_user_seed_data,
            reverse_create_user_seed_data
        ),
    ]
