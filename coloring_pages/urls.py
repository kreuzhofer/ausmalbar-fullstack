from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('page/<int:pk>/', views.page_detail, name='page_detail'),
    path('page/<int:pk>/download/', views.download_image, name='download_image'),
    path('admin/generate/', views.generate_coloring_page, name='generate_coloring_page'),
]
