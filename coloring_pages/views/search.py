"""
Search functionality for coloring pages.
"""
from django.db.models import Q
from django.shortcuts import render
from django.core.paginator import Paginator
from django.utils.translation import get_language
from ..models.search import SearchQuery
from ..models.coloring_page import ColoringPage

def search(request):
    """
    Search for coloring pages with tracking of search queries.
    """
    query = request.GET.get('q', '').strip()
    
    # Search in both English and German fields
    if query:
        pages = ColoringPage.objects.filter(
            Q(title_en__icontains=query) |
            Q(description_en__icontains=query) |
            Q(title_de__icontains=query) |
            Q(description_de__icontains=query) |
            Q(prompt__icontains=query)
        ).distinct()
        
        # Track search query if not a duplicate
        if not SearchQuery.is_duplicate_search(request, query):
            SearchQuery.create_from_request(request, query, pages.count())
    else:
        pages = ColoringPage.objects.all()
    
    # Order by most recent first
    pages = pages.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(pages, 8)  # 8 items per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get popular searches for the sidebar (only show on empty search)
    popular_searches = []
    if not query:
        current_language = get_language() or 'en'
        popular_searches = SearchQuery.get_popular_searches(
            days=30, 
            limit=5,
            language=current_language  # Only show popular searches in the current language
        )
    
    context = {
        'query': query,
        'page_obj': page_obj,
        'popular_searches': popular_searches,
        'is_search': bool(query),
    }
    
    # Store current search in session for back navigation
    if query:
        if not request.session.session_key:
            request.session.create()
            
        request.session['last_search'] = {
            'query': query,
            'result_count': pages.count(),
            'timestamp': request.session.get('last_search', {}).get('timestamp', ''),
            'language': get_language() or 'en'  # Store the language with the search
        }
    
    return render(request, 'coloring_pages/search.html', context)
