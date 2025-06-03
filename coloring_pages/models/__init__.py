"""
This package contains all models for the coloring_pages app.

To import models, use: `from coloring_pages.models import ModelName`
"""

# Import models from their respective modules
from .coloring_page import ColoringPage
from .system_prompt import SystemPrompt
from .search import SearchQuery

# This makes the models available when importing from coloring_pages.models
__all__ = [
    'ColoringPage',
    'SystemPrompt',
    'SearchQuery',
]
