import os
import sys
import django
from django.utils import translation

# Add the project root to Python path for test discovery
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ausmalbar.test_settings')
django.setup()

from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from ausmalbar import settings as project_settings

class ColoringPageTests(TestCase):
    def setUp(self):
        # Create a test client
        self.client = Client()
        
        # Create a test image
        self.test_image = SimpleUploadedFile(
            name='test_image.png',
            content=open(os.path.join(settings.BASE_DIR, 'static', 'images', 'test-image.png'), 'rb').read(),
            content_type='image/png'
        )
        
        # Set default language to English
        self.client.cookies['django_language'] = 'en'
        translation.activate('en')
    
    def test_home_page_status_code(self):
        """Test that the home page loads successfully in English"""
        response = self.client.get('/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'coloring_pages/home.html')
        self.assertTemplateUsed(response, 'coloring_pages/base.html')
        self.assertTemplateUsed(response, 'app.html')
        self.assertTemplateUsed(response, 'coloring_pages/includes/coloring_page_card.html')

    def test_home_page_status_code_de(self):
        """Test that the home page loads successfully in German"""
        # Switch to German language
        self.client.cookies['django_language'] = 'de'
        translation.activate('de')
        response = self.client.get('/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'coloring_pages/home.html')
        self.assertTemplateUsed(response, 'coloring_pages/base.html')
        self.assertTemplateUsed(response, 'app.html')
        self.assertTemplateUsed(response, 'coloring_pages/includes/coloring_page_card.html')
        
        # Switch back to English for other tests
        self.client.cookies['django_language'] = 'en'
        translation.activate('en')
    
    def test_search_page_status_code(self):
        """Test that the search page loads successfully in English"""
        response = self.client.get('/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'coloring_pages/home.html')
        self.assertTemplateUsed(response, 'coloring_pages/base.html')
        self.assertTemplateUsed(response, 'app.html')
        self.assertTemplateUsed(response, 'coloring_pages/includes/coloring_page_card.html')

    def test_search_page_status_code_de(self):
        """Test that the search page loads successfully in German"""
        # Switch to German language
        self.client.cookies['django_language'] = 'de'
        translation.activate('de')
        response = self.client.get('/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'coloring_pages/home.html')
        
        # Switch back to English for other tests
        self.client.cookies['django_language'] = 'en'
        translation.activate('en')

    def test_imprint_page_status_code(self):
        """Test that the imprint page loads successfully in English"""
        response = self.client.get('/imprint/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'imprint.html')
        self.assertTemplateUsed(response, 'app.html')

    def test_imprint_page_status_code_de(self):
        """Test that the imprint page loads successfully in German"""
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

    def test_privacy_policy_page_status_code(self):
        """Test that the privacy policy page loads successfully in English"""
        response = self.client.get('/privacy-policy/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'coloring_pages/legal.html')
        self.assertTemplateUsed(response, 'coloring_pages/base.html')
        self.assertTemplateUsed(response, 'app.html')

    def test_privacy_policy_page_status_code_de(self):
        """Test that the privacy policy page loads successfully in German"""
        # Switch to German language
        self.client.cookies['django_language'] = 'de'
        translation.activate('de')
        response = self.client.get('/datenschutzerklaerung/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'coloring_pages/legal.html')
        self.assertTemplateUsed(response, 'coloring_pages/base.html')
        self.assertTemplateUsed(response, 'app.html')
        
        # Switch back to English for other tests
        self.client.cookies['django_language'] = 'en'
        translation.activate('en')

    def test_terms_of_service_page_status_code(self):
        """Test that the terms of service page loads successfully in English"""
        response = self.client.get('/terms-of-service/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'coloring_pages/legal.html')
        self.assertTemplateUsed(response, 'coloring_pages/base.html')
        self.assertTemplateUsed(response, 'app.html')

    def test_terms_of_service_page_status_code_de(self):
        """Test that the terms of service page loads successfully in German"""
        # Switch to German language
        self.client.cookies['django_language'] = 'de'
        translation.activate('de')
        response = self.client.get('/nutzungsbedingungen/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'coloring_pages/legal.html')
        self.assertTemplateUsed(response, 'coloring_pages/base.html')
        self.assertTemplateUsed(response, 'app.html')
        
        # Switch back to English for other tests
        self.client.cookies['django_language'] = 'en'
        translation.activate('en')

    def test_robots_txt_status_code(self):
        """Test that the robots.txt file is accessible"""
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')

    def test_sitemap_xml_status_code(self):
        """Test that the sitemap.xml file is accessible"""
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')

    def test_ads_txt_status_code(self):
        """Test that the ads.txt file is accessible"""
        response = self.client.get('/ads.txt')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
    
    def tearDown(self):
        # Clean up any files created during tests
        if os.path.exists(self.test_image.name):
            os.remove(self.test_image.name)
