"""
Search functionality for coloring pages.
Uses vector similarity search with keyword fallback.
"""
import logging

from django.db.models import Q
from django.shortcuts import render
from django.core.paginator import Paginator
from django.utils.translation import get_language
from ..models.search import SearchQuery
from ..models.coloring_page import ColoringPage

logger = logging.getLogger(__name__)


def _vector_search(query):
    """
    Try vector similarity search. Returns a queryset or None on failure.
    """
    try:
        from ..embeddings import find_similar_pages
        results = find_similar_pages(query, limit=50, published_only=True)
        # Only return results with reasonable similarity (distance < 0.5)
        return [r for r in results if r.distance < 0.5]
    except Exception:
        logger.debug("Vector search failed, falling back to keyword search", exc_info=True)
        return None


def _keyword_search(query):
    """Keyword-based search as fallback."""
    return ColoringPage.objects.filter(
        Q(title_en__icontains=query) |
        Q(description_en__icontains=query) |
        Q(title_de__icontains=query) |
        Q(description_de__icontains=query) |
        Q(prompt__icontains=query),
        status=ColoringPage.STATUS_PUBLISHED,
    ).distinct().order_by('-created_at')


def search(request):
    """
    Search for coloring pages with tracking of search queries.
    """
    query = request.GET.get('q', '').strip()

    if query:
        # Try vector search first, fall back to keyword
        vector_results = _vector_search(query)
        if vector_results is not None and len(vector_results) > 0:
            pages = vector_results
            result_count = len(pages)
            # Paginate the list (not a queryset)
            paginator = Paginator(pages, 8)
        else:
            pages = _keyword_search(query)
            result_count = pages.count()
            paginator = Paginator(pages, 8)

        # Track search query if not a duplicate
        if not SearchQuery.is_duplicate_search(request, query):
            SearchQuery.create_from_request(request, query, result_count)
    else:
        pages = ColoringPage.objects.filter(
            status=ColoringPage.STATUS_PUBLISHED
        ).order_by('-created_at')
        result_count = pages.count()
        paginator = Paginator(pages, 8)

    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Get popular searches for the sidebar (only show on empty search)
    popular_searches = []
    if not query:
        current_language = get_language() or 'en'
        popular_searches = SearchQuery.get_popular_searches(
            days=30,
            limit=5,
            language=current_language
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
            'result_count': result_count,
            'timestamp': request.session.get('last_search', {}).get('timestamp', ''),
            'language': get_language() or 'en'
        }

    return render(request, 'coloring_pages/search.html', context)
