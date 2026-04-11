"""
Admin views for unmet demand analysis and auto-generation scheduling.
"""
import json
import logging
import threading

from django.contrib import admin
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from ...demand import get_unmet_queries
from ...embeddings import embed_all_pages, embed_coloring_page
from ...models.coloring_page import ColoringPage
from ...models.schedule import GenerationSchedule
from ...models.system_prompt import SystemPrompt
from ...models.trend import TrendQuery
from ...suggestions import generate_suggestions
from ...trends import get_ungenerated_trends, refresh_trends
from ...utils import generate_coloring_page_image

logger = logging.getLogger(__name__)


def demand_dashboard(request):
    """Show unmet demand analysis, trends, and schedule configuration."""
    unmet = get_unmet_queries(limit=20)
    schedule = GenerationSchedule.get_schedule()
    system_prompts = SystemPrompt.objects.all()

    # Trends grouped by source
    trends_de = list(
        TrendQuery.objects.filter(source=TrendQuery.SOURCE_RELATED_DE)
        .order_by("-score")[:15]
    )
    trends_en = list(
        TrendQuery.objects.filter(source=TrendQuery.SOURCE_RELATED_EN)
        .order_by("-score")[:15]
    )
    trends_last_fetched = (
        TrendQuery.objects.order_by("-fetched_at").values_list("fetched_at", flat=True).first()
    )

    context = {
        **admin.site.each_context(request),
        "title": _("Demand Analysis"),
        "unmet_queries": unmet,
        "schedule": schedule,
        "system_prompts": system_prompts,
        "trends_de": trends_de,
        "trends_en": trends_en,
        "trends_last_fetched": trends_last_fetched,
    }
    return TemplateResponse(
        request,
        "admin/coloring_pages/demand/dashboard.html",
        context,
    )


@require_POST
def demand_generate(request):
    """Generate a coloring page from a single query (AJAX)."""
    data = json.loads(request.body)
    query = data.get("query", "").strip()
    if not query:
        return JsonResponse({"error": "No query provided"}, status=400)

    system_prompt = None
    sp_name = data.get("system_prompt")
    if sp_name:
        try:
            system_prompt = SystemPrompt.objects.get(name=sp_name)
        except SystemPrompt.DoesNotExist:
            pass

    try:
        logger.info("Generating page for query: %s", query)

        title_en, title_de, desc_en, desc_de = generate_titles_and_descriptions(query)
        result = generate_coloring_page_image(query, system_prompt=system_prompt)

        page = ColoringPage(
            title_en=title_en[:200],
            title_de=title_de[:200],
            description_en=desc_en,
            description_de=desc_de,
            prompt=query,
            status=ColoringPage.STATUS_DRAFT,
            metadata={
                "source": "demand_dashboard",
                "system_prompt_name": system_prompt.name if system_prompt else "default",
            },
        )
        img_name = f"coloring_page_demand_{query[:30].replace(' ', '_')}.png"
        page.image.save(img_name, ContentFile(result["image_bytes"]), save=False)
        if result.get("thumbnail_bytes"):
            thumb_name = f"thumb_demand_{query[:30].replace(' ', '_')}.png"
            page.thumbnail.save(thumb_name, ContentFile(result["thumbnail_bytes"]), save=False)
        page.save()

        # Mark trend as generated if it came from trends
        trend_id = data.get("trend_id")
        if trend_id:
            TrendQuery.objects.filter(pk=trend_id).update(generated=True)

        logger.info("Generated draft page: %s (id=%d)", page.title_en, page.pk)
        return JsonResponse({
            "success": True,
            "page_id": page.pk,
            "title": page.title_en,
        })

    except Exception as e:
        logger.exception("Failed to generate page for query: %s", query)
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
def demand_refresh_trends(request):
    """Manually trigger a trends refresh."""
    try:
        count = refresh_trends(force=True)
        return JsonResponse({"success": True, "new_trends": count})
    except Exception as e:
        logger.exception("Failed to refresh trends")
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
def demand_generate_batch(request):
    """Generate pages for top N unmet queries in a background thread."""
    data = json.loads(request.body)
    count = min(int(data.get("count", 5)), 10)

    def _run():
        try:
            from io import StringIO
            out = StringIO()
            call_command("generate_daily", count=count, stdout=out)
            output = out.getvalue()
            schedule = GenerationSchedule.get_schedule()
            schedule.last_run = timezone.now()
            schedule.last_result = output
            schedule.save()
            logger.info("Batch generation complete: %s", output[-200:])
        except Exception:
            logger.exception("Batch generation failed")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return JsonResponse({"success": True, "message": f"Generating up to {count} pages in background..."})


@require_POST
def demand_schedule_save(request):
    """Save schedule configuration."""
    data = json.loads(request.body)
    schedule = GenerationSchedule.get_schedule()
    schedule.enabled = data.get("enabled", False)
    schedule.interval_hours = max(1, int(data.get("interval_hours", 24)))
    schedule.max_pages = max(1, min(10, int(data.get("max_pages", 5))))
    schedule.save()

    logger.info(
        "Schedule updated: enabled=%s, interval=%dh, max_pages=%d",
        schedule.enabled, schedule.interval_hours, schedule.max_pages,
    )

    return JsonResponse({
        "success": True,
        "enabled": schedule.enabled,
        "interval_hours": schedule.interval_hours,
        "max_pages": schedule.max_pages,
    })


@require_POST
def demand_ai_suggestions(request):
    """Generate AI-powered coloring page suggestions."""
    data = json.loads(request.body)
    count = min(int(data.get("count", 5)), 10)
    try:
        suggestions = generate_suggestions(count=count)
        return JsonResponse({"success": True, "suggestions": suggestions})
    except Exception as e:
        logger.exception("Failed to generate AI suggestions")
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
def demand_approve_suggestion(request):
    """Approve an AI suggestion: generate the image and create a draft page."""
    data = json.loads(request.body)
    image_prompt = data.get("image_prompt", "").strip()
    title_en = data.get("title_en", "").strip()
    title_de = data.get("title_de", "").strip()
    description_en = data.get("description_en", "").strip()
    description_de = data.get("description_de", "").strip()

    if not image_prompt:
        return JsonResponse({"error": "No image prompt"}, status=400)

    try:
        logger.info("Generating image from AI suggestion: %s", image_prompt[:80])
        result = generate_coloring_page_image(image_prompt)

        page = ColoringPage(
            title_en=title_en[:200] or "Untitled",
            title_de=title_de[:200] or "Ohne Titel",
            description_en=description_en or title_en,
            description_de=description_de or title_de,
            prompt=image_prompt,
            status=ColoringPage.STATUS_DRAFT,
            metadata={"source": "ai_suggestion"},
        )
        img_name = f"coloring_ai_{title_en[:30].replace(' ', '_')}.png"
        page.image.save(img_name, ContentFile(result["image_bytes"]), save=False)
        if result.get("thumbnail_bytes"):
            thumb_name = f"thumb_ai_{title_en[:30].replace(' ', '_')}.png"
            page.thumbnail.save(thumb_name, ContentFile(result["thumbnail_bytes"]), save=False)
        page.save()

        # Generate embedding for the new page
        try:
            embed_coloring_page(page)
        except Exception:
            logger.warning("Failed to embed new page %d", page.pk)

        return JsonResponse({
            "success": True,
            "page_id": page.pk,
            "title": page.title_en,
        })
    except Exception as e:
        logger.exception("Failed to generate image from AI suggestion")
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
def demand_embed_all(request):
    """Trigger embedding generation for all pages."""
    def _run():
        try:
            count = embed_all_pages()
            logger.info("Embed all pages complete: %d pages", count)
        except Exception:
            logger.exception("Embed all pages failed")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return JsonResponse({"success": True, "message": "Embedding generation started in background..."})


def get_demand_urls():
    """Return URL patterns for the demand dashboard."""
    return [
        path(
            "demand/",
            admin.site.admin_view(demand_dashboard),
            name="demand_dashboard",
        ),
        path(
            "demand/generate/",
            admin.site.admin_view(demand_generate),
            name="demand_generate",
        ),
        path(
            "demand/generate-batch/",
            admin.site.admin_view(demand_generate_batch),
            name="demand_generate_batch",
        ),
        path(
            "demand/schedule/",
            admin.site.admin_view(demand_schedule_save),
            name="demand_schedule_save",
        ),
        path(
            "demand/refresh-trends/",
            admin.site.admin_view(demand_refresh_trends),
            name="demand_refresh_trends",
        ),
        path(
            "demand/ai-suggestions/",
            admin.site.admin_view(demand_ai_suggestions),
            name="demand_ai_suggestions",
        ),
        path(
            "demand/approve-suggestion/",
            admin.site.admin_view(demand_approve_suggestion),
            name="demand_approve_suggestion",
        ),
        path(
            "demand/embed-all/",
            admin.site.admin_view(demand_embed_all),
            name="demand_embed_all",
        ),
    ]
