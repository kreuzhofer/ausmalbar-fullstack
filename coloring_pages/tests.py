from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
import os

class ColoringPageTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a test image
        self.test_image = SimpleUploadedFile(
            name='test_image.png',
            content=open(os.path.join(settings.BASE_DIR, 'static', 'images', 'test-image.png'), 'rb').read(),
            content_type='image/png'
        )
    
    def test_home_page_status_code(self):
        """Test that the home page loads successfully"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
    
    def test_search_page_status_code(self):
        """Test that the search page loads successfully"""
        response = self.client.get(reverse('search') + '?q=test')
        self.assertEqual(response.status_code, 200)
    
    # Add more tests as needed
    
    def tearDown(self):
        # Clean up any files created during tests
        if os.path.exists(self.test_image.name):
            os.remove(self.test_image.name)
