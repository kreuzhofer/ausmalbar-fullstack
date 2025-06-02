import base64
import io
import os
import uuid
from django.conf import settings
import requests
from io import BytesIO
from django.views.generic import TemplateView, DetailView
from django.views.generic.base import ContextMixin, TemplateResponseMixin, View
from django.contrib import messages
from django.utils.translation import get_language
from django.db.models import Q
from django.db.models.fields.files import ImageFieldFile
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse, HttpResponseServerError
from django.shortcuts import get_object_or_404, redirect, render
from django.template import loader
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from PIL import Image
from django.utils import timezone

from .models import ColoringPage, SearchQuery, create_unique_slug
from .utils import get_coloring_page_prompt


# Moved to utils.py

def home(request):
    latest_pages = ColoringPage.objects.all()[:3]
    return render(request, 'coloring_pages/home.html', {'latest_pages': latest_pages})

def search(request):
    """
    Search for coloring pages with tracking of search queries.
    """
    query = request.GET.get('q', '').strip()
    
    # Search in both English and German fields
    if query:
        pages = ColoringPage.objects.filter(
            Q(title_en__icontains=query) |
            Q(description_en__icontains=query) |
            Q(title_de__icontains=query) |
            Q(description_de__icontains=query) |
            Q(prompt__icontains=query)
        ).distinct()
        
        # Track search query if not a duplicate
        if not SearchQuery.is_duplicate_search(request, query):
            SearchQuery.create_from_request(request, query, pages.count())
    else:
        pages = ColoringPage.objects.all()
    
    # Order by most recent first
    pages = pages.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(pages, 8)  # 8 items per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get popular searches for the sidebar (only show on empty search)
    popular_searches = []
    if not query:
        current_language = get_language() or 'en'
        popular_searches = SearchQuery.get_popular_searches(
            days=30, 
            limit=5,
            language=current_language  # Only show popular searches in the current language
        )
    
    context = {
        'query': query,
        'page_obj': page_obj,
        'popular_searches': popular_searches,
        'is_search': bool(query),
    }
    
    # Store current search in session for back navigation
    if query:
        if not request.session.session_key:
            request.session.create()
            
        request.session['last_search'] = {
            'query': query,
            'result_count': pages.count(),
            'timestamp': timezone.now().isoformat(),
            'language': get_language() or 'en'  # Store the language with the search
        }
    
    return render(request, 'coloring_pages/search.html', context)

def page_detail(request, pk):
    """
    Legacy view that redirects to the new SEO-friendly URL format.
    """
    page = get_object_or_404(ColoringPage, pk=pk)
    return redirect(page.get_absolute_url(), permanent=True)

def download_image(request, pk):
    coloring_page = get_object_or_404(ColoringPage, pk=pk)
    if not coloring_page.image:
        raise Http404("Image not found")
    
    # Get the appropriate title based on the current language
    language = request.LANGUAGE_CODE or 'en'
    title = getattr(coloring_page, f'title_{language[:2]}', 'coloring_page')
    
    # Clean up the filename to be URL-safe
    import re
    filename = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
    
    response = HttpResponse(coloring_page.image.read(), content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="{filename}.png"'
    return response


def page_not_found(request, exception=None, template_name='404.html'):
    """Custom 404 error handler."""
    return render(request, '404.html', status=404)


def server_error(request, template_name='500.html'):
    """Custom 500 error handler."""
    return render(request, template_name, status=500)


def sitemap(request, *args, **kwargs):
    """Custom sitemap view that passes the request to sitemaps"""
    # Get the sitemaps dict
    from .sitemaps import sitemaps
    
    # Create a copy of the sitemaps dict to avoid modifying the original
    sitemaps_instances = {}
    
    # Initialize sitemap instances and pass the request
    for name, sitemap_class in sitemaps.items():
        if isinstance(sitemap_class, type):  # It's a class, instantiate it
            sitemap_instance = sitemap_class()
            sitemap_instance._request = request
            sitemaps_instances[name] = sitemap_instance
        else:  # It's already an instance
            sitemap_class._request = request
            sitemaps_instances[name] = sitemap_class
    
    # Import here to avoid circular imports
    from django.contrib.sitemaps.views import sitemap as django_sitemap_view
    
    # Call the original sitemap view with our updated sitemaps
    return django_sitemap_view(
        request,
        sitemaps=sitemaps_instances,
        template_name='sitemap.xml',
        content_type='application/xml',
        *args, **kwargs
    )


class ColoringPageDetailView(DetailView):
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
    template_name = 'imprint.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add imprint information from environment variables
        context.update({
            'imprint_name': settings.IMPRINT_NAME,
            'imprint_street': settings.IMPRINT_STREET,
            'imprint_city': settings.IMPRINT_CITY,
            'imprint_country': settings.IMPRINT_COUNTRY,
            'imprint_email': settings.IMPRINT_EMAIL,
            'imprint_phone': settings.IMPRINT_PHONE,
        })
        return context
# Admin views have been moved to coloring_pages/views/admin/coloring_pages.py
