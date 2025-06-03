from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.urls import reverse
from django.conf import settings
from coloring_pages.models.coloring_page import ColoringPage
import os
from datetime import datetime

class Command(BaseCommand):
    help = 'Generate a sitemap.xml file for SEO'

    def handle(self, *args, **options):
        # Get the current site domain
        current_site = Site.objects.get_current()
        domain = current_site.domain
        
        # Start the sitemap XML
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        
        # Add static URLs
        static_urls = [
            reverse('home'),
            reverse('search'),
        ]
        
        # Add static pages
        for url in static_urls:
            xml += self.url_to_xml(f'https://{domain}{url}')
        
        # Add coloring pages
        for page in ColoringPage.objects.all():
            url = f'https://{domain}{reverse("page_detail", args=[page.id])}'
            xml += self.url_to_xml(url, page.updated_at)
        
        # Close the sitemap
        xml += '</urlset>'
        
        # Write to file
        sitemap_path = os.path.join(settings.BASE_DIR, 'static', 'sitemap.xml')
        os.makedirs(os.path.dirname(sitemap_path), exist_ok=True)
        
        with open(sitemap_path, 'w') as f:
            f.write(xml)
        
        self.stdout.write(self.style.SUCCESS(f'Sitemap generated at {sitemap_path}'))
    
    def url_to_xml(self, url, lastmod=None):
        """Convert a URL to sitemap XML format"""
        if lastmod is None:
            lastmod = datetime.now().strftime('%Y-%m-%d')
        else:
            lastmod = lastmod.strftime('%Y-%m-%d')
            
        return f'  <url>\n    <loc>{url}</loc>\n    <lastmod>{lastmod}</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>0.8</priority>\n  </url>\n'
