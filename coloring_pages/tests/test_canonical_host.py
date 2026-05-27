from django.http import HttpResponse
from django.test import TestCase, override_settings
from django.urls import re_path


def simple_view(request, *args, **kwargs):
    return HttpResponse('ok')


# Minimal URLconf used so pass-through requests resolve without needing
# templates or static-file manifests.
urlpatterns = [re_path(r'^.*$', simple_view)]


@override_settings(
    ALLOWED_HOSTS=['ausmalbar.de', 'www.ausmalbar.de', 'testserver'],
    MIDDLEWARE=[
        'coloring_pages.middleware.canonical_host.CanonicalHostMiddleware',
        'django.middleware.locale.LocaleMiddleware',
        'django.middleware.common.CommonMiddleware',
    ],
    CANONICAL_HOSTS={'ausmalbar.de': 'ausmalbar.de', 'www.ausmalbar.de': 'ausmalbar.de'},
    ROOT_URLCONF=__name__,
)
class CanonicalHostMiddlewareTests(TestCase):
    def test_www_apex_redirects_to_apex(self):
        response = self.client.get('/de/', HTTP_HOST='www.ausmalbar.de')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], 'http://ausmalbar.de/de/')

    def test_apex_is_passed_through(self):
        response = self.client.get('/de/', HTTP_HOST='ausmalbar.de', follow=False)
        self.assertEqual(response.status_code, 200)

    def test_unknown_host_passes_through(self):
        # Hosts not in CANONICAL_HOSTS are left alone (e.g. localhost during dev)
        response = self.client.get('/de/', HTTP_HOST='testserver', follow=False)
        self.assertEqual(response.status_code, 200)

    def test_query_string_preserved(self):
        response = self.client.get('/de/suche/?q=hund', HTTP_HOST='www.ausmalbar.de')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], 'http://ausmalbar.de/de/suche/?q=hund')

    def test_https_redirect_preserves_scheme(self):
        response = self.client.get(
            '/de/',
            HTTP_HOST='www.ausmalbar.de',
            secure=True,
        )
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], 'https://ausmalbar.de/de/')
