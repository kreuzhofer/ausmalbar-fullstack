"""
Models for search functionality and analytics.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import TimeStampedModel, geoip, GEOIP_AVAILABLE


class SearchQuery(TimeStampedModel):
    """
    Tracks search queries and their results for analytics.
    """
    query = models.CharField(max_length=255, db_index=True)
    result_count = models.PositiveIntegerField(default=0)
    session_key = models.CharField(max_length=40, db_index=True, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    language = models.CharField(max_length=10, default='en')
    referrer = models.URLField(max_length=500, blank=True, null=True)
    user_agent = models.CharField(max_length=500, blank=True, null=True)
    referrer_url = models.URLField(max_length=500, blank=True, null=True)

    class Meta:
        verbose_name = _('Search Query')
        verbose_name_plural = _('Search Queries')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['query', 'created_at']),
            models.Index(fields=['session_key', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.query} ({self.result_count} results)"
    
    @classmethod
    def create_from_request(cls, request, query, result_count):
        """
        Create a new search query record from a request.
        """
        if not query or not query.strip():
            return None
            
        # Skip if this is a duplicate search from the same session
        if cls.is_duplicate_search(request, query):
            return None
            
        search = cls(
            query=query,
            result_count=result_count,
            session_key=request.session.session_key,
            ip_address=cls._get_client_ip(request),
            language=getattr(request, 'LANGUAGE_CODE', 'en'),
            referrer=request.META.get('HTTP_REFERER'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            referrer_url=request.META.get('HTTP_REFERER')
        )
        search.save()
        return search
    
    @classmethod
    def is_duplicate_search(cls, request, query):
        """
        Check if this search is a duplicate from the same session within a short time window.
        """
        if not request.session.session_key:
            return False
            
        from django.utils import timezone
        from datetime import timedelta
        
        time_threshold = timezone.now() - timedelta(minutes=5)
        
        return cls.objects.filter(
            query__iexact=query,
            session_key=request.session.session_key,
            created_at__gt=time_threshold
        ).exists()
    
    @classmethod
    def get_popular_searches(cls, days=30, limit=10, language=None):
        """
        Get the most popular search queries in the last N days that returned at least 1 result.
        If language is provided, only return searches from that language.
        """
        from django.utils import timezone
        from django.db.models import Count
        
        time_threshold = timezone.now() - timezone.timedelta(days=days)
        
        queryset = cls.objects.filter(
            created_at__gte=time_threshold,
            result_count__gt=0
        )
        
        if language:
            queryset = queryset.filter(language=language)
        
        # Convert the queryset to a list of dictionaries with both query and count
        return list(
            queryset
            .values('query')
            .annotate(count=Count('id'))
            .order_by('-count')
            .values('query', 'count')[:limit]
        )
    
    def get_country(self):
        """
        Get the country code for the IP address if GeoIP is available.
        """
        if not self.ip_address or not GEOIP_AVAILABLE or not geoip:
            return None
            
        try:
            return geoip.country_code(self.ip_address)
        except Exception:
            return None
    
    @staticmethod
    def _get_client_ip(request):
        """Get the client's IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
