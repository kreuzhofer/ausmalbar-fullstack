from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from . import views
from .views import ImprintView
from .views_legal import PrivacyPolicyView, TermsOfServiceView

app_name = 'coloring_pages'

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('page/<int:pk>/', views.page_detail, name='page_detail'),
    path('page/<int:pk>/download/', views.download_image, name='download_image'),
    path('admin/generate/', login_required(views.generate_coloring_page), name='generate_coloring_page'),
    path('admin/confirm/', login_required(views.confirm_coloring_page), name='confirm_coloring_page'),
    path('imprint/', ImprintView.as_view(), name='imprint'),
    # Legal pages
    path('privacy-policy/', PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('datenschutzerklaerung/', PrivacyPolicyView.as_view(), name='datenschutz'),
    path('terms-of-service/', TermsOfServiceView.as_view(), name='terms_of_service'),
    path('nutzungsbedingungen/', TermsOfServiceView.as_view(), name='nutzungsbedingungen'),
]
