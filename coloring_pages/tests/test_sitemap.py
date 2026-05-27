import io
from xml.etree import ElementTree as ET
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from coloring_pages.models.coloring_page import ColoringPage


def _img():
    buf = io.BytesIO()
    Image.new('RGB', (10, 10), 'white').save(buf, format='PNG')
    buf.seek(0)
    return SimpleUploadedFile('t.png', buf.getvalue(), content_type='image/png')


SITEMAP_NS = {
    'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9',
    'xhtml': 'http://www.w3.org/1999/xhtml',
    'image': 'http://www.google.com/schemas/sitemap-image/1.1',
}


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class SitemapCanonicalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.page = ColoringPage.objects.create(
            title_en='Cute Dog', description_en='d',
            title_de='Niedlicher Hund', description_de='d',
            prompt='p', image=_img(),
            status=ColoringPage.STATUS_PUBLISHED,
        )

    def _locs(self, lang_header):
        response = self.client.get('/sitemap.xml', HTTP_ACCEPT_LANGUAGE=lang_header)
        self.assertEqual(response.status_code, 200)
        root = ET.fromstring(response.content)
        return [el.text for el in root.findall('sm:url/sm:loc', SITEMAP_NS)]

    def test_canonical_does_not_depend_on_request_language(self):
        en_locs = sorted(self._locs('en'))
        de_locs = sorted(self._locs('de'))
        self.assertEqual(en_locs, de_locs)

    def test_both_language_versions_listed_per_page(self):
        locs = self._locs('en')
        self.assertTrue(
            any(f'/en/coloring-page/{self.page.seo_url_en}/' in loc for loc in locs),
            f'Missing EN URL in {locs}',
        )
        self.assertTrue(
            any(f'/de/ausmalbild/{self.page.seo_url_de}/' in loc for loc in locs),
            f'Missing DE URL in {locs}',
        )


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class ImageSitemapTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.page = ColoringPage.objects.create(
            title_en='Cute Dog', description_en='Dog description',
            title_de='Niedlicher Hund', description_de='Hund Beschreibung',
            prompt='p', image=_img(),
            status=ColoringPage.STATUS_PUBLISHED,
        )

    def test_sitemap_includes_image_namespace(self):
        response = self.client.get('/sitemap.xml')
        self.assertIn(b'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"',
                      response.content)

    def test_each_page_has_image_loc_and_title(self):
        response = self.client.get('/sitemap.xml')
        root = ET.fromstring(response.content)
        image_locs = root.findall('sm:url/image:image/image:loc', SITEMAP_NS)
        self.assertTrue(len(image_locs) >= 2,
                        f'Expected 2 image entries (one per language), got {len(image_locs)}')
        image_titles = [el.text for el in root.findall('sm:url/image:image/image:title', SITEMAP_NS)]
        self.assertIn('Cute Dog', image_titles)
        self.assertIn('Niedlicher Hund', image_titles)
