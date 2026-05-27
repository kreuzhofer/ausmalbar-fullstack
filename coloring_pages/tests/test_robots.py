from django.test import TestCase


class RobotsTxtTests(TestCase):
    def setUp(self):
        self.response = self.client.get('/robots.txt')

    def test_returns_200(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response['Content-Type'], 'text/plain')

    def test_disallows_search(self):
        body = self.response.content.decode()
        self.assertIn('Disallow: /*/search/', body)
        self.assertIn('Disallow: /*/suche/', body)

    def test_disallows_download_endpoint(self):
        body = self.response.content.decode()
        self.assertIn('Disallow: /*/page/*/download/', body)

    def test_admin_still_blocked(self):
        body = self.response.content.decode()
        self.assertIn('Disallow: /admin/', body)

    def test_sitemap_present(self):
        body = self.response.content.decode()
        self.assertIn('Sitemap: ', body)
        self.assertIn('/sitemap.xml', body)
