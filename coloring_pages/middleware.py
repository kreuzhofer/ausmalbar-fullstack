from django.http import HttpResponse, Http404
from django.conf import settings
import os

class RobotsTxtMiddleware:
    """
    Middleware to serve robots.txt from static files.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.robots_txt_path = os.path.join(settings.STATIC_ROOT, 'robots.txt')
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.robots_txt_path), exist_ok=True)
        
        # Create a default robots.txt if it doesn't exist
        if not os.path.exists(self.robots_txt_path):
            with open(self.robots_txt_path, 'w') as f:
                f.write("""# robots.txt for Ausmalbar\n"""
                       """User-agent: *\n"""
                       """Allow: /\n"""
                       """Disallow: /admin/\n""")

    def __call__(self, request):
        if request.path == '/robots.txt':
            try:
                with open(self.robots_txt_path, 'r') as f:
                    content = f.read()
                return HttpResponse(content, content_type='text/plain')
            except IOError:
                raise Http404('robots.txt not found')
        return self.get_response(request)
