"""
Home view for the coloring pages application.
"""
from django.shortcuts import render
from ..models.coloring_page import ColoringPage

def home(request):
    """
    Render the home page with the latest coloring pages.
    """
    latest_pages = ColoringPage.objects.all()[:3]
    return render(request, 'coloring_pages/home.html', {'latest_pages': latest_pages})
