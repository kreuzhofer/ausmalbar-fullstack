from .settings import *

# Add testserver to ALLOWED_HOSTS
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']

# Disable CSRF checks for testing
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Use in-memory SQLite for testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Disable caching for testing
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Disable email sending for testing
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
