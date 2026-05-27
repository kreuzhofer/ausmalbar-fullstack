from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.conf import settings
from django.utils import translation
from django.contrib.sites.shortcuts import get_current_site
from .models.coloring_page import ColoringPage


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        # List of all static pages to include in sitemap
        # Each item is a tuple of (view_name, lang_code, alternate_view_name)
        return [
            # Home pages
            ('coloring_pages:home', 'en', 'coloring_pages:home'),  # English home
            ('coloring_pages:home', 'de', 'coloring_pages:home'),  # German home
            
            # Search pages
            ('coloring_pages:search', 'en', 'coloring_pages:suche'),  # English search
            ('coloring_pages:suche', 'de', 'coloring_pages:search'),  # German suche
            
            # Legal pages
            ('coloring_pages:imprint', 'en', 'coloring_pages:impressum'),  # English imprint
            ('coloring_pages:impressum', 'de', 'coloring_pages:imprint'),  # German impressum
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
    """One entry per (page, language) pair. Each entry's <loc> is the URL in
    its own language; each carries xhtml:link alternates for the other language(s)
    plus x-default. Canonical computation is wrapped in translation.override
    so it never depends on the request's Accept-Language header.
    """
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        pages = ColoringPage.objects.filter(
            status=ColoringPage.STATUS_PUBLISHED,
        ).exclude(seo_url_en__isnull=True, seo_url_de__isnull=True)
        # Yield (page, lang) tuples for each available language.
        entries = []
        for page in pages:
            if page.seo_url_en:
                entries.append((page, 'en'))
            if page.seo_url_de:
                entries.append((page, 'de'))
        return entries

    def lastmod(self, item):
        page, _lang = item
        return page.updated_at

    def location(self, item):
        page, lang = item
        with translation.override(lang):
            if lang == 'en':
                return reverse('coloring_pages:detail_en',
                               kwargs={'seo_url': page.seo_url_en},
                               current_app='coloring_pages')
            return reverse('coloring_pages:detail_de',
                           kwargs={'seo_url': page.seo_url_de},
                           current_app='coloring_pages')

    def get_urls(self, page=1, site=None, protocol=None, domain=None):
        urls = []
        protocol = protocol or 'http'
        request = getattr(self, '_request', None)
        if request is not None:
            domain = request.get_host()
            protocol = 'https' if request.is_secure() else 'http'
        if domain is None:
            try:
                if site is None:
                    site = get_current_site(None)
                domain = site.domain
            except Exception:
                domain = 'localhost:8000'
        clean_domain = domain.replace('http://', '').replace('https://', '').rstrip('/')

        for item in self.paginator.page(page).object_list:
            page_obj, lang = item
            path = self.location(item)
            loc = f'{protocol}://{clean_domain}{path}'

            alternates = []
            if page_obj.seo_url_en:
                with translation.override('en'):
                    en_path = reverse('coloring_pages:detail_en',
                                      kwargs={'seo_url': page_obj.seo_url_en},
                                      current_app='coloring_pages')
                alternates.append({
                    'lang_code': 'en',
                    'location': f'{protocol}://{clean_domain}{en_path}',
                })
            if page_obj.seo_url_de:
                with translation.override('de'):
                    de_path = reverse('coloring_pages:detail_de',
                                      kwargs={'seo_url': page_obj.seo_url_de},
                                      current_app='coloring_pages')
                alternates.append({
                    'lang_code': 'de',
                    'location': f'{protocol}://{clean_domain}{de_path}',
                })
            # x-default -> EN if available, else first alternate.
            default_alt = next((a for a in alternates if a['lang_code'] == 'en'),
                               alternates[0] if alternates else None)
            if default_alt:
                alternates.append({
                    'lang_code': 'x-default',
                    'location': default_alt['location'],
                })

            urls.append({
                'item': page_obj,
                'location': loc,
                'lastmod': page_obj.updated_at,
                'changefreq': self.changefreq,
                'priority': self.priority,
                'alternates': alternates,
            })
        return urls


# Combine all sitemaps
sitemaps = {
    'static': StaticViewSitemap,
    'coloring_pages': ColoringPageSitemap,
}
