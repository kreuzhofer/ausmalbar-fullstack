"""
Dynamic robots.txt view for the coloring pages application.
"""
from django.http import HttpResponse
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

def robots(request):
    """
    Generate dynamic robots.txt content based on settings and sitemap configuration.
    """
    # Get the full sitemap URL
    sitemap_url = request.build_absolute_uri(reverse('django.contrib.sitemaps.views.sitemap'))
    
    # Build the robots.txt content
    content = [
        "# robots.txt for Ausmalbar",
        "User-agent: *",
        "Allow: /",
        "",
        "# Disallow admin and sensitive areas",
        "Disallow: /admin/",
        "Disallow: /media/admin/",
        "Disallow: /static/admin/",
        "Disallow: /accounts/",
        "Disallow: /api/",
        "",
        "# Sitemap location",
        f"Sitemap: {sitemap_url}"
    ]
    
    return HttpResponse("\n".join(content), content_type="text/plain")
