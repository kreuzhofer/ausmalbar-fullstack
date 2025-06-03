from django import forms
from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from django.utils.html import format_html
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _

from ...models.coloring_page import ColoringPage
from ...forms import ColoringPageForm
from . import generate_coloring_page, confirm_coloring_page
from ...utils import generate_coloring_page_image, generate_titles_and_descriptions

class ColoringPageAddForm(forms.ModelForm):
    class Meta:
        model = ColoringPage
        fields = ('prompt',)  # Only show prompt field for new pages
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['prompt'].widget.attrs.update({
            'placeholder': 'Describe the coloring page you want to create...',
            'class': 'vLargeTextField'
        })

class ColoringPageAdmin(admin.ModelAdmin):
    list_display = ('title_en', 'title_de', 'seo_url_en_column', 'seo_url_de_column', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title_en', 'title_de', 'description_en', 'description_de', 'prompt')
    readonly_fields = ('created_at', 'updated_at', 'thumbnail_preview', 'seo_url_en', 'seo_url_de')
    fieldsets = (
        ('English Content', {
            'fields': ('title_en', 'description_en')
        }),
        ('German Content', {
            'fields': ('title_de', 'description_de'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('prompt', 'image', 'thumbnail', 'seo_url_en', 'seo_url_de', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['delete_selected_with_confirmation']
    
    # Add methods to display clickable SEO URLs in the admin list
    def seo_url_en_column(self, obj):
        if obj.seo_url_en:
            url = reverse('coloring_pages:detail_en', kwargs={'seo_url': obj.seo_url_en})
            return format_html('<a href="{}" target="_blank">{}</a>', url, obj.seo_url_en)
        return ""
    seo_url_en_column.short_description = 'SEO URL (EN)'
    seo_url_en_column.admin_order_field = 'seo_url_en'
    
    def seo_url_de_column(self, obj):
        if obj.seo_url_de:
            url = reverse('coloring_pages:detail_de', kwargs={'seo_url': obj.seo_url_de})
            return format_html('<a href="{}" target="_blank">{}</a>', url, obj.seo_url_de)
        return ""
    seo_url_de_column.short_description = 'SEO URL (DE)'
    seo_url_de_column.admin_order_field = 'seo_url_de'
    
    # Use different forms for add and change views
    add_form = ColoringPageAddForm
    form = ColoringPageForm
    
    # Add confirmation template
    delete_confirmation_template = 'admin/coloring_pages/coloringpage/delete_confirmation.html'
    
    def get_form(self, request, obj=None, **kwargs):
        """Use special form during creation"""
        defaults = {}
        if obj is None:
            defaults['form'] = self.add_form
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)
    
    def get_fieldsets(self, request, obj=None):
        if obj is None:
            # Add view - only show prompt field
            return (
                (None, {
                    'fields': ('prompt',)
                }),
            )
        # Change view - use fieldsets defined in the class
        return self.fieldsets
        
    def save_model(self, request, obj, form, change):
        """Generate title and description when creating a new coloring page"""
        if not change:  # Only for new objects
            # First, generate titles and descriptions
            try:
                from openai import OpenAI
                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                
                # Generate titles and descriptions in both languages
                title_en, title_de, description_en, description_de = generate_titles_and_descriptions(obj.prompt)
                
                # Set the generated content
                obj.title_en = title_en[:100]  # Ensure max length
                obj.title_de = title_de[:100] if title_de else title_en
                obj.description_en = description_en or f"A coloring page of {obj.prompt[:90]}{'...' if len(obj.prompt) > 90 else ''}"
                obj.description_de = description_de or f"Eine Malvorlage von {obj.prompt[:90]}{'...' if len(obj.prompt) > 90 else ''}"
                
            except Exception as e:
                # Fallback if AI generation fails
                obj.title_en = f"Coloring Page: {obj.prompt[:50]}"
                obj.title_de = f"Ausmalbild: {obj.prompt[:50]}"
                obj.description_en = f"A beautiful coloring page featuring {obj.prompt}."
                obj.description_de = f"Eine schöne Malvorlage mit {obj.prompt}."
                messages.warning(request, _('Generated default content due to AI service error.'))
            
            # Save the object first to get an ID
            super().save_model(request, obj, form, change)
            
            # Then generate and save the image
            try:
                # Generate the image and thumbnail using our utility function
                try:
                    # Generate the image and thumbnail
                    result = generate_coloring_page_image(obj.prompt)
                    
                    # Save the main image
                    img_name = f"coloring_page_{obj.id}.png"
                    obj.image.save(img_name, ContentFile(result['image_bytes']), save=True)
                    
                    # Save the thumbnail if it was generated
                    if result['thumbnail_bytes']:
                        thumb_name = f"thumb_{obj.id}.png"
                        obj.thumbnail.save(thumb_name, ContentFile(result['thumbnail_bytes']), save=False)
                        
                    # Save the model again to ensure everything is updated
                    obj.save()
                    
                    messages.success(request, _('Coloring page was generated successfully.'))
                    return
                    
                except Exception as e:
                    # Clean up will be handled by the generate_coloring_page_image function
                    messages.error(request, _('Error generating image: %s') % str(e))
                    return
                
            except Exception as e:
                messages.error(request, _('Error generating coloring page image: %s') % str(e))
                # Continue with saving even if image generation fails
                return
        
        super().save_model(request, obj, form, change)
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<div style="width: 150px; height: 150px; display: flex; align-items: center; justify-content: center; '
                'background: #f8f8f8; border: 1px solid #eee; border-radius: 4px; overflow: hidden;">'
                '<img src="{}" style="max-width: 100%; max-height: 100%; width: auto; height: auto; object-fit: contain;" />'
                '</div>',
                obj.thumbnail.url
            )
        return "No thumbnail available"
    thumbnail_preview.short_description = 'Thumbnail Preview'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'generate/',
                self.admin_site.admin_view(generate_coloring_page),
                name='coloring_pages_coloringpage_generate',
            ),
            path(
                'confirm/',
                self.admin_site.admin_view(confirm_coloring_page),
                name='confirm_coloring_page',
            ),
        ]
        return custom_urls + urls
    
    def response_add(self, request, obj, post_url_continue=None):
        """Redirect to the change list view after adding a new object."""
        response = super().response_add(request, obj, post_url_continue)
        if '_addanother' in request.POST:
            return response
        return redirect('admin:coloring_pages_coloringpage_changelist')
        
    def add_view(self, request, form_url='', extra_context=None):
        # Redirect to our custom view for adding new coloring pages
        return redirect('admin:coloring_pages_coloringpage_generate')
    
    def get_actions(self, request):
        """Configure available actions"""
        actions = super().get_actions(request)
        # Add custom actions here if needed
        return actions

# This will be registered in the main admin.py file
