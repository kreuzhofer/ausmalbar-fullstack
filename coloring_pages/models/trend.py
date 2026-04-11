"""
Model for caching Google Trends data.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import TimeStampedModel


class TrendQuery(TimeStampedModel):
    """
    Caches a trending search query fetched from Google Trends.
    """
    SOURCE_RELATED_DE = "related_de"
    SOURCE_RELATED_EN = "related_en"
    SOURCE_TRENDING = "trending"
    SOURCE_CHOICES = [
        (SOURCE_RELATED_DE, _("Related (Germany)")),
        (SOURCE_RELATED_EN, _("Related (Worldwide)")),
        (SOURCE_TRENDING, _("Trending")),
    ]

    query = models.CharField(max_length=300, db_index=True, verbose_name=_("Query"))
    source = models.CharField(
        max_length=20, choices=SOURCE_CHOICES, verbose_name=_("Source")
    )
    score = models.IntegerField(
        default=0,
        verbose_name=_("Score"),
        help_text=_("Relative popularity score from Google Trends."),
    )
    fetched_at = models.DateTimeField(verbose_name=_("Fetched at"))
    generated = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_("Generated"),
        help_text=_("Whether a coloring page has been created from this trend."),
    )

    class Meta:
        ordering = ["-score", "-fetched_at"]
        verbose_name = _("Trend Query")
        verbose_name_plural = _("Trend Queries")
        unique_together = [("query", "source")]

    def __str__(self):
        return f"{self.query} ({self.get_source_display()}, score={self.score})"
