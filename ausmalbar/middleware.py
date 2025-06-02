from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from .utils.mixpanel_tracking import tracker
import uuid

class MixpanelTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to track page views in Mixpanel.
    """
    def process_request(self, request):
        # Skip tracking for admin and static files
        if request.path.startswith(('/admin', '/static', '/media')):
            return None
            
        # Get or create a session ID for anonymous users
        if not request.session.get('session_id'):
            request.session['session_id'] = str(uuid.uuid4())
        
        # Get the view name for the current request
        try:
            view_name = resolve(request.path_info).view_name
        except:
            view_name = 'unknown_view'
        
        # Get user identifier (user ID if authenticated, session ID if not)
        distinct_id = str(request.user.id) if request.user.is_authenticated else f"anon_{request.session['session_id']}"
        
        # Track the page view
        tracker.track_event(
            distinct_id=distinct_id,
            event_name='Page View',
            properties={
                'url': request.build_absolute_uri(),
                'path': request.path,
                'view_name': view_name,
                'method': request.method,
                'is_authenticated': request.user.is_authenticated,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'referrer': request.META.get('HTTP_REFERER', ''),
            }
        )
        
        # If user is authenticated, update their profile in Mixpanel
        if request.user.is_authenticated:
            tracker.set_user_properties(
                distinct_id=distinct_id,
                properties={
                    '$name': request.user.get_full_name() or request.user.get_username(),
                    '$email': getattr(request.user, 'email', ''),
                    'last_seen': request.user.last_login.isoformat() if hasattr(request.user, 'last_login') and request.user.last_login else None,
                    'is_staff': request.user.is_staff,
                    'is_superuser': request.user.is_superuser,
                }
            )
        
        return None
