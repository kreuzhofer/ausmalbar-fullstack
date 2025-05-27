from django.shortcuts import render
from django.utils.translation import get_language
from django.views.generic import TemplateView

class LegalPageView(TemplateView):
    template_name = "coloring_pages/legal.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_type'] = self.page_type
        return context

class PrivacyPolicyView(LegalPageView):
    page_type = 'privacy'

class TermsOfServiceView(LegalPageView):
    page_type = 'terms'
