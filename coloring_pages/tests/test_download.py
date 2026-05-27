import io
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from coloring_pages.models.coloring_page import ColoringPage


def _make_image_file():
    buf = io.BytesIO()
    Image.new('RGB', (10, 10), 'white').save(buf, format='PNG')
    buf.seek(0)
    return SimpleUploadedFile('t.png', buf.getvalue(), content_type='image/png')


class DownloadEndpointTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.page = ColoringPage.objects.create(
            title_en='Test', description_en='Test',
            title_de='Test', description_de='Test',
            prompt='t', image=_make_image_file(),
            status=ColoringPage.STATUS_PUBLISHED,
        )

    def test_download_emits_noindex_header(self):
        response = self.client.get(f'/en/page/{self.page.pk}/download/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['X-Robots-Tag'], 'noindex')
