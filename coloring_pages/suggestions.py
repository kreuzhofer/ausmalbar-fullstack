"""
AI-driven creative suggestion engine.
Uses GPT to generate rich, seasonal coloring page ideas from demand signals.
"""
import json
import logging
import os
from datetime import datetime

import openai

from .demand import get_unmet_queries
from .trends import get_ungenerated_trends

logger = logging.getLogger(__name__)

SUGGESTION_MODEL = "gpt-4o"

SYSTEM_PROMPT = """\
You are a creative director for a children's coloring page website (ages 3-10).

Your job is to suggest new coloring page ideas based on:
1. What users are searching for (unmet demand)
2. What's trending on Google Trends
3. The current date and season (for seasonal/holiday relevance)
4. What already exists (to avoid duplicates)

For each suggestion, provide:
- A detailed image prompt describing the coloring page scene (black & white line art, child-friendly)
- Short, engaging titles in English and German
- Descriptions in English and German (1-2 sentences)
- A brief reasoning explaining why this suggestion is timely and relevant

Guidelines:
- Target age 3-10: simple, friendly, no scary content
- Be specific and creative: "A friendly dragon reading a book in a cozy cave" not just "dragon"
- Consider seasonality: Easter in spring, Halloween in fall, Christmas in winter, beach in summer
- Avoid duplicating existing content — suggest complementary or different angles
- Mix trending topics with evergreen children's favorites
- Image prompts should describe LINE ART suitable for coloring: clear outlines, no shading, no color

Respond with a JSON array only, no other text. Each element:
{
  "image_prompt": "detailed line art description...",
  "title_en": "English Title",
  "title_de": "German Title",
  "description_en": "English description...",
  "description_de": "German description...",
  "reasoning": "Why this suggestion is relevant now..."
}
"""


def generate_suggestions(count=5):
    """
    Generate AI-powered coloring page suggestions from demand signals.

    Returns a list of suggestion dicts with keys:
    image_prompt, title_en, title_de, description_en, description_de, reasoning
    """
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # Gather context
    now = datetime.now()
    date_context = now.strftime("%A, %B %d, %Y")

    # Unmet search queries
    unmet = get_unmet_queries(limit=20)
    unmet_text = "\n".join(
        f"- \"{q['query']}\" ({q['count']} searches)"
        for q in unmet
    ) or "No unmet search queries."

    # Google Trends
    trends = get_ungenerated_trends(limit=20)
    trends_text = "\n".join(
        f"- \"{t.query}\" (score: {t.score}, source: {t.get_source_display()})"
        for t in trends
    ) or "No trending data available."

    # Existing pages (to avoid duplicates)
    existing_text = _get_existing_pages_context()

    user_message = f"""Today's date: {date_context}

## Unmet Search Queries (users searched but found nothing)
{unmet_text}

## Google Trends (currently trending coloring page topics)
{trends_text}

## Existing Coloring Pages (avoid duplicating these)
{existing_text}

Please suggest {count} new coloring page ideas. Return JSON array only."""

    logger.info("Generating %d AI suggestions...", count)
    logger.debug("Suggestion prompt context: %d unmet queries, %d trends", len(unmet), len(trends))

    try:
        response = client.chat.completions.create(
            model=SUGGESTION_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.9,
            max_tokens=4000,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content.strip()
        parsed = json.loads(content)

        # Handle both {"suggestions": [...]} and [...] formats
        if isinstance(parsed, dict):
            suggestions = parsed.get("suggestions", parsed.get("ideas", []))
        elif isinstance(parsed, list):
            suggestions = parsed
        else:
            logger.error("Unexpected GPT response format: %s", type(parsed))
            return []

        logger.info("Generated %d AI suggestions", len(suggestions))
        return suggestions[:count]

    except json.JSONDecodeError:
        logger.exception("Failed to parse GPT response as JSON")
        return []
    except Exception:
        logger.exception("Failed to generate AI suggestions")
        return []


def _get_existing_pages_context():
    """Build a compact summary of existing coloring pages for the GPT context."""
    from .models.coloring_page import ColoringPage

    pages = ColoringPage.objects.values_list("title_en", flat=True).order_by("-created_at")[:50]
    if not pages:
        return "No existing coloring pages."
    return "\n".join(f"- {title}" for title in pages)
