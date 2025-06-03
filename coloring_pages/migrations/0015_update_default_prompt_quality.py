from django.db import migrations


def update_default_prompt_quality(apps, schema_editor):
    """Set quality to 'medium' for the default system prompt."""
    SystemPrompt = apps.get_model('coloring_pages', 'SystemPrompt')
    # Update the default prompt (assuming it has a specific name or other identifying characteristic)
    SystemPrompt.objects.filter(name='Default').update(quality='medium')


def reverse_update(apps, schema_editor):
    """No need to reverse this data migration."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('coloring_pages', '0014_alter_systemprompt_quality'),
    ]

    operations = [
        migrations.RunPython(
            update_default_prompt_quality,
            reverse_code=reverse_update,
        ),
    ]
