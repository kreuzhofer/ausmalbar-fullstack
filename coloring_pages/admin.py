from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import redirect, render
from django.urls import reverse
from django import forms
from django.conf import settings
from django.utils.html import format_html
from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from openai import OpenAI
from .models.coloring_page import ColoringPage
from .models.search import SearchQuery
from .models.system_prompt import SystemPrompt
from .forms import ColoringPageForm
from .views.admin import generate_coloring_page, confirm_coloring_page
from .utils import generate_coloring_page_image

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

@admin.register(ColoringPage)
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
                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                
                # Generate titles and descriptions in both languages
                from .utils import generate_titles_and_descriptions
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
                from .utils import generate_coloring_page_image
                
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
        
        # Remove all delete actions first
        delete_actions = [name for name in actions.keys() if 'delete' in name.lower()]
        for action in delete_actions:
            del actions[action]
            
        # Add our custom delete action
        actions['delete_selected'] = (
            self.delete_selected_with_files,
            'delete_selected',
            'Delete selected %(verbose_name_plural)s'
        )
        
        return actions
    
    def delete_selected_with_files(self, modeladmin, request, queryset):
        """Custom action to delete selected objects and their associated files"""
        # First delete the files
        for obj in queryset:
            # Delete the image file if it exists
            if obj.image:
                try:
                    storage, path = obj.image.storage, obj.image.path
                    storage.delete(path)
                except Exception as e:
                    self.message_user(request, f"Error deleting image for {obj}: {str(e)}", level='error')
            
            # Delete the thumbnail if it exists
            if obj.thumbnail:
                try:
                    storage, path = obj.thumbnail.storage, obj.thumbnail.path
                    storage.delete(path)
                except Exception as e:
                    self.message_user(request, f"Error deleting thumbnail for {obj}: {str(e)}", level='error')
        
        # Then delete the database records
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'Successfully deleted {count} coloring page(s).', messages.SUCCESS)
    
    delete_selected_with_files.short_description = 'Delete selected coloring pages and their files'
    
    def delete_view(self, request, object_id, extra_context=None):
        """Override delete view to add confirmation"""
        if request.method == 'POST' and 'confirm' in request.POST:
            return super().delete_view(request, object_id, extra_context)
        
        # Show confirmation page
        obj = self.get_object(request, object_id)
        context = {
            'title': 'Are you sure?',
            'object': obj,
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
            **(extra_context or {}),
        }
        
        return TemplateResponse(
            request,
            'admin/coloring_pages/coloringpage/delete_confirmation_single.html',
            context
        )

# Add a link to the generate page in the admin index
admin.site.site_header = 'Ausmalbar Administration'
admin.site.site_title = 'Ausmalbar Admin'
admin.site.index_title = 'Dashboard'

@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ('query', 'language', 'result_count', 'created_at', 'ip_address')
    list_filter = ('language', 'created_at')
    search_fields = ('query', 'ip_address', 'session_key')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    list_per_page = 20

from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _

@admin.register(SystemPrompt)
class SystemPromptAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_provider', 'model_name', 'created_at', 'updated_at')
    list_filter = ('model_provider', 'created_at')
    search_fields = ('name', 'model_provider', 'model_name', 'prompt')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['duplicate_prompt']
    fieldsets = (
        (None, {
            'fields': ('name', 'model_provider', 'model_name')
        }),
        ('Prompt', {
            'fields': ('prompt',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def duplicate_prompt(self, request, queryset):
        """
        Action to duplicate selected system prompts with a new name and unique model identifier.
        """
        if queryset.count() != 1:
            self.message_user(
                request,
                _('Please select exactly one prompt to duplicate.'),
                messages.ERROR
            )
            return

        original = queryset.first()
        
        # Create a copy with a new name
        new_name = f"{original.name} (Copy)"
        counter = 1
        while SystemPrompt.objects.filter(name=new_name).exists():
            counter += 1
            new_name = f"{original.name} (Copy {counter})"
        
        # Create a unique model name by appending a suffix
        base_model_name = original.model_name
        new_model_name = f"{base_model_name}-copy"
        counter = 1
        while SystemPrompt.objects.filter(
            model_provider=original.model_provider,
            model_name=new_model_name
        ).exists():
            counter += 1
            new_model_name = f"{base_model_name}-copy-{counter}"
        
        try:
            new_prompt = SystemPrompt.objects.create(
                name=new_name,
                model_provider=original.model_provider,
                model_name=new_model_name,
                prompt=original.prompt
            )
            
            self.message_user(
                request,
                _('Successfully duplicated "{original}" as "{new}" with model name "{model}".').format(
                    original=original.name,
                    new=new_prompt.name,
                    model=new_model_name
                ),
                messages.SUCCESS
            )
        except Exception as e:
            self.message_user(
                request,
                _('Error duplicating prompt: {error}').format(error=str(e)),
                messages.ERROR
            )
    
    duplicate_prompt.short_description = _('Duplicate selected prompt')
