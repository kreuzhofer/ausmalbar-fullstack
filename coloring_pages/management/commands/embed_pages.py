"""
Management command to backfill embeddings for existing coloring pages.
"""
from django.core.management.base import BaseCommand

from ...embeddings import embed_all_pages


class Command(BaseCommand):
    help = "Generate vector embeddings for all coloring pages that don't have one yet."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help="Re-embed all pages, even those that already have embeddings.",
        )

    def handle(self, *args, **options):
        self.stdout.write("Generating embeddings for coloring pages...")
        count = embed_all_pages(force=options["force"])
        self.stdout.write(
            self.style.SUCCESS(f"Done. Embedded {count} pages.")
        )
