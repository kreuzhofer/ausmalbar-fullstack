from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.conf import settings

# Import views
from coloring_pages.views.home import home
from coloring_pages.views.search import search
from coloring_pages.views.views_class_based import ImprintView

urlpatterns = [
    path('', include('coloring_pages.urls')),
]

# Internationalized URL patterns
urlpatterns += i18n_patterns(
    path('', home, name='home'),
    path('search/', search, name='search'),
    path('imprint/', ImprintView.as_view(), name='imprint'),
    path('impressum/', ImprintView.as_view(), name='impressum'),
    prefix_default_language=True
)
