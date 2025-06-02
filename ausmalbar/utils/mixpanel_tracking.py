import logging
from django.conf import settings
from mixpanel import Mixpanel

logger = logging.getLogger(__name__)

class MixpanelTracker:
    def __init__(self, token=None):
        """
        Initialize Mixpanel tracker.
        If no token is provided, it will try to get it from Django settings.
        """
        self.token = token or getattr(settings, 'MIXPANEL_TOKEN', None)
        self.enabled = bool(self.token)
        
        if self.enabled:
            self.mp = Mixpanel(self.token)
            logger.info("Mixpanel tracking initialized with token")
        else:
            logger.warning("Mixpanel tracking is disabled - no token provided")
    
    def track_event(self, distinct_id, event_name, properties=None):
        """
        Track an event in Mixpanel
        
        Args:
            distinct_id: A unique identifier for the user/session
            event_name: Name of the event to track
            properties: Dictionary of additional properties for the event
        """
        if not self.enabled:
            logger.debug(f"Mixpanel tracking disabled - would have tracked: {event_name}")
            return False
            
        try:
            props = properties or {}
            self.mp.track(distinct_id, event_name, props)
            logger.debug(f"Tracked event: {event_name} for user {distinct_id}")
            return True
        except Exception as e:
            logger.error(f"Error tracking Mixpanel event {event_name}: {str(e)}")
            return False
    
    def set_user_properties(self, distinct_id, properties):
        """
        Set properties for a user in Mixpanel
        
        Args:
            distinct_id: A unique identifier for the user
            properties: Dictionary of properties to set for the user
        """
        if not self.enabled:
            return False
            
        try:
            self.mp.people_set(distinct_id, properties)
            logger.debug(f"Set properties for user {distinct_id}")
            return True
        except Exception as e:
            logger.error(f"Error setting Mixpanel user properties: {str(e)}")
            return False

# Create a global instance to be used across the application
tracker = MixpanelTracker()
