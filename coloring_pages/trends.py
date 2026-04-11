"""
Fetch and cache Google Trends data for coloring page demand analysis.
"""
import logging
from datetime import timedelta

from django.utils import timezone

logger = logging.getLogger(__name__)

# Minimum hours between trend refreshes to avoid rate limiting
CACHE_HOURS = 6


def _get_pytrends():
    """Create a pytrends TrendReq instance."""
    from pytrends.request import TrendReq
    return TrendReq(hl="de", tz=60)


def fetch_related_trends():
    """
    Fetch related queries for coloring page keywords.
    Returns list of (query, source, score) tuples.
    """
    results = []
    pt = _get_pytrends()

    keywords_sources = [
        (["Ausmalbild"], "DE", "related_de"),
        (["coloring page"], "", "related_en"),
    ]

    for keywords, geo, source in keywords_sources:
        try:
            pt.build_payload(keywords, cat=0, timeframe="today 3-m", geo=geo)
            related = pt.related_queries()

            for kw in keywords:
                if kw not in related:
                    continue
                # "top" related queries (most popular)
                top = related[kw].get("top")
                if top is not None and not top.empty:
                    for _, row in top.iterrows():
                        query = str(row.get("query", "")).strip()
                        score = int(row.get("value", 0))
                        if query and len(query) > 2:
                            results.append((query, source, score))

                # "rising" related queries (growing fast)
                rising = related[kw].get("rising")
                if rising is not None and not rising.empty:
                    for _, row in rising.iterrows():
                        query = str(row.get("query", "")).strip()
                        # Rising scores can be strings like "Breakout"
                        try:
                            score = int(row.get("value", 0))
                        except (ValueError, TypeError):
                            score = 100
                        if query and len(query) > 2:
                            results.append((query, source, score))

        except Exception:
            logger.exception("Failed to fetch related trends for %s (geo=%s)", keywords, geo)

    logger.info("Fetched %d related trend queries", len(results))
    return results


def fetch_trending_topics():
    """
    Fetch currently trending searches in Germany.
    Returns list of (query, source, score) tuples.
    """
    results = []
    pt = _get_pytrends()

    try:
        trending = pt.trending_searches(pn="germany")
        if trending is not None and not trending.empty:
            for _, row in trending.iterrows():
                query = str(row.iloc[0]).strip()
                if query and len(query) > 2:
                    results.append((query, "trending", 50))
    except Exception:
        logger.exception("Failed to fetch trending searches")

    logger.info("Fetched %d trending topics", len(results))
    return results


def refresh_trends(force=False):
    """
    Fetch and store trends in the database.
    Respects a cache window to avoid hammering Google.
    Returns the number of new/updated trend entries.
    """
    from .models.trend import TrendQuery

    # Check cache freshness
    if not force:
        latest = TrendQuery.objects.order_by("-fetched_at").first()
        if latest and (timezone.now() - latest.fetched_at) < timedelta(hours=CACHE_HOURS):
            logger.info(
                "Trends cache still fresh (last fetch: %s), skipping refresh",
                latest.fetched_at,
            )
            return 0

    now = timezone.now()
    count = 0

    # Fetch all trends
    all_trends = []
    all_trends.extend(fetch_related_trends())
    all_trends.extend(fetch_trending_topics())

    # Deduplicate by (query, source), keeping highest score
    seen = {}
    for query, source, score in all_trends:
        key = (query.lower().strip(), source)
        if key not in seen or score > seen[key][2]:
            seen[key] = (query, source, score)

    # Upsert into database
    for query, source, score in seen.values():
        _, created = TrendQuery.objects.update_or_create(
            query=query,
            source=source,
            defaults={
                "score": score,
                "fetched_at": now,
            },
        )
        if created:
            count += 1

    logger.info("Trends refresh complete: %d new, %d total", count, len(seen))
    return count


def get_ungenerated_trends(limit=10):
    """
    Get top trending queries that haven't been used to generate a page yet.
    """
    from .models.trend import TrendQuery

    return list(
        TrendQuery.objects.filter(generated=False)
        .order_by("-score", "-fetched_at")[:limit]
    )
