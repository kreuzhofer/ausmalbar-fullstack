"""
Models related to coloring pages.
"""
import os
import io
from django.db import models
from django.conf import settings
from django.core.files.base import ContentFile
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import get_language, gettext_lazy as _
from PIL import Image

from .base import TimeStampedModel, create_unique_slug


class ColoringPage(TimeStampedModel):
    """
    Represents a coloring page with multilingual content.
    """
    # English fields
    title_en = models.CharField(max_length=200, verbose_name=_('Title (English)'))
    description_en = models.TextField(verbose_name=_('Description (English)'))
    
    # German fields
    title_de = models.CharField(max_length=200, verbose_name=_('Title (German)'))
    description_de = models.TextField(verbose_name=_('Description (German)'))
    
    # Common fields
    prompt = models.TextField()
    image = models.ImageField(upload_to='coloring_pages/')
    thumbnail = models.ImageField(upload_to='coloring_pages/thumbnails/', blank=True)
    seo_url_en = models.SlugField(max_length=255, unique=True, blank=True, null=True, 
                                 verbose_name=_('SEO URL (English)'))
    seo_url_de = models.SlugField(max_length=255, unique=True, blank=True, null=True, 
                                 verbose_name=_('SEO URL (German)'))
    
    # Metadata for additional data like system prompt information
    metadata = models.JSONField(blank=True, null=True, default=dict,
                              help_text=_('Additional metadata stored as JSON'))

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
        
        # Process image and generate thumbnail if this is a new image or the image has changed
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
