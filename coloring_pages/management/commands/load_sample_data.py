import os
from django.core.management.base import BaseCommand
from django.core.files import File
from coloring_pages.models import ColoringPage
from django.conf import settings

class Command(BaseCommand):
    help = 'Load sample coloring pages for development and testing'

    def handle(self, *args, **options):
        # Clear existing data
        ColoringPage.objects.all().delete()
        
        # Sample data
        samples = [
            {
                'title': 'Cute Teddy Bear',
                'description': 'An adorable teddy bear with a big bow tie',
                'prompt': 'A cute teddy bear with a big bow tie, black and white line art, coloring page, simple lines, high contrast',
                'image': 'sample_teddy.png'
            },
            {
                'title': 'Magical Unicorn',
                'description': 'A majestic unicorn with flowing mane and tail',
                'prompt': 'A beautiful unicorn with flowing mane and tail, black and white line art, coloring page, fantasy style',
                'image': 'sample_unicorn.png'
            },
            {
                'title': 'Space Rocket',
                'description': 'A rocket blasting off into space',
                'prompt': 'A detailed space rocket taking off, black and white line art, coloring page, space theme',
                'image': 'sample_rocket.png'
            },
        ]
        
        # Create sample coloring pages
        for sample in samples:
            # Use our test image as a placeholder
            image_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'test-image.png')
            
            with open(image_path, 'rb') as f:
                coloring_page = ColoringPage(
                    title=sample['title'],
                    description=sample['description'],
                    prompt=sample['prompt']
                )
                coloring_page.image.save(
                    sample['image'],
                    File(f),
                    save=False
                )
                coloring_page.save()
                
                self.stdout.write(self.style.SUCCESS(f'Created sample: {sample["title"]}'))
        
        self.stdout.write(self.style.SUCCESS('Successfully loaded sample data!'))
