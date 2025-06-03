from django.contrib import admin

class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ('query', 'language', 'result_count', 'created_at', 'ip_address')
    list_filter = ('language', 'created_at')
    search_fields = ('query', 'ip_address', 'session_key')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    list_per_page = 20
