from django.test import TestCase, override_settings


# Empty staticfiles dir means CompressedManifestStaticFilesStorage breaks on
# {% static %} tags. Override to the plain backend for tests that render real templates.
@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class SearchNoindexTests(TestCase):
    def test_search_page_emits_noindex_meta(self):
        response = self.client.get('/en/search/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<meta name="robots" content="noindex,follow">',
            html=False,
        )

    def test_search_page_emits_xrobots_header(self):
        response = self.client.get('/en/search/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['X-Robots-Tag'], 'noindex, follow')

    def test_home_page_does_not_emit_noindex(self):
        # Sanity: noindex must only appear on search, not on real pages.
        response = self.client.get('/en/')
        self.assertNotIn('noindex', response.content.decode())
