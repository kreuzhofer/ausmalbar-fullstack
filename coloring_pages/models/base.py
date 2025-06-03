"""
Base models and utilities for the coloring_pages app.
"""
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

# GeoIP2 is optional
try:
    from django.contrib.gis.geoip2 import GeoIP2
    from django.contrib.gis.geoip2 import GeoIP2Exception
    
    try:
        geoip = GeoIP2()
        GEOIP_AVAILABLE = True
    except (ImportError, OSError, GeoIP2Exception):
        geoip = None
        GEOIP_AVAILABLE = False
except (ImportError, OSError):
    GeoIP2 = None
    geoip = None
    GEOIP_AVAILABLE = False


def create_unique_slug(model, field_value, field_name, slug_field_name):
    """
    Create a unique slug by appending an index if necessary.
    
    Args:
        model: The model class
        field_value: The value to convert to a slug
        field_name: The name of the field being slugified
        slug_field_name: The name of the slug field
        
    Returns:
        str: A unique slug
    """
    slug = slugify(field_value)
    unique_slug = slug
    num = 1
    
    # Check if a slug with this name already exists
    while model.objects.filter(**{f"{slug_field_name}__iexact": unique_slug}).exists():
        unique_slug = f"{slug}-{num}"
        num += 1
    
    return unique_slug


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    'created_at' and 'updated_at' fields.
    """
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        abstract = True
