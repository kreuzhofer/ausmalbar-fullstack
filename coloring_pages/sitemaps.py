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
        # Each item is a tuple of (view_name, lang_code, alternate_view_name)
        return [
            ('coloring_pages:home', 'en', 'coloring_pages:home'),  # English home
            ('coloring_pages:home', 'de', 'coloring_pages:home'),  # German home
            ('coloring_pages:search', None, None),  # Search handles both languages
            ('coloring_pages:imprint', 'en', 'coloring_pages:imprint'),
            ('coloring_pages:imprint', 'de', 'coloring_pages:imprint'),
            ('coloring_pages:privacy_policy', 'en', 'coloring_pages:datenschutz'),
            ('coloring_pages:datenschutz', 'de', 'coloring_pages:privacy_policy'),
            ('coloring_pages:terms_of_service', 'en', 'coloring_pages:nutzungsbedingungen'),
            ('coloring_pages:nutzungsbedingungen', 'de', 'coloring_pages:terms_of_service'),
        ]

    def location(self, item):
        view_name, lang_code, _ = item
        # Use the specified language for the URL
        if lang_code:
            with translation.override(lang_code):
                return reverse(view_name, current_app='coloring_pages')
        # For None lang_code, let the view handle language detection
        return reverse(view_name, current_app='coloring_pages')
            
    def get_urls(self, page=1, site=None, protocol=None, domain=None):
        # Override to include proper domain from the request
        urls = []
        protocol = protocol or 'http'
        
        # Get domain from request if available
        request = getattr(self, '_request', None)
        if request is not None:
            domain = request.get_host()
            protocol = 'https' if request.is_secure() else 'http'
        
        # Fallback to site framework if no request
        if domain is None:
            try:
                if site is None:
                    site = get_current_site(None)
                domain = site.domain
            except:
                domain = 'localhost:8000'  # Final fallback
        
        for item in self.items():
            path = self.location(item)
            
            # Build the full URL
            if not path.startswith(('http://', 'https://')):
                # Ensure domain doesn't have protocol
                clean_domain = domain.replace('http://', '').replace('https://', '').rstrip('/')
                loc = f"{protocol}://{clean_domain}{path}"
            else:
                loc = path
                
            # Add alternate language URLs for static pages
            alternates = []
            view_name, current_lang, alternate_view_name = item
            
            # Only add alternates for pages that have language-specific versions
            if current_lang and alternate_view_name:
                # Determine the alternate language code
                alt_lang = 'de' if current_lang == 'en' else 'en'
                
                # Generate the alternate URL
                with translation.override(alt_lang):
                    alt_path = reverse(alternate_view_name, current_app='coloring_pages')
                    if not alt_path.startswith(('http://', 'https://')):
                        alt_url = f"{protocol}://{clean_domain}{alt_path}"
                    else:
                        alt_url = alt_path
                    alternates.append({'lang_code': alt_lang, 'location': alt_url})
            
            url_info = {
                'location': loc,
                'changefreq': self._get('changefreq', None, 'weekly'),
                'priority': self._get('priority', None, 0.8),
                'lastmod': None,
                'alternates': alternates
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

    def get_urls(self, page=1, site=None, protocol=None, domain=None):
        # Override to include hreflang links for each URL
        urls = []
        protocol = protocol or 'http'
        
        # Get domain from request if available
        request = getattr(self, '_request', None)
        if request is not None:
            domain = request.get_host()
            protocol = 'https' if request.is_secure() else 'http'
        
        # Fallback to site framework if no request
        if domain is None:
            try:
                if site is None:
                    site = get_current_site(None)
                domain = site.domain
            except:
                domain = 'localhost:8000'  # Final fallback
        
        # Clean up the domain
        clean_domain = domain.replace('http://', '').replace('https://', '').rstrip('/')
        
        for item in self.paginator.page(page).object_list:
            path = self.location(item)
            
            # Build the full URL
            if not path.startswith(('http://', 'https://')):
                loc = f"{protocol}://{clean_domain}{path}"
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
                    en_url = f"{protocol}://{clean_domain}{en_path}"
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
                    de_url = f"{protocol}://{clean_domain}{de_path}"
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
