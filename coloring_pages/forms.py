from django import forms
from .models.coloring_page import ColoringPage

class GenerateColoringPageForm(forms.Form):
    """Form for generating a new coloring page with just the prompt field."""
    prompt = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={
            'class': 'vLargeTextField',
            'rows': 4,
            'placeholder': 'Describe the coloring page you want to generate...',
            'style': 'width: 100%;',
        }),
        required=True,
        help_text='Describe the coloring page you want to generate.'
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
