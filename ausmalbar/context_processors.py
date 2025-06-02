from .utils.mixpanel_tracking import tracker

def mixpanel_tracker(request):
    """
    Context processor that adds the Mixpanel tracker to the template context.
    """
    return {
        'mixpanel_tracker': tracker,
    }
