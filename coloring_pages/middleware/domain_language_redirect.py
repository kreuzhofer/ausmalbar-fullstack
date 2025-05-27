from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from urllib.parse import urlparse

class DomainLanguageRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Get domain to language mapping from settings
        self.domain_language_map = {}
        
        # Parse DOMAIN_LANGUAGE_MAPPING from settings
        # Format: "domain1.com:lang1,domain2.com:lang2"
        domain_mapping = getattr(settings, 'DOMAIN_LANGUAGE_MAPPING', '')
        for mapping in domain_mapping.split(','):
            if ':' in mapping:
                domain, lang = mapping.split(':', 1)
                self.domain_language_map[domain.strip()] = lang.strip()

    def __call__(self, request):
        # Only process root URL
        if request.path != '/':
            return self.get_response(request)
            
        # Get the host from the request
        host = request.get_host().split(':')[0]  # Remove port if present
        
        # Check if we have a language mapping for this domain
        target_language = None
        for domain, lang in self.domain_language_map.items():
            if host == domain or host == f'www.{domain}':
                target_language = lang
                break
        
        # If we found a matching domain, redirect to the appropriate language
        if target_language:
            # Get the current path and query string
            path = request.get_full_path().lstrip('/')
            redirect_url = f'/{target_language}/{path}'
            return HttpResponsePermanentRedirect(redirect_url)
            
        # No matching domain, continue with normal processing
        return self.get_response(request)
