from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler404, handler500
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap
from django.conf.urls.i18n import i18n_patterns

from coloring_pages.sitemaps import sitemaps

# Internationalized URL patterns
urlpatterns = i18n_patterns(
    path('', include('coloring_pages.urls')),
    prefix_default_language=True
)

# Non-internationalized URL patterns
urlpatterns += [
    path('admin/', admin.site.urls),
    # Add robots.txt handler
    path('robots.txt', TemplateView.as_view(
        template_name='robots.txt', 
        content_type='text/plain'
    )),
    # Sitemap
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    # Language switcher
    path('i18n/', include('django.conf.urls.i18n')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Error handlers
handler404 = 'coloring_pages.views.page_not_found'
handler500 = 'coloring_pages.views.server_error'

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
