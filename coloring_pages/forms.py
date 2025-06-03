from django import forms
from django.utils.translation import gettext_lazy as _
from .models.coloring_page import ColoringPage
from .models.system_prompt import SystemPrompt

class GenerateColoringPageForm(forms.Form):
    """Form for generating a new coloring page with prompt and system prompt selection."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['system_prompt'] = forms.ModelChoiceField(
            queryset=SystemPrompt.objects.all().order_by('name'),
            label=_('System Prompt'),
            required=True,
            help_text=_('Select a system prompt to use for image generation')
        )
        self.fields['prompt'] = forms.CharField(
            label=_('Prompt'),
            widget=forms.Textarea(attrs={
                'class': 'vLargeTextField',
                'rows': 4,
                'placeholder': _('Describe the coloring page you want to generate...'),
                'style': 'width: 100%;',
            }),
            required=True,
            help_text=_('Describe the coloring page you want to generate.')
        )

class ColoringPageForm(forms.ModelForm):
    class Meta:
        model = ColoringPage
        fields = ['title_en', 'title_de', 'description_en', 'description_de', 'prompt']
        widgets = {
            'title_en': forms.TextInput(attrs={
                'class': 'vTextField',
                'placeholder': 'Enter an English title for the coloring page...'
            }),
            'title_de': forms.TextInput(attrs={
                'class': 'vTextField',
                'placeholder': 'Geben Sie einen deutschen Titel für die Malvorlage ein...'
            }),
            'description_en': forms.Textarea(attrs={
                'class': 'vLargeTextField',
                'rows': 3,
                'placeholder': 'Enter an English description for the coloring page...'
            }),
            'description_de': forms.Textarea(attrs={
                'class': 'vLargeTextField',
                'rows': 3,
                'placeholder': 'Geben Sie eine deutsche Beschreibung für die Malvorlage ein...'
            }),
            'prompt': forms.Textarea(attrs={
                'class': 'vLargeTextField',
                'rows': 3,
                'placeholder': 'The original prompt used to generate this page...',
                'readonly': 'readonly'
            }),
        }
