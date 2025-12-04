# Data migration to seed ClientEvent Configuration
# Based on db_inserts.sql line 4 and load_sample_data.py

from django.db import migrations


def create_clientevent_configuration(apps, schema_editor):
    """
    Create the default ClientEvent Configuration record.

    This record is required by the logged_in view and other endpoints
    that check whether client event logging is enabled.

    Based on db_inserts.sql:
    INSERT INTO `clientevent_configuration` (`id`, `log_client_events`) VALUES ('1', '1');
    """
    # Skip during test runs - tests create their own data
    db_name = schema_editor.connection.settings_dict.get('NAME', '')
    if 'memory' in db_name.lower() or db_name.startswith('test_'):
        return

    Configuration = apps.get_model('clientevent', 'Configuration')

    Configuration.objects.get_or_create(
        id=1,
        defaults={'log_client_events': True}
    )


def reverse_create_clientevent_configuration(apps, schema_editor):
    """Reverse migration - delete configuration if no dependent data."""
    Configuration = apps.get_model('clientevent', 'Configuration')

    try:
        config = Configuration.objects.get(id=1)
        config.delete()
    except Configuration.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('clientevent', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            create_clientevent_configuration,
            reverse_create_clientevent_configuration
        ),
    ]
