"""
Model for storing the auto-generation schedule configuration.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import TimeStampedModel


class GenerationSchedule(TimeStampedModel):
    """
    Stores the schedule configuration for automatic coloring page generation.
    Only one active schedule is supported (singleton pattern via admin).
    """
    enabled = models.BooleanField(
        default=False,
        verbose_name=_("Enabled"),
    )
    interval_hours = models.PositiveIntegerField(
        default=24,
        verbose_name=_("Interval (hours)"),
        help_text=_("How often to run auto-generation, in hours."),
    )
    max_pages = models.PositiveIntegerField(
        default=5,
        verbose_name=_("Max pages per run"),
    )
    last_run = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last run"),
    )
    last_result = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Last run result"),
    )

    class Meta:
        verbose_name = _("Generation Schedule")
        verbose_name_plural = _("Generation Schedule")

    def __str__(self):
        status = "enabled" if self.enabled else "disabled"
        return f"Auto-generation: {status}, every {self.interval_hours}h"

    @classmethod
    def get_schedule(cls):
        """Get or create the singleton schedule instance."""
        schedule, _ = cls.objects.get_or_create(pk=1)
        return schedule
