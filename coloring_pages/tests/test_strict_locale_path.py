import io
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from coloring_pages.models.coloring_page import ColoringPage


def _make_image_file():
    buf = io.BytesIO()
    Image.new('RGB', (10, 10), 'white').save(buf, format='PNG')
    buf.seek(0)
    return SimpleUploadedFile('t.png', buf.getvalue(), content_type='image/png')


@override_settings(
    # Use plain StaticFilesStorage so tests don't need a collected manifest.
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage',
)
class StrictLocalePathTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.page = ColoringPage.objects.create(
            title_en='Cute Dog',
            description_en='A cute dog',
            title_de='Niedlicher Hund',
            description_de='Ein niedlicher Hund',
            prompt='dog',
            image=_make_image_file(),
            status=ColoringPage.STATUS_PUBLISHED,
        )

    def test_en_locale_with_en_path_serves_200(self):
        r = self.client.get(f'/en/coloring-page/{self.page.seo_url_en}/')
        self.assertEqual(r.status_code, 200)

    def test_de_locale_with_de_path_serves_200(self):
        r = self.client.get(f'/de/ausmalbild/{self.page.seo_url_de}/')
        self.assertEqual(r.status_code, 200)

    def test_en_locale_with_de_path_redirects_to_de(self):
        # /en/ausmalbild/<de-slug>/ → 301 → /de/ausmalbild/<de-slug>/
        r = self.client.get(f'/en/ausmalbild/{self.page.seo_url_de}/')
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r['Location'], f'/de/ausmalbild/{self.page.seo_url_de}/')

    def test_de_locale_with_en_path_redirects_to_en(self):
        r = self.client.get(f'/de/coloring-page/{self.page.seo_url_en}/')
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r['Location'], f'/en/coloring-page/{self.page.seo_url_en}/')
