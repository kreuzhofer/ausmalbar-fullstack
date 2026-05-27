"""Class-based views for the coloring pages application."""
from django.http import Http404, HttpResponsePermanentRedirect
from django.urls import reverse
from django.views.generic import DetailView, TemplateView
from django.utils import timezone, translation

from ..models.coloring_page import ColoringPage
from ..models.slug_history import ColoringPageSlugHistory


class ColoringPageDetailView(DetailView):
    """Display a single published coloring page by its SEO slug.

    On slug miss, look the slug up in ``ColoringPageSlugHistory`` and 301-redirect
    to the page's current SEO URL. This survives admin title edits without
    breaking external links or Google's index.
    """
    model = ColoringPage
    template_name = 'coloring_pages/detail.html'
    context_object_name = 'page'
    slug_field = 'seo_url_en'
    slug_url_kwarg = 'seo_url'
    queryset = ColoringPage.objects.filter(status=ColoringPage.STATUS_PUBLISHED)

    def get_object(self, queryset=None):
        url_name = self.request.resolver_match.url_name
        if url_name == 'detail_de':
            self.slug_field = 'seo_url_de'
        return super().get_object(queryset=queryset)

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            slug = kwargs.get('seo_url')
            url_name = request.resolver_match.url_name
            lang = 'de' if url_name == 'detail_de' else 'en'
            history = (
                ColoringPageSlugHistory.objects
                .filter(language=lang, slug=slug, page__status=ColoringPage.STATUS_PUBLISHED)
                .select_related('page')
                .first()
            )
            if history is None:
                raise
            with translation.override(lang):
                target = history.page.get_absolute_url(language=lang)
            return HttpResponsePermanentRedirect(target)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_year'] = timezone.now().year
        return context


class ImprintView(TemplateView):
    """
    View for displaying the imprint page.
    """
    template_name = 'imprint.html'

    def get_context_data(self, **kwargs):
        from django.conf import settings
        context = super().get_context_data(**kwargs)
        context.update({
            'imprint_name': getattr(settings, 'IMPRINT_NAME', 'Your Name'),
            'imprint_street': getattr(settings, 'IMPRINT_STREET', 'Your Street'),
            'imprint_city': getattr(settings, 'IMPRINT_CITY', 'Your City'),
            'imprint_country': getattr(settings, 'IMPRINT_COUNTRY', 'Your Country'),
            'imprint_email': getattr(settings, 'IMPRINT_EMAIL', 'your@email.com'),
            'imprint_phone': getattr(settings, 'IMPRINT_PHONE', '+1234567890'),
        })
        return context
