from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

def test_i18n(request):
    """A test view to demonstrate internationalization."""
    context = {
        'welcome_message': _('Welcome to Ausmalbar!'),
        'description': _('This is a test page to demonstrate internationalization.'),
    }
    return render(request, 'coloring_pages/test_i18n.html', context)
