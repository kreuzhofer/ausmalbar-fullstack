import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from coloring_pages.models.coloring_page import ColoringPage


def _make_image_file():
    buf = io.BytesIO()
    Image.new('RGB', (10, 10), 'white').save(buf, format='PNG')
    buf.seek(0)
    return SimpleUploadedFile('t.png', buf.getvalue(), content_type='image/png')


# Empty staticfiles dir means CompressedManifestStaticFilesStorage breaks on
# {% static %} tags during template rendering. Override to plain backend for
# tests that exercise real templates.
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class CanonicalUrlTests(TestCase):
    def test_home_page_has_canonical(self):
        response = self.client.get('/en/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<link rel="canonical" href="', html=False)
        # Canonical must include the full path of the current page
        self.assertContains(response, 'href="http://testserver/en/"', html=False)

    def test_search_page_canonical_excludes_query_string(self):
        response = self.client.get('/en/search/?q=dog&page=2')
        self.assertContains(response, 'href="http://testserver/en/search/"', html=False)


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class HreflangAlternatesTests(TestCase):
    def test_home_page_emits_three_hreflang_links(self):
        response = self.client.get('/en/')
        body = response.content.decode()
        self.assertIn('hreflang="en"', body)
        self.assertIn('hreflang="de"', body)
        self.assertIn('hreflang="x-default"', body)

    def test_detail_page_emits_lang_specific_urls(self):
        page = ColoringPage.objects.create(
            title_en='Test Dog', description_en='d',
            title_de='Test Hund', description_de='d',
            prompt='t', image=_make_image_file(),
            status=ColoringPage.STATUS_PUBLISHED,
        )
        response = self.client.get(f'/en/coloring-page/{page.seo_url_en}/')
        body = response.content.decode()
        self.assertIn(
            f'hreflang="en" href="http://testserver/en/coloring-page/{page.seo_url_en}/"',
            body,
        )
        self.assertIn(
            f'hreflang="de" href="http://testserver/de/ausmalbild/{page.seo_url_de}/"',
            body,
        )

    def test_detail_page_xdefault_points_to_en(self):
        page = ColoringPage.objects.create(
            title_en='Test Dog', description_en='d',
            title_de='Test Hund', description_de='d',
            prompt='t', image=_make_image_file(),
            status=ColoringPage.STATUS_PUBLISHED,
        )
        response = self.client.get(f'/en/coloring-page/{page.seo_url_en}/')
        body = response.content.decode()
        self.assertIn(
            f'hreflang="x-default" href="http://testserver/en/coloring-page/{page.seo_url_en}/"',
            body,
        )


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class MetaDescriptionTests(TestCase):
    def test_home_page_has_meta_description(self):
        response = self.client.get('/en/')
        self.assertContains(response, '<meta name="description" content="', html=False)

    def test_detail_page_uses_page_description(self):
        page = ColoringPage.objects.create(
            title_en='Cute Dog',
            description_en='A simple line-art dog for kids to color.',
            title_de='Niedlicher Hund',
            description_de='Ein Hund zum Ausmalen.',
            prompt='dog', image=_make_image_file(),
            status=ColoringPage.STATUS_PUBLISHED,
        )
        response = self.client.get(f'/en/coloring-page/{page.seo_url_en}/')
        self.assertContains(
            response,
            'content="A simple line-art dog for kids to color."',
            html=False,
        )
