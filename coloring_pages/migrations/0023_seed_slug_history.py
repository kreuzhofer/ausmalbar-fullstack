from django.db import migrations


def seed_history(apps, schema_editor):
    """Insert each page's current slug into history so we have at least one
    redirect target if titles are renamed later.

    This is idempotent: we use get_or_create on (language, slug).
    """
    ColoringPage = apps.get_model('coloring_pages', 'ColoringPage')
    SlugHistory = apps.get_model('coloring_pages', 'ColoringPageSlugHistory')
    for page in ColoringPage.objects.all().only('id', 'seo_url_en', 'seo_url_de'):
        if page.seo_url_en:
            SlugHistory.objects.get_or_create(
                language='en', slug=page.seo_url_en, defaults={'page_id': page.id},
            )
        if page.seo_url_de:
            SlugHistory.objects.get_or_create(
                language='de', slug=page.seo_url_de, defaults={'page_id': page.id},
            )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('coloring_pages', '0022_coloringpageslughistory'),
    ]

    operations = [
        migrations.RunPython(seed_history, reverse_code=noop),
    ]
