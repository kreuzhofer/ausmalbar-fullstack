from django.conf import settings

def i18n(request):
    """
    Adds language-related context variables to the context.
    """
    return {
        'LANGUAGES': settings.LANGUAGES,
        'CURRENT_LANGUAGE': request.LANGUAGE_CODE,
    }
