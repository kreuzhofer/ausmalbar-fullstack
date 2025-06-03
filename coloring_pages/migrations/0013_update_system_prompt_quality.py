from django.db import migrations


def update_system_prompt_quality(apps, schema_editor):
    """Set quality to 'hd' for all existing system prompts."""
    SystemPrompt = apps.get_model('coloring_pages', 'SystemPrompt')
    SystemPrompt.objects.all().update(quality='hd')


class Migration(migrations.Migration):

    dependencies = [
        ('coloring_pages', '0012_systemprompt_quality'),
    ]

    operations = [
        migrations.RunPython(
            update_system_prompt_quality,
            # No reverse code needed as this is a data migration
            reverse_code=migrations.RunPython.noop,
        ),
    ]
