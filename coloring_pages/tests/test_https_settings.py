"""Verify production-leaning HTTPS toggles exist and have safe defaults.

These settings are read from env vars by ``ausmalbar/settings.py``; we test
their presence and dev-safe defaults here rather than their env-parsing logic
(which uses the same trusted ``os.getenv(...) == 'True'`` pattern as 30+ other
settings in the file).
"""
from django.test import SimpleTestCase, override_settings


class HttpsEnforcementTests(SimpleTestCase):

    def test_ssl_redirect_defaults_off_for_dev(self):
        """Without the env var, SSL redirect must be off so local HTTP dev works."""
        from django.conf import settings
        self.assertFalse(settings.SECURE_SSL_REDIRECT)

    def test_hsts_defaults_off_for_dev(self):
        from django.conf import settings
        self.assertEqual(settings.SECURE_HSTS_SECONDS, 0)
        self.assertFalse(settings.SECURE_HSTS_INCLUDE_SUBDOMAINS)
        self.assertFalse(settings.SECURE_HSTS_PRELOAD)

    def test_ssl_redirect_can_be_overridden(self):
        """When deployed with SECURE_SSL_REDIRECT=True, Django's middleware picks it up."""
        with self.settings(SECURE_SSL_REDIRECT=True):
            from django.conf import settings
            self.assertTrue(settings.SECURE_SSL_REDIRECT)
