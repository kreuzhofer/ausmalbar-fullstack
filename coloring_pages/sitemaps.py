from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import translation
from django.conf import settings
from .models import ColoringPage


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        # List of all static pages to include in sitemap
        return [
            'coloring_pages:home',
            'coloring_pages:search',
            'coloring_pages:imprint',
            'coloring_pages:privacy_policy',
            'coloring_pages:datenschutz',
            'coloring_pages:terms_of_service',
            'coloring_pages:nutzungsbedingungen',
        ]

    def location(self, item):
        # Use the default language for static pages
        with translation.override(settings.LANGUAGE_CODE):
            return reverse(item, current_app='coloring_pages')


class ColoringPageSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.9

    def items(self):
        # Get all coloring pages that have at least one SEO URL
        return ColoringPage.objects.exclude(seo_url_en__isnull=True, seo_url_de__isnull=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        # Get the current language
        current_lang = translation.get_language()
        
        # For the location, use the English URL as default
        if obj.seo_url_en:
            return reverse('coloring_pages:detail_en', 
                         kwargs={'seo_url': obj.seo_url_en}, 
                         current_app='coloring_pages')
        # Fallback to German if English is not available
        elif obj.seo_url_de:
            return reverse('coloring_pages:detail_de', 
                         kwargs={'seo_url': obj.seo_url_de}, 
                         current_app='coloring_pages')
        # Fallback to ID-based URL if no SEO URLs are available
        return reverse('coloring_pages:page_detail', 
                     kwargs={'pk': obj.pk}, 
                     current_app='coloring_pages')

    def get_urls(self, page=1, site=None, protocol=None):
        # Override to include hreflang links for each URL
        urls = []
        for item in self.paginator.page(page).object_list:
            loc = self._location(item)
            url_info = {
                'item': item,
                'location': loc,
                'lastmod': item.updated_at,
                'changefreq': self._get('changefreq', item),
                'priority': self._get('priority', item, 0.5),
                'alternates': []
            }
            
            # Add alternate language URLs
            if item.seo_url_en:  # English version
                en_url = reverse('coloring_pages:detail_en', 
                               kwargs={'seo_url': item.seo_url_en}, 
                               current_app='coloring_pages')
                url_info['alternates'].append({
                    'lang': 'en',
                    'url': en_url
                })
                
            if item.seo_url_de:  # German version
                de_url = reverse('coloring_pages:detail_de', 
                               kwargs={'seo_url': item.seo_url_de}, 
                               current_app='coloring_pages')
                url_info['alternates'].append({
                    'lang': 'de',
                    'url': de_url
                })
            
            urls.append(url_info)
        
        return urls


# Combine all sitemaps
sitemaps = {
    'static': StaticViewSitemap,
    'coloring_pages': ColoringPageSitemap,
}
