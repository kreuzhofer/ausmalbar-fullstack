"""
Analyse search queries to find unmet user demand for coloring pages.
"""
import logging

from django.db.models import Count, Max, Q
from django.db.models.functions import Lower, Trim

from .models.coloring_page import ColoringPage
from .models.search import SearchQuery

logger = logging.getLogger(__name__)


def get_unmet_queries(limit=5):
    """
    Find the most frequently searched queries that returned zero results,
    excluding queries that have already been used to generate a coloring page.

    Returns a list of dicts:
        [{"query": str, "count": int, "last_searched": datetime}, ...]
    """
    # Get existing prompts and titles to exclude already-generated content
    existing = set()
    for page in ColoringPage.objects.values_list(
        "prompt", "title_en", "title_de"
    ):
        for val in page:
            if val:
                existing.add(val.strip().lower())

    # Find zero-result queries, grouped by normalized text
    unmet = (
        SearchQuery.objects.filter(result_count=0)
        .exclude(query="")
        .annotate(
            normalized=Lower(Trim("query")),
        )
        .values("normalized")
        .annotate(
            count=Count("id"),
            last_searched=Max("created_at"),
        )
        .order_by("-count")
    )

    results = []
    for entry in unmet:
        query = entry["normalized"]
        if query in existing:
            continue
        results.append({
            "query": query,
            "count": entry["count"],
            "last_searched": entry["last_searched"],
        })
        if len(results) >= limit:
            break

    logger.info("Found %d unmet queries (limit=%d)", len(results), limit)
    return results
