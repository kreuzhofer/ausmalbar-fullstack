"""
This module contains all the views for the coloring_pages app.
"""
from django.views.generic import TemplateView
from django.utils import timezone
from django.conf import settings

# Import function-based views
from .home import home
from .search import search
from .detail import page_detail, download_image
from .sitemap import sitemap
from .robots import robots

# Import class-based views
from .views_class_based import ColoringPageDetailView, ImprintView
from .views_legal import PrivacyPolicyView, TermsOfServiceView

# Import admin views
from .admin import generate_coloring_page, confirm_coloring_page

# Import error handlers
from .errors import page_not_found, server_error

# These imports are kept for backward compatibility
__all__ = [
    'home',
    'search',
    'page_detail',
    'download_image',
    'sitemap',
    'ColoringPageDetailView',
    'ImprintView',
    'PrivacyPolicyView',
    'TermsOfServiceView',
    'generate_coloring_page',
    'confirm_coloring_page',
    'page_not_found',
    'server_error',
]
