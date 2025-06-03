from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from django.shortcuts import redirect
from django.urls import reverse

class SystemPromptAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_provider', 'model_name', 'created_at', 'updated_at')
    list_filter = ('model_provider', 'created_at')
    search_fields = ('name', 'model_provider', 'model_name', 'prompt')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['duplicate_prompt']
    fieldsets = (
        (None, {
            'fields': ('name', 'model_provider', 'model_name', 'quality')
        }),
        ('Prompt', {
            'fields': ('prompt',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    list_display = ('name', 'model_provider', 'model_name', 'quality', 'created_at')
    list_filter = ('quality', 'model_provider', 'created_at')

    def duplicate_prompt(self, request, queryset):
        """
        Action to duplicate selected system prompts with a new name and unique model identifier.
        """
        if queryset.count() != 1:
            self.message_user(
                request,
                _('Please select exactly one prompt to duplicate.'),
                level='error'
            )
            return

        original = queryset.first()
        
        # Create a copy with a new name
        new_prompt = SystemPrompt(
            name=f"{original.name} (Copy)",
            model_provider=original.model_provider,
            model_name=original.model_name,
            prompt=original.prompt,
            quality=original.quality
        )
        new_prompt.save()
        
        self.message_user(
            request,
            _('Successfully duplicated prompt: %s') % new_prompt.name,
            level='success'
        )
        
        # Redirect to the change form for the new prompt
        return redirect(reverse('admin:coloring_pages_systemprompt_change', args=[new_prompt.id]))
    
    duplicate_prompt.short_description = _('Duplicate selected prompt')
