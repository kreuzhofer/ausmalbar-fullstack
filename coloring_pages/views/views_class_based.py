"""
Class-based views for the coloring pages application.
"""
from django.views.generic import DetailView, TemplateView
from django.utils import timezone
from ..models.coloring_page import ColoringPage


class ColoringPageDetailView(DetailView):
    """
    View for displaying a single coloring page with SEO-friendly URLs.
    """
    model = ColoringPage
    template_name = 'coloring_pages/detail.html'
    context_object_name = 'page'
    slug_field = 'seo_url_en'  # Default field to look up by
    slug_url_kwarg = 'seo_url'  # Name of the URL parameter
    
    def get_object(self, queryset=None):
        """
        Get the object by checking both English and German SEO URLs.
        """
        # Determine which language URL was used
        url_name = self.request.resolver_match.url_name
        
        if url_name == 'detail_de':
            # For German URLs, look up by seo_url_de
            self.slug_field = 'seo_url_de'
        
        # Get the object using the parent class's logic
        obj = super().get_object(queryset=queryset)
        
        # If the object was found by ID (fallback), redirect to the SEO URL
        if not obj:
            raise Http404("No coloring page found matching the query")
            
        return obj
    
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
        context = super().get_context_data(**kwargs)
        context.update({
            'imprint_name': getattr(self.request, 'site', None) and self.request.site.settings.IMPRINT_NAME or 'Your Name',
            'imprint_street': getattr(self.request, 'site', None) and self.request.site.settings.IMPRINT_STREET or 'Your Street',
            'imprint_city': getattr(self.request, 'site', None) and self.request.site.settings.IMPRINT_CITY or 'Your City',
            'imprint_country': getattr(self.request, 'site', None) and self.request.site.settings.IMPRINT_COUNTRY or 'Your Country',
            'imprint_email': getattr(self.request, 'site', None) and self.request.site.settings.IMPRINT_EMAIL or 'your@email.com',
            'imprint_phone': getattr(self.request, 'site', None) and self.request.site.settings.IMPRINT_PHONE or '+1234567890',
        })
        return context
