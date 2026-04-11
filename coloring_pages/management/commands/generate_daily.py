"""
Management command to generate coloring pages from top unmet search queries.
"""
import logging

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from ...demand import get_unmet_queries
from ...models.coloring_page import ColoringPage
from ...models.system_prompt import SystemPrompt
from ...utils import generate_coloring_page_image, generate_titles_and_descriptions

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generate coloring pages for the top unmet search queries (saved as drafts)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=5,
            help="Maximum number of pages to generate (default: 5).",
        )
        parser.add_argument(
            "--system-prompt",
            type=str,
            default=None,
            help="Name of the SystemPrompt to use. Defaults to 'default-image'.",
        )
        parser.add_argument(
            "--publish",
            action="store_true",
            default=False,
            help="Publish pages immediately instead of saving as drafts.",
        )

    def handle(self, *args, **options):
        count = options["count"]
        prompt_name = options["system_prompt"] or "default-image"
        status = (
            ColoringPage.STATUS_PUBLISHED if options["publish"]
            else ColoringPage.STATUS_DRAFT
        )

        # Load system prompt
        system_prompt = None
        try:
            system_prompt = SystemPrompt.objects.get(name=prompt_name)
            self.stdout.write(f"Using system prompt: {system_prompt.name}")
        except SystemPrompt.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(
                    f"System prompt '{prompt_name}' not found, using default."
                )
            )

        # Find unmet queries
        unmet = get_unmet_queries(limit=count)
        if not unmet:
            self.stdout.write(self.style.WARNING("No unmet queries found."))
            return

        self.stdout.write(f"Found {len(unmet)} unmet queries to generate:")
        for entry in unmet:
            self.stdout.write(f"  - \"{entry['query']}\" ({entry['count']} searches)")

        generated = 0
        for entry in unmet:
            query = entry["query"]
            self.stdout.write(f"\nGenerating: \"{query}\"...")

            try:
                # Generate titles and descriptions
                title_en, title_de, desc_en, desc_de = (
                    generate_titles_and_descriptions(query)
                )
                self.stdout.write(f"  Titles: EN=\"{title_en}\" / DE=\"{title_de}\"")

                # Generate image
                result = generate_coloring_page_image(
                    query, system_prompt=system_prompt
                )

                # Create ColoringPage as draft
                page = ColoringPage(
                    title_en=title_en[:200],
                    title_de=title_de[:200],
                    description_en=desc_en,
                    description_de=desc_de,
                    prompt=query,
                    status=status,
                    metadata={
                        "source": "auto_generated",
                        "search_count": entry["count"],
                        "system_prompt_name": (
                            system_prompt.name if system_prompt else "default"
                        ),
                    },
                )

                # Save image
                img_name = f"coloring_page_auto_{query[:30].replace(' ', '_')}.png"
                page.image.save(
                    img_name, ContentFile(result["image_bytes"]), save=False
                )

                # Save thumbnail
                if result.get("thumbnail_bytes"):
                    thumb_name = f"thumb_auto_{query[:30].replace(' ', '_')}.png"
                    page.thumbnail.save(
                        thumb_name,
                        ContentFile(result["thumbnail_bytes"]),
                        save=False,
                    )

                page.save()
                generated += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Created: {page.title_en} (status={page.status})"
                    )
                )

            except Exception as e:
                logger.exception("Failed to generate page for query: %s", query)
                self.stdout.write(
                    self.style.ERROR(f"  Failed: {e}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. Generated {generated}/{len(unmet)} pages as {status}."
            )
        )
