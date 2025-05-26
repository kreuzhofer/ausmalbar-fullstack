from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect, render
from django.contrib import messages
from django.urls import reverse
from django import forms
from django.conf import settings
from django.utils.html import format_html
from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from openai import OpenAI
from .models import ColoringPage
from .forms import ColoringPageForm
from .views import generate_coloring_page, confirm_coloring_page

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
    list_display = ('title', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'description', 'prompt')
    readonly_fields = ('created_at', 'updated_at', 'thumbnail_preview')
    actions = ['delete_selected_with_confirmation']
    
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
        # Change view - show all fields
        return (
            (None, {
                'fields': ('title', 'description', 'prompt')
            }),
            ('Images', {
                'fields': ('image', 'thumbnail_preview', 'thumbnail')
            }),
            ('Metadata', {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',)
            }),
        )
        
    def save_model(self, request, obj, form, change):
        """Generate title and description when creating a new coloring page"""
        if not change:  # Only for new objects
            try:
                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                
                # Generate title and description using GPT-4o-mini
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an AI that helps create SEO-friendly content for coloring pages."},
                        {"role": "user", "content": f"Create a concise title (max 60 chars) and a short description (1-2 sentences) for a coloring page with this prompt: {obj.prompt}"}
                    ],
                    max_tokens=100
                )
                
                # Parse the response to extract title and description
                result = response.choices[0].message.content.strip()
                if ':' in result:
                    title_part, desc_part = result.split(':', 1)
                    title = title_part.replace('Title:', '').strip()
                    description = desc_part.replace('Description:', '').strip()
                else:
                    # Fallback if the format is unexpected
                    title = f"Coloring Page: {obj.prompt[:50]}"
                    description = f"A beautiful coloring page featuring {obj.prompt}."
                
                obj.title = title
                obj.description = description
                
            except Exception as e:
                # Fallback if AI generation fails
                obj.title = f"Coloring Page: {obj.prompt[:50]}"
                obj.description = f"A beautiful coloring page featuring {obj.prompt}."
        
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
        """Remove the default delete action"""
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    def delete_selected_with_confirmation(self, request, queryset):
        """Custom delete action with confirmation"""
        if 'confirm' in request.POST:
            # Delete the selected items
            count = queryset.count()
            queryset.delete()
            self.message_user(request, f'Successfully deleted {count} coloring page(s).')
            return None
        
        # Show confirmation page
        context = {
            'title': 'Are you sure?',
            'objects_name': 'coloring page(s)',
            'queryset': queryset,
            'opts': self.model._meta,
            'action_checkbox_name': ACTION_CHECKBOX_NAME,
        }
        
        return TemplateResponse(
            request,
            self.delete_confirmation_template,
            context
        )
    
    delete_selected_with_confirmation.short_description = 'Delete selected coloring pages'
    
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
