"""History of past SEO slugs, used to 301-redirect old URLs to the current slug."""
from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import TimeStampedModel


class ColoringPageSlugHistory(TimeStampedModel):
    """A slug that a ColoringPage used to have, in a given language."""

    LANG_EN = 'en'
    LANG_DE = 'de'
    LANG_CHOICES = [(LANG_EN, 'English'), (LANG_DE, 'German')]

    page = models.ForeignKey(
        'coloring_pages.ColoringPage',
        on_delete=models.CASCADE,
        related_name='slug_history',
    )
    language = models.CharField(max_length=2, choices=LANG_CHOICES, db_index=True)
    slug = models.SlugField(max_length=255, db_index=True)

    class Meta:
        verbose_name = _('Slug History Entry')
        verbose_name_plural = _('Slug History Entries')
        unique_together = [('language', 'slug')]
        indexes = [models.Index(fields=['language', 'slug'])]

    def __str__(self):
        return f'{self.language}:{self.slug} → page #{self.page_id}'
