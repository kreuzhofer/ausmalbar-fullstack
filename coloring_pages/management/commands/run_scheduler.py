"""
Background scheduler that runs auto-generation based on the admin-configured schedule.
Designed to run as a background thread in the gunicorn startup command.
"""
import logging
import time

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run the auto-generation scheduler (long-running, checks schedule periodically)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--check-interval",
            type=int,
            default=300,
            help="How often to check the schedule, in seconds (default: 300).",
        )

    def handle(self, *args, **options):
        check_interval = options["check_interval"]
        self.stdout.write(f"Scheduler started. Checking every {check_interval}s.")
        logger.info("Scheduler started, check interval=%ds", check_interval)

        while True:
            try:
                self._check_and_run()
            except Exception:
                logger.exception("Scheduler tick failed")
            time.sleep(check_interval)

    def _check_and_run(self):
        # Import here to avoid issues with app registry at startup
        from coloring_pages.models.schedule import GenerationSchedule

        schedule = GenerationSchedule.get_schedule()
        if not schedule.enabled:
            return

        now = timezone.now()
        if schedule.last_run:
            elapsed = (now - schedule.last_run).total_seconds() / 3600
            if elapsed < schedule.interval_hours:
                return

        logger.info(
            "Schedule triggered: interval=%dh, max_pages=%d",
            schedule.interval_hours, schedule.max_pages,
        )
        self.stdout.write("Running scheduled generation...")

        try:
            from io import StringIO
            out = StringIO()
            call_command("generate_daily", count=schedule.max_pages, stdout=out)
            output = out.getvalue()

            schedule.last_run = now
            schedule.last_result = output
            schedule.save()

            logger.info("Scheduled generation complete")
            self.stdout.write(self.style.SUCCESS(output))
        except Exception:
            logger.exception("Scheduled generation failed")
            schedule.last_run = now
            schedule.last_result = "Error: see logs"
            schedule.save()
