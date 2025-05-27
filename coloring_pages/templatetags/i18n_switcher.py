from django import template
from django.conf import settings
from django.utils import translation
from django.urls import translate_url

register = template.Library()

@register.simple_tag(takes_context=True)
def change_lang(context, lang=None, *args, **kwargs):
    """
    Get the URL for the current page in another language.
    Usage: {% change_lang 'en' %}
    """
    path = context.get('request').get_full_path()
    return translate_url(path, lang) or path
