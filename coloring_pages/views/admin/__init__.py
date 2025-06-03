# This file makes the admin directory a Python package
# Import views here to make them available when importing from coloring_pages.views.admin
from .coloring_page_views import GenerateColoringPageView, ConfirmColoringPageView

generate_coloring_page = GenerateColoringPageView.as_view()
confirm_coloring_page = ConfirmColoringPageView.as_view()
