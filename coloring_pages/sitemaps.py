from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import ColoringPage

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return ['home', 'search']

    def location(self, item):
        return reverse(item)


class ColoringPageSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.9

    def items(self):
        return ColoringPage.objects.all()

    def lastmod(self, obj):
        return obj.updated_at


# Combine all sitemaps
sitemaps = {
    'static': StaticViewSitemap,
    'coloring_pages': ColoringPageSitemap,
}
