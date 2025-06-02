from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.conf import settings
from django.utils import translation
from django.contrib.sites.shortcuts import get_current_site
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
            
    def get_urls(self, page=1, site=None, protocol=None):
        # Override to include proper domain from the request
        urls = []
        protocol = protocol or 'http'
        domain = None
        
        # Try to get the current site domain
        try:
            if site is None:
                site = get_current_site(None)
            domain = site.domain
        except:
            domain = 'localhost:8000'  # Fallback if site framework not properly set up
            
        for item in self.items():
            path = self.location(item)
            
            # Build the full URL
            if not path.startswith(('http://', 'https://')):
                loc = f"{protocol}://{domain.rstrip('/')}{path}"
            else:
                loc = path
                
            url_info = {
                'location': loc,
                'changefreq': self._get('changefreq', None, 'weekly'),
                'priority': self._get('priority', None, 0.8),
                'lastmod': None,
                'alternates': []
            }
            urls.append(url_info)
            
        return urls


class ColoringPageSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.9

    def items(self):
        # Get all coloring pages that have at least one SEO URL
        return ColoringPage.objects.exclude(seo_url_en__isnull=True, seo_url_de__isnull=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        # Always use English version as canonical URL
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
        protocol = protocol or 'http'
        domain = None
        
        # Try to get the current site domain
        try:
            if site is None:
                site = get_current_site(None)
            domain = site.domain
        except:
            domain = 'localhost:8000'  # Fallback if site framework not properly set up
            
        for item in self.paginator.page(page).object_list:
            path = self.location(item)
            
            # Build the full URL
            if not path.startswith(('http://', 'https://')):
                loc = f"{protocol}://{domain.rstrip('/')}{path}"
            else:
                loc = path
                
            url_info = {
                'item': item,
                'location': loc,
                'lastmod': item.updated_at,
                'changefreq': self._get('changefreq', item, 'daily'),
                'priority': self._get('priority', item, 0.9),
                'alternates': []
            }
            
            # Add alternate language URLs with full URLs
            if item.seo_url_en:  # English version
                en_path = reverse('coloring_pages:detail_en', 
                               kwargs={'seo_url': item.seo_url_en}, 
                               current_app='coloring_pages')
                if not en_path.startswith(('http://', 'https://')):
                    en_url = f"{protocol}://{domain.rstrip('/')}{en_path}"
                else:
                    en_url = en_path
                url_info['alternates'].append({
                    'lang_code': 'en',
                    'location': en_url
                })
                
            if item.seo_url_de:  # German version
                de_path = reverse('coloring_pages:detail_de', 
                               kwargs={'seo_url': item.seo_url_de}, 
                               current_app='coloring_pages')
                if not de_path.startswith(('http://', 'https://')):
                    de_url = f"{protocol}://{domain.rstrip('/')}{de_path}"
                else:
                    de_url = de_path
                url_info['alternates'].append({
                    'lang_code': 'de',
                    'location': de_url
                })
            
            urls.append(url_info)
        
        return urls


# Combine all sitemaps
sitemaps = {
    'static': StaticViewSitemap,
    'coloring_pages': ColoringPageSitemap,
}
