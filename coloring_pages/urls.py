from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from . import views
from . import views_i18n

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('page/<int:pk>/', views.page_detail, name='page_detail'),
    path('page/<int:pk>/download/', views.download_image, name='download_image'),
    path('test-i18n/', views_i18n.test_i18n, name='test_i18n'),
    path('admin/generate/', login_required(views.generate_coloring_page), name='generate_coloring_page'),
    path('admin/confirm/', login_required(views.confirm_coloring_page), name='confirm_coloring_page'),
]
