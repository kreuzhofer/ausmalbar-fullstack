from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.utils.translation import gettext_lazy as _
from . import views
from .views import ImprintView, ColoringPageDetailView
from .views_legal import PrivacyPolicyView, TermsOfServiceView
from .views.admin import generate_coloring_page, confirm_coloring_page

app_name = 'coloring_pages'

urlpatterns = [
    path('', views.home, name='home'),
    # Search URLs
    path('search/', views.search, name='search'),  # English
    path('suche/', views.search, name='suche'),    # German
    
    # SEO-friendly URLs for coloring pages
    # English version
    path(_('coloring-page') + '/<slug:seo_url>/', 
         ColoringPageDetailView.as_view(), 
         name='detail_en'),
    
    # German version
    path(_('ausmalbild') + '/<slug:seo_url>/', 
         ColoringPageDetailView.as_view(), 
         name='detail_de'),
    
    # Keep the old URL pattern for backward compatibility
    path('page/<int:pk>/', views.page_detail, name='page_detail'),
    path('page/<int:pk>/download/', views.download_image, name='download_image'),
    
    # Admin URLs
    path('admin/generate/', login_required(generate_coloring_page), name='generate_coloring_page'),
    path('admin/confirm/', login_required(confirm_coloring_page), name='confirm_coloring_page'),
    
    # Legal pages - English
    path('imprint/', ImprintView.as_view(), name='imprint'),
    # Legal pages - German
    path('impressum/', ImprintView.as_view(), name='impressum'),
    
    # Privacy policy and terms
    path('privacy-policy/', PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('datenschutzerklaerung/', PrivacyPolicyView.as_view(), name='datenschutz'),
    path('terms-of-service/', TermsOfServiceView.as_view(), name='terms_of_service'),
    path('nutzungsbedingungen/', TermsOfServiceView.as_view(), name='nutzungsbedingungen'),
]
