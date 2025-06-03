from django.db import models
from django.utils import timezone
from django.core.files.base import ContentFile
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.utils.text import slugify
from django.utils.translation import get_language, get_language_from_request
from django.urls import reverse
from django.db.models import Avg, Count, F, Max, Q
from django.contrib.sessions.models import Session
from django.utils.http import urlencode
from PIL import Image
import io
import os
import uuid
import re
import json
from django.db.models.signals import pre_delete
from django.dispatch import receiver
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
    """
    slug = slugify(field_value)
    unique_slug = slug
    num = 1
    
    # Check if a slug with this name already exists
    while model.objects.filter(**{f"{slug_field_name}__iexact": unique_slug}).exists():
        unique_slug = f"{slug}-{num}"
        num += 1
    
    return unique_slug

class ColoringPage(models.Model):
    # English fields
    title_en = models.CharField(max_length=200, verbose_name='Title (English)')
    description_en = models.TextField(verbose_name='Description (English)')
    
    # German fields
    title_de = models.CharField(max_length=200, verbose_name='Title (German)')
    description_de = models.TextField(verbose_name='Description (German)')
    
    # Common fields
    prompt = models.TextField()
    image = models.ImageField(upload_to='coloring_pages/')
    thumbnail = models.ImageField(upload_to='coloring_pages/thumbnails/', blank=True)
    seo_url_en = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name='SEO URL (English)')
    seo_url_de = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name='SEO URL (German)')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['seo_url_en']),
            models.Index(fields=['seo_url_de']),
        ]
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        # Generate SEO URLs if they don't exist or if the title has changed
        if not self.seo_url_en or 'title_en' in self.get_changed_fields():
            self.seo_url_en = create_unique_slug(ColoringPage, self.title_en, 'title_en', 'seo_url_en')
        
        if not self.seo_url_de or 'title_de' in self.get_changed_fields():
            self.seo_url_de = create_unique_slug(ColoringPage, self.title_de, 'title_de', 'seo_url_de')
        
        super().save(*args, **kwargs)

    def save(self, *args, **kwargs):
        # Only process if this is a new image or the image has changed
        if self.image and (not self.pk or 'image' in self.get_changed_fields()):
            try:
                # Open original image
                with Image.open(self.image) as img:
                    # Convert to RGB if necessary (for PNG with transparency)
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background
                    
                    # Create thumbnail with high-quality downsampling
                    img.thumbnail(
                        settings.THUMBNAIL_SIZE,
                        Image.Resampling.LANCZOS
                    )
                    
                    # Save thumbnail to memory in WebP format
                    thumb_io = io.BytesIO()
                    img.save(
                        thumb_io,
                        format=settings.THUMBNAIL_FORMAT,
                        quality=settings.THUMBNAIL_QUALITY,
                        optimize=True,
                        progressive=True
                    )
                    
                    # Create thumbnail filename with WebP extension
                    original_name = os.path.splitext(os.path.basename(self.image.name))[0]
                    thumb_filename = f"{original_name}_thumb.{settings.THUMBNAIL_FORMAT.lower()}"
                    
                    # Delete old thumbnail if it exists
                    if self.thumbnail:
                        self.thumbnail.delete(save=False)
                    
                    # Save new thumbnail
                    self.thumbnail.save(
                        thumb_filename,
                        ContentFile(thumb_io.getvalue()),
                        save=False
                    )
                    
            except Exception as e:
                # If there's an error processing the image, continue without thumbnail
                print(f"Error generating thumbnail: {str(e)}")
        
        super().save(*args, **kwargs)
    
    def get_changed_fields(self):
        """Helper method to get changed fields"""
        if not self.pk:
            return []
        model = self.__class__
        old = model.objects.get(pk=self.pk)
        return [field.name for field in model._meta.fields 
                if getattr(self, field.name) != getattr(old, field.name)]

    def __str__(self):
        return self.title_en

    class Meta:
        ordering = ['-created_at']
        
    def get_absolute_url(self, language=None):
        """
        Get the URL for this coloring page in the specified language.
        If no language is specified, use the current language.
        """
        if not language:
            language = get_language()
        
        if language == 'de' and self.seo_url_de:
            return reverse('coloring_pages:detail_de', kwargs={'seo_url': self.seo_url_de})
        # Default to English
        return reverse('coloring_pages:detail_en', kwargs={'seo_url': self.seo_url_en or str(self.id)})
    
    def delete(self, *args, **kwargs):
        """
        Delete the model instance and its associated files.
        """
        # Store the file paths before deletion
        storage, path = self.image.storage, self.image.path
        thumbnail_storage, thumbnail_path = None, None
        if self.thumbnail:
            thumbnail_storage, thumbnail_path = self.thumbnail.storage, self.thumbnail.path
        
        # Call the parent delete method
        super().delete(*args, **kwargs)
        
        # Delete the files after the model is deleted
        try:
            if path and os.path.exists(path):
                os.remove(path)
                # Delete the parent directory if it's empty
                dir_path = os.path.dirname(path)
                if os.path.exists(dir_path) and not os.listdir(dir_path):
                    os.rmdir(dir_path)
        except (ValueError, OSError) as e:
            print(f"Error deleting image file {path}: {e}")
            
        try:
            if thumbnail_path and os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
                # Delete the parent directory if it's empty
                thumbnail_dir = os.path.dirname(thumbnail_path)
                if os.path.exists(thumbnail_dir) and not os.listdir(thumbnail_dir):
                    os.rmdir(thumbnail_dir)
        except (ValueError, OSError) as e:
            print(f"Error deleting thumbnail file {thumbnail_path}: {e}")


class SystemPrompt(models.Model):
    """
    Stores system prompts for different AI model providers and models.
    """
    class Meta:
        verbose_name = _('System Prompt')
        verbose_name_plural = _('System Prompts')
        ordering = ['name', 'model_provider', 'model_name']
        unique_together = [['model_provider', 'model_name']]
    
    name = models.CharField(
        max_length=200,
        verbose_name=_('Name'),
        help_text=_('A descriptive name for this system prompt'),
        default='Unnamed Prompt'  # Default value for existing records
    )
    
    model_provider = models.CharField(
        max_length=100,
        verbose_name=_('Model Provider'),
        help_text=_('The provider of the AI model (e.g., OpenAI, Anthropic, etc.)')
    )
    
    model_name = models.CharField(
        max_length=100,
        verbose_name=_('Model Name'),
        help_text=_('The name of the specific model (e.g., gpt-4, claude-2, etc.)')
    )
    
    prompt = models.TextField(
        verbose_name=_('System Prompt'),
        help_text=_('The system prompt to use with this model')
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    
    def __str__(self):
        return self.name


class SearchQuery(models.Model):
    """
    Tracks search queries and their results for analytics.
    """
    # Search information
    query = models.CharField(max_length=255, db_index=True)
    result_count = models.PositiveIntegerField(default=0)
    session_key = models.CharField(max_length=40, db_index=True, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    language = models.CharField(max_length=10, default='en')
    referrer = models.URLField(max_length=500, blank=True, null=True)
    user_agent = models.CharField(max_length=500, blank=True, null=True)
    referrer_url = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Search Query'
        verbose_name_plural = 'Search Queries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['query', 'created_at']),
            models.Index(fields=['session_key', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
        ]
    
    def __str__(self):
        return f'"{self.query}" - {self.result_count} results ({self.created_at})'
    
    @classmethod
    def create_from_request(cls, request, query, result_count):
        """
        Create a new search query record from a request.
        """
        # Get client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
            
        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]  # Limit length to prevent DB errors
        
        # Get referrer URL
        referrer = request.META.get('HTTP_REFERER', '')[:500]  # Limit length
        
        # Get current language from request or default to 'en'
        language = get_language() or 'en'
        
        # Create and return the search query
        return cls.objects.create(
            query=query,
            result_count=result_count,
            session_key=request.session.session_key or '',
            ip_address=ip or '',
            user_agent=user_agent,
            referrer_url=referrer,
            language=language
        )
    
    @classmethod
    def is_duplicate_search(cls, request, query):
        """
        Check if this search is a duplicate from the same session within a short time window.
        """
        if not request.session.session_key or not query:
            return False
            
        # Check if this exact search was performed recently in the same session and language
        last_search = request.session.get('last_search')
        current_language = get_language() or 'en'
        
        if last_search and last_search.get('query') == query and last_search.get('language') == current_language:
            try:
                last_search_time = timezone.datetime.fromisoformat(last_search.get('timestamp', ''))
                time_since = timezone.now() - last_search_time
                if time_since.total_seconds() < 3600:  # 1 hour window
                    return True
            except (ValueError, TypeError):
                pass
                
        return False
    
    @classmethod
    def get_popular_searches(cls, days=30, limit=10, language=None):
        """
        Get the most popular search queries in the last N days that returned at least 1 result.
        If language is provided, only return searches from that language.
        """
        since = timezone.now() - timezone.timedelta(days=days)
        queryset = cls.objects.filter(
            created_at__gte=since,
            result_count__gt=0  # Only include searches with results
        )
        
        # Filter by language if specified
        if language:
            queryset = queryset.filter(language=language)
            
        return queryset.values('query').annotate(
            search_count=Count('id'),
            avg_results=Avg('result_count'),
            last_searched=Max('created_at')
        ).order_by('-search_count', '-last_searched')[:limit]
    
    def get_country(self):
        """
        Get the country code for the IP address if GeoIP is available.
        """
        if not self.ip_address or not GEOIP_AVAILABLE:
            return None
            
        try:
            return GeoIP2().country_code(self.ip_address)
        except Exception:
            return None
