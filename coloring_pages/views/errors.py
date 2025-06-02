"""
Error handlers for the coloring pages application.
"""
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _


def page_not_found(request, exception=None, template_name='404.html'):
    """
    Custom 404 error handler.
    """
    context = {
        'title': _('Page Not Found'),
        'error_code': 404,
        'error_message': _('The page you are looking for does not exist.'),
    }
    return render(request, template_name, context, status=404)


def server_error(request, template_name='500.html'):
    """
    Custom 500 error handler.
    """
    context = {
        'title': _('Server Error'),
        'error_code': 500,
        'error_message': _('An error occurred while processing your request.'),
    }
    return render(request, template_name, context, status=500)
