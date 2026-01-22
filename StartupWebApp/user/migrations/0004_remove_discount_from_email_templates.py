# Generated migration to remove discount_information from email templates

from django.db import migrations


def remove_discount_from_emails(apps, schema_editor):
    """
    Remove {discount_information} placeholder and related text from email templates.
    This migration updates order confirmation email templates for both members and prospects.
    """
    Email = apps.get_model('user', 'Email')
    Orderconfiguration = apps.get_model('order', 'Orderconfiguration')

    # Get the email codes for order confirmation emails
    try:
        member_em_cd = Orderconfiguration.objects.get(key='order_confirmation_em_cd_member').string_value
        prospect_em_cd = Orderconfiguration.objects.get(key='order_confirmation_em_cd_prospect').string_value
    except Orderconfiguration.DoesNotExist:
        # If configurations don't exist, skip this migration
        print("Order confirmation email codes not found in configuration. Skipping.")
        return

    # Update member email template
    try:
        member_email = Email.objects.get(em_cd=member_em_cd)
        if '{discount_information}' in member_email.body_text:
            # Remove the discount_information line and any surrounding formatting
            body_text = member_email.body_text

            # Remove lines containing discount_information
            lines = body_text.split('\n')
            filtered_lines = []
            skip_next_blank = False

            for i, line in enumerate(lines):
                if '{discount_information}' in line:
                    skip_next_blank = True
                    continue
                if skip_next_blank and line.strip() == '':
                    skip_next_blank = False
                    continue
                filtered_lines.append(line)

            member_email.body_text = '\n'.join(filtered_lines)
            member_email.save()
            print(f"Updated member email template: {member_em_cd}")
    except Email.DoesNotExist:
        print(f"Member email template not found: {member_em_cd}")

    # Update prospect email template
    try:
        prospect_email = Email.objects.get(em_cd=prospect_em_cd)
        if '{discount_information}' in prospect_email.body_text:
            # Remove the discount_information line and any surrounding formatting
            body_text = prospect_email.body_text

            # Remove lines containing discount_information
            lines = body_text.split('\n')
            filtered_lines = []
            skip_next_blank = False

            for i, line in enumerate(lines):
                if '{discount_information}' in line:
                    skip_next_blank = True
                    continue
                if skip_next_blank and line.strip() == '':
                    skip_next_blank = False
                    continue
                filtered_lines.append(line)

            prospect_email.body_text = '\n'.join(filtered_lines)
            prospect_email.save()
            print(f"Updated prospect email template: {prospect_em_cd}")
    except Email.DoesNotExist:
        print(f"Prospect email template not found: {prospect_em_cd}")


def add_discount_back_to_emails(apps, schema_editor):
    """
    Reverse migration - this is a no-op since we don't want to restore the discount text.
    Manual intervention would be required to restore the original templates.
    """
    print("Reverse migration for discount removal is not implemented.")
    print("If you need to restore discount information, please update email templates manually.")


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_update_email_addresses'),
        ('order', '0008_remove_discount_models'),
    ]

    operations = [
        migrations.RunPython(remove_discount_from_emails, add_discount_back_to_emails),
    ]
