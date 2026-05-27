"""Enforce that the URL locale prefix matches the URL's expected language.

`coloring-page/<slug>/` (URL name ``detail_en``) is only valid under ``/en/``;
`ausmalbild/<slug>/` (URL name ``detail_de``) is only valid under ``/de/``.
Cross-locale combinations are 301-redirected to the correct combination so
Google sees a single canonical URL per page rather than four duplicates.
"""
from django.http import HttpResponsePermanentRedirect
from django.urls import resolve, reverse
from django.urls.exceptions import Resolver404
from django.utils import translation


URL_NAME_TO_REQUIRED_LANG = {
    'detail_en': 'en',
    'detail_de': 'de',
}


class StrictLocalePathMiddleware:
    """Run AFTER LocaleMiddleware so request.LANGUAGE_CODE is populated."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            match = resolve(request.path_info)
        except Resolver404:
            return self.get_response(request)

        required_lang = URL_NAME_TO_REQUIRED_LANG.get(match.url_name)
        current_lang = getattr(request, 'LANGUAGE_CODE', None)
        if required_lang and current_lang and required_lang != current_lang:
            with translation.override(required_lang):
                target = reverse(
                    f'coloring_pages:{match.url_name}',
                    kwargs=match.kwargs,
                )
            qs = request.META.get('QUERY_STRING', '')
            if qs:
                target = f'{target}?{qs}'
            return HttpResponsePermanentRedirect(target)
        return self.get_response(request)
