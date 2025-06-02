"""
Legal views for the coloring pages application.
"""
from django.views.generic import TemplateView
from django.utils.translation import gettext_lazy as _

class PrivacyPolicyView(TemplateView):
    """
    View for displaying the privacy policy.
    """
    template_name = 'legal/privacy_policy.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('Privacy Policy'),
            'current_year': self.request.site.settings.CURRENT_YEAR,
        })
        return context


class TermsOfServiceView(TemplateView):
    """
    View for displaying the terms of service.
    """
    template_name = 'legal/terms_of_service.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('Terms of Service'),
            'current_year': self.request.site.settings.CURRENT_YEAR,
        })
        return context
