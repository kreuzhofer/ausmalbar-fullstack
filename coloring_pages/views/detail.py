"""
Views for individual coloring page details and downloads.
"""
import re
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from ..models import ColoringPage

def page_detail(request, pk):
    """
    Legacy view that redirects to the new SEO-friendly URL format.
    """
    page = get_object_or_404(ColoringPage, pk=pk)
    return redirect(page.get_absolute_url(), permanent=True)

def download_image(request, pk):
    """
    Download the coloring page image.
    """
    coloring_page = get_object_or_404(ColoringPage, pk=pk)
    if not coloring_page.image:
        raise Http404("Image not found")
    
    # Get the appropriate title based on the current language
    language = request.LANGUAGE_CODE or 'en'
    title = getattr(coloring_page, f'title_{language[:2]}', 'coloring_page')
    
    # Clean up the filename to be URL-safe
    filename = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
    
    response = HttpResponse(coloring_page.image.read(), content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="{filename}.png"'
    return response
