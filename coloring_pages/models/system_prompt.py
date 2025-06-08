"""
Models for managing system prompts for different AI models.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import TimeStampedModel


class SystemPrompt(TimeStampedModel):
    """
    Stores system prompts for different AI model providers and models.
    """
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
    
    quality = models.CharField(
        max_length=20,
        default='standard',
        verbose_name=_('Quality'),
        help_text=_('Image generation quality setting (e.g., standard, hd)')
    )

    class Meta:
        verbose_name = _('System Prompt')
        verbose_name_plural = _('System Prompts')
        ordering = ['name', 'model_provider', 'model_name']
    
    def __str__(self):
        return self.name
