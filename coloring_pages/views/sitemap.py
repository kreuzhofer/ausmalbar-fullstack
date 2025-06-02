"""
Sitemap view for the coloring pages application.
"""
from django.shortcuts import render
from django.http import Http404

def sitemap(request, *args, **kwargs):
    """
    Custom sitemap view that passes the request to sitemaps
    """
    # Get the sitemaps dict
    from ..sitemaps import sitemaps
    
    # Create a copy of the sitemaps dict to avoid modifying the original
    sitemaps_instances = {}
    
    # Initialize sitemap instances and pass the request
    for name, sitemap_class in sitemaps.items():
        if isinstance(sitemap_class, type):  # It's a class, instantiate it
            sitemap_instance = sitemap_class()
            sitemap_instance._request = request
            sitemaps_instances[name] = sitemap_instance
        else:  # It's already an instance
            sitemap_class._request = request
            sitemaps_instances[name] = sitemap_class
    
    # Import here to avoid circular imports
    from django.contrib.sitemaps.views import sitemap as django_sitemap_view
    
    # Call the original sitemap view with our updated sitemaps
    return django_sitemap_view(
        request,
        sitemaps=sitemaps_instances,
        template_name='sitemap.xml',
        content_type='application/xml',
        *args, **kwargs
    )
