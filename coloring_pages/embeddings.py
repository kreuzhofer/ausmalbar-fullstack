"""
Vector embedding utilities for semantic search and content similarity.
Uses OpenAI text-embedding-3-large (3072 dimensions).
"""
import logging
import os

import openai
from pgvector.django import CosineDistance

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-large"


def _get_client():
    return openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def generate_embedding(text: str) -> list[float]:
    """Generate a vector embedding for the given text."""
    client = _get_client()
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text[:8000],  # truncate to stay within token limits
    )
    return response.data[0].embedding


def _page_text(page) -> str:
    """Combine a ColoringPage's text fields into a single string for embedding."""
    parts = [
        page.title_en or "",
        page.title_de or "",
        page.description_en or "",
        page.description_de or "",
        page.prompt or "",
    ]
    return " | ".join(p.strip() for p in parts if p.strip())


def embed_coloring_page(page, save=True):
    """Generate and store an embedding for a single ColoringPage."""
    text = _page_text(page)
    if not text:
        logger.warning("Page %d has no text to embed", page.pk)
        return

    embedding = generate_embedding(text)
    page.embedding = embedding
    if save:
        # Use update to avoid triggering the full save() with thumbnail regeneration
        from .models.coloring_page import ColoringPage
        ColoringPage.objects.filter(pk=page.pk).update(embedding=embedding)
    logger.debug("Embedded page %d: %s", page.pk, page.title_en[:50])


def embed_all_pages(force=False):
    """
    Generate embeddings for all pages that don't have one yet.
    If force=True, re-embed all pages.
    """
    from .models.coloring_page import ColoringPage

    if force:
        pages = ColoringPage.objects.all()
    else:
        pages = ColoringPage.objects.filter(embedding__isnull=True)

    count = pages.count()
    if count == 0:
        logger.info("All pages already have embeddings")
        return 0

    logger.info("Embedding %d pages...", count)
    embedded = 0
    for page in pages.iterator():
        try:
            embed_coloring_page(page)
            embedded += 1
            if embedded % 10 == 0:
                logger.info("  Embedded %d/%d pages", embedded, count)
        except Exception:
            logger.exception("Failed to embed page %d", page.pk)

    logger.info("Embedding complete: %d/%d pages", embedded, count)
    return embedded


def find_similar_pages(text: str, limit=10, published_only=True):
    """
    Find ColoringPages most similar to the given text using vector cosine distance.
    Returns a QuerySet annotated with `distance`.
    """
    from .models.coloring_page import ColoringPage

    embedding = generate_embedding(text)
    qs = ColoringPage.objects.filter(embedding__isnull=False)
    if published_only:
        qs = qs.filter(status=ColoringPage.STATUS_PUBLISHED)
    return (
        qs.annotate(distance=CosineDistance("embedding", embedding))
        .order_by("distance")[:limit]
    )


def find_similar_to_queries(queries: list[str], limit=10):
    """
    Find existing pages similar to any of the given query strings.
    Combines queries into one embedding for efficiency.
    """
    combined = " | ".join(queries[:20])
    return find_similar_pages(combined, limit=limit, published_only=False)
