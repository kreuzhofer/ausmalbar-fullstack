import os
import sys
import django
from django.utils import translation

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Configure Django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'coloring_pages.tests.frontend.test_settings'
django.setup()

# Import project settings
from ausmalbar import settings as project_settings

from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings


class FrontendUrlAccessibilityTests(TestCase):
    """Test accessibility of frontend URLs in both English and German."""
    
    def setUp(self):
        # Create a test client
        self.client = Client()
        
        # Set default language to English
        self.client.cookies['django_language'] = 'en'
        translation.activate('en')
    
    def test_home_page_accessibility(self):
        """Test that the home page is accessible in English."""
        response = self.client.get('/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'coloring_pages/home.html')
        self.assertTemplateUsed(response, 'coloring_pages/base.html')
        self.assertTemplateUsed(response, 'app.html')

    def test_home_page_accessibility_de(self):
        """Test that the home page is accessible in German."""
        # Switch to German language
        self.client.cookies['django_language'] = 'de'
        translation.activate('de')
        response = self.client.get('/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'coloring_pages/home.html')
        self.assertTemplateUsed(response, 'coloring_pages/base.html')
        self.assertTemplateUsed(response, 'app.html')
        
        # Switch back to English for other tests
        self.client.cookies['django_language'] = 'en'
        translation.activate('en')
    
    def test_search_page_accessibility(self):
        """Test that the search page is accessible in English."""
        response = self.client.get('/search/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'coloring_pages/search.html')
        self.assertTemplateUsed(response, 'coloring_pages/base.html')
        self.assertTemplateUsed(response, 'app.html')

    def test_search_page_accessibility_de(self):
        """Test that the search page is accessible in German."""
        # Switch to German language
        self.client.cookies['django_language'] = 'de'
        translation.activate('de')
        response = self.client.get('/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'coloring_pages/home.html')
        
        # Switch back to English for other tests
        self.client.cookies['django_language'] = 'en'
        translation.activate('en')
    
    def test_imprint_page_accessibility(self):
        """Test that the imprint page is accessible in English."""
        response = self.client.get('/imprint/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'imprint.html')
        self.assertTemplateUsed(response, 'app.html')

    def test_imprint_page_accessibility_de(self):
        """Test that the imprint page is accessible in German."""
        # Switch to German language
        self.client.cookies['django_language'] = 'de'
        translation.activate('de')
        response = self.client.get('/impressum/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'imprint.html')
        self.assertTemplateUsed(response, 'app.html')
        
        # Switch back to English for other tests
        self.client.cookies['django_language'] = 'en'
        translation.activate('en')
