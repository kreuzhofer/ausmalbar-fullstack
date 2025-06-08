from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler404, handler500
from django.views.generic import TemplateView
from django.conf.urls.i18n import i18n_patterns
from django.views.static import serve
import os

from coloring_pages.sitemaps import sitemaps
from coloring_pages.views import sitemap
from coloring_pages.views.robots import robots

# Sitemaps and robots.txt - outside i18n_patterns so they work with any language prefix
urlpatterns = [
    path('robots.txt', robots, name='robots'),
    path('sitemap.xml', sitemap, name='django.contrib.sitemaps.views.sitemap'),
    path('sitemap-<section>.xml', sitemap, name='django.contrib.sitemaps.views.sitemap_section'),
]

# Internationalized URL patterns
urlpatterns += i18n_patterns(
    path('', include(('coloring_pages.urls', 'coloring_pages'), namespace='coloring_pages')),
    prefix_default_language=True
)

# Non-internationalized URL patterns
urlpatterns += [
    path('admin/', admin.site.urls),
    # Add robots.txt and ads.txt handlers
    # Remove duplicate robots.txt pattern since we already have it defined above
    # path('robots.txt', serve, {
    #     'document_root': os.path.join(settings.BASE_DIR, 'static'),
    #     'path': 'robots.txt',
    # }, name='robots_txt'),
    path('ads.txt', serve, {
        'document_root': os.path.join(settings.BASE_DIR, 'static'),
        'path': 'ads.txt',
    }, name='ads_txt'),
    # Language switcher
    path('i18n/', include('django.conf.urls.i18n')),
]

# Serve media files in both development and production
from django.views.static import serve

# Serve media files
urlpatterns += [
    path(f'{settings.MEDIA_URL.strip("/")}/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Error handlers
handler404 = 'coloring_pages.views.errors.page_not_found'
handler500 = 'coloring_pages.views.errors.server_error'

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Debug toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
