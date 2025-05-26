from django import forms
from .models import ColoringPage

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
        fields = ['title', 'description', 'prompt']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'vTextField',
                'placeholder': 'Enter a title for the coloring page...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'vLargeTextField',
                'rows': 3,
                'placeholder': 'Enter a description for the coloring page...'
            }),
            'prompt': forms.Textarea(attrs={
                'class': 'vLargeTextField',
                'rows': 4,
                'placeholder': 'Describe the image you want to generate...'
            }),
        }
