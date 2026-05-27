import io
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from coloring_pages.models.coloring_page import ColoringPage
from coloring_pages.models.slug_history import ColoringPageSlugHistory


def _img():
    buf = io.BytesIO()
    Image.new('RGB', (10, 10), 'white').save(buf, format='PNG')
    buf.seek(0)
    return SimpleUploadedFile('t.png', buf.getvalue(), content_type='image/png')


class SlugHistoryCaptureTests(TestCase):
    def setUp(self):
        self.page = ColoringPage.objects.create(
            title_en='Cute Dog', description_en='d',
            title_de='Niedlicher Hund', description_de='d',
            prompt='p', image=_img(),
            status=ColoringPage.STATUS_PUBLISHED,
        )
        self.original_en_slug = self.page.seo_url_en
        self.original_de_slug = self.page.seo_url_de

    def test_no_history_on_initial_create(self):
        self.assertEqual(self.page.slug_history.count(), 0)

    def test_history_captured_when_title_changes(self):
        self.page.title_en = 'Friendly Dog'
        self.page.save()
        self.page.refresh_from_db()
        self.assertNotEqual(self.page.seo_url_en, self.original_en_slug)
        history = self.page.slug_history.filter(language='en').values_list('slug', flat=True)
        self.assertIn(self.original_en_slug, list(history))

    def test_history_captured_for_both_languages_independently(self):
        self.page.title_de = 'Freundlicher Hund'
        self.page.save()
        self.assertEqual(self.page.slug_history.filter(language='de').count(), 1)
        self.assertEqual(self.page.slug_history.filter(language='en').count(), 0)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class SlugHistoryRedirectTests(TestCase):
    def setUp(self):
        self.page = ColoringPage.objects.create(
            title_en='Cute Dog', description_en='d',
            title_de='Niedlicher Hund', description_de='d',
            prompt='p', image=_img(),
            status=ColoringPage.STATUS_PUBLISHED,
        )
        self.old_en_slug = self.page.seo_url_en
        # Rename to trigger history capture.
        self.page.title_en = 'Friendly Dog'
        self.page.save()
        self.page.refresh_from_db()

    def test_old_slug_301s_to_current(self):
        response = self.client.get(f'/en/coloring-page/{self.old_en_slug}/')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(
            response['Location'],
            f'/en/coloring-page/{self.page.seo_url_en}/',
        )

    def test_unknown_slug_still_404s(self):
        response = self.client.get('/en/coloring-page/this-never-existed/')
        self.assertEqual(response.status_code, 404)
