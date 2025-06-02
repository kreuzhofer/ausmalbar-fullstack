import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env.production first, then fall back to .env
load_dotenv('.env.production')
load_dotenv()  # This will not override variables already set

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-your-secret-key-here')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Read ALLOWED_HOSTS from environment variable, default to localhost for development
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# CSRF and security settings
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False') == 'True'
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False') == 'True'
CSRF_USE_SESSIONS = os.getenv('CSRF_USE_SESSIONS', 'False') == 'True'
CSRF_COOKIE_HTTPONLY = os.getenv('CSRF_COOKIE_HTTPONLY', 'True') == 'True'
CSRF_COOKIE_SAMESITE = os.getenv('CSRF_COOKIE_SAMESITE', 'Lax')
SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True') == 'True'

# Set CSRF_TRUSTED_ORIGINS from environment variable
if os.getenv('CSRF_TRUSTED_ORIGINS'):
    CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS').split(',')

# Set SECURE_PROXY_SSL_HEADER if configured
if os.getenv('SECURE_PROXY_SSL_HEADER'):
    SECURE_PROXY_SSL_HEADER = tuple(os.getenv('SECURE_PROXY_SSL_HEADER').split(','))

# Add all domains from DOMAIN_LANGUAGE_MAPPING to ALLOWED_HOSTS
domain_mapping = os.getenv('DOMAIN_LANGUAGE_MAPPING', '')
for mapping in domain_mapping.split(','):
    if ':' in mapping:
        domain = mapping.split(':', 1)[0].strip()
        # Add both domain and www.domain to ALLOWED_HOSTS
        if domain not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(domain)
        if f'www.{domain}' not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(f'www.{domain}')

# Thumbnail settings
THUMBNAIL_SIZE = (256, 256)
THUMBNAIL_QUALITY = 85  # Good balance between quality and file size
THUMBNAIL_FORMAT = 'WEBP'  # Use WebP for better compression

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'storages',
    'coloring_pages.apps.ColoringPagesConfig',
]

# Debug Toolbar
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']

# Site ID for Django sites framework
SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add WhiteNoise middleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'coloring_pages.middleware.DomainLanguageRedirectMiddleware',  # Domain-based language redirect
]

ROOT_URLCONF = 'ausmalbar.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'coloring_pages.context_processors.i18n',
            ],
        },
    },
]

WSGI_APPLICATION = 'ausmalbar.wsgi.application'

# Database
DB_ENGINE = os.getenv('DB_ENGINE', 'django.db.backends.sqlite3')
DB_NAME = os.getenv('DB_NAME', BASE_DIR / 'db.sqlite3')
DB_USER = os.getenv('DB_USER', '')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', '')
DB_PORT = os.getenv('DB_PORT', '')

if 'postgresql' in DB_ENGINE.lower():
    # Ensure we're using the full module path for PostgreSQL
    engine = 'django.db.backends.postgresql' if 'postgresql' in DB_ENGINE.lower() else DB_ENGINE
    DATABASES = {
        'default': {
            'ENGINE': engine,
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': DB_PORT or '5432',
            'OPTIONS': {
                'connect_timeout': 5,  # 5 seconds timeout
            },
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': str(BASE_DIR / 'db.sqlite3'),
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Available languages
LANGUAGES = [
    ('en', 'English'),
    ('de', 'Deutsch'),
]

# Domain to language mapping
# Format: "domain1.com:lang1,domain2.com:lang2"
# For example: "yourdomain.de:de,yourdomain.com:en"
DOMAIN_LANGUAGE_MAPPING = os.getenv('DOMAIN_LANGUAGE_MAPPING', 'yourdomain.de:de,yourdomain.com:en')

# Imprint settings
IMPRINT_NAME = os.getenv('IMPRINT_NAME', 'Your Name or Company')
IMPRINT_STREET = os.getenv('IMPRINT_STREET', 'Street Address')
IMPRINT_CITY = os.getenv('IMPRINT_CITY', 'Postal Code City')
IMPRINT_COUNTRY = os.getenv('IMPRINT_COUNTRY', 'Country')
IMPRINT_EMAIL = os.getenv('IMPRINT_EMAIL', 'info@example.com')
IMPRINT_PHONE = os.getenv('IMPRINT_PHONE', '+49 123 456789')

# Path where Django looks for translation files
LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# WhiteNoise configuration for static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
AWS_DEFAULT_ACL = 'public-read'
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = False

# Use S3 for storage when AWS credentials are provided
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and AWS_STORAGE_BUCKET_NAME:
    DEFAULT_FILE_STORAGE = 'coloring_pages.storage_backends.MediaStorage'
    STATICFILES_STORAGE = 'coloring_pages.storage_backends.StaticStorage'

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Thumbnail settings
THUMBNAIL_SIZE = (300, 300)

# Login URL for admin
LOGIN_URL = '/admin/login/'

# Email settings (for error reporting)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # For development
DEFAULT_FROM_EMAIL = 'noreply@ausmalbar.com'

# Mixpanel settings
MIXPANEL_TOKEN = os.getenv('MIXPANEL_TOKEN')
