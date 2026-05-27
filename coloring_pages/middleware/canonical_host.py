"""Redirect requests on non-canonical hosts (e.g. www variants) to the canonical host."""
from django.conf import settings
from django.http import HttpResponsePermanentRedirect


class CanonicalHostMiddleware:
    """301-redirects requests whose Host header is a non-canonical alias of a known host.

    Configured via ``settings.CANONICAL_HOSTS`` — a dict mapping any-known-alias
    (lowercased, no port) to the desired canonical hostname. Hosts not present
    in the map are passed through unchanged so local development and tests
    keep working.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.canonical_hosts = {
            alias.lower(): canonical.lower()
            for alias, canonical in getattr(settings, 'CANONICAL_HOSTS', {}).items()
        }

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()
        canonical = self.canonical_hosts.get(host)
        if canonical and canonical != host:
            scheme = 'https' if request.is_secure() else 'http'
            target = f'{scheme}://{canonical}{request.get_full_path()}'
            return HttpResponsePermanentRedirect(target)
        return self.get_response(request)
