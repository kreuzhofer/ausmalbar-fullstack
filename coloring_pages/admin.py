from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models.coloring_page import ColoringPage
from .models.search import SearchQuery
from .models.system_prompt import SystemPrompt
from .views.admin.coloring_page import ColoringPageAdmin
from .views.admin.search import SearchQueryAdmin
from .views.admin.system_prompt import SystemPromptAdmin

# Register models with their respective admin classes
admin.site.register(ColoringPage, ColoringPageAdmin)
admin.site.register(SearchQuery, SearchQueryAdmin)
admin.site.register(SystemPrompt, SystemPromptAdmin)

# Admin site configuration
admin.site.site_header = 'Ausmalbar Administration'
admin.site.site_title = 'Ausmalbar Admin'
admin.site.index_title = 'Dashboard'
