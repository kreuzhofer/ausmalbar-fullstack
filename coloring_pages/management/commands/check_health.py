import os
import sys
import time
import psutil
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection, OperationalError

class Command(BaseCommand):
    help = 'Check the health of the application and its dependencies'

    def handle(self, *args, **options):
        """Check the health of the application and its dependencies."""
        self.stdout.write(self.style.MIGRATE_HEADING('Starting health check...'))
        
        # Check database connection
        self.check_database()
        
        # Check storage
        self.check_storage()
        
        # Check external services
        self.check_external_services()
        
        # Check system resources
        self.check_system_resources()
        
        self.stdout.write(self.style.SUCCESS('✅ Health check completed successfully!'))
    
    def check_database(self):
        """Check if the database is accessible."""
        self.stdout.write('\n🔍 Checking database connection...', ending=' ')
        try:
            connection.ensure_connection()
            self.stdout.write(self.style.SUCCESS('OK'))
            self.stdout.write(f'   Database: {settings.DATABASES["default"]["ENGINE"]}')
        except OperationalError as e:
            self.stdout.write(self.style.ERROR('ERROR'))
            self.stdout.write(self.style.ERROR(f'   Could not connect to database: {e}'))
            sys.exit(1)
    
    def check_storage(self):
        """Check if storage is writable."""
        self.stdout.write('\n💾 Checking storage...')
        
        # Check media directory
        media_path = settings.MEDIA_ROOT
        self.check_directory_writable('Media directory', media_path)
        
        # Check static files directory
        static_path = settings.STATIC_ROOT
        self.check_directory_writable('Static files directory', static_path)
        
        # Check for S3 if configured
        if hasattr(settings, 'AWS_STORAGE_BUCKET_NAME'):
            self.stdout.write('   S3 Storage: Configured')
        else:
            self.stdout.write('   S3 Storage: Not configured')
    
    def check_directory_writable(self, name, path):
        """Check if a directory exists and is writable."""
        self.stdout.write(f'   {name}: {path}', ending=' ')
        if not os.path.exists(path):
            self.stdout.write(self.style.WARNING('(Creating directory)'))
            try:
                os.makedirs(path, exist_ok=True)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'ERROR creating directory: {e}'))
                return
        
        test_file = os.path.join(path, f'test_{int(time.time())}.tmp')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            self.stdout.write(self.style.SUCCESS('(Writable)'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'(Not writable: {e})'))
    
    def check_external_services(self):
        """Check connectivity to external services."""
        self.stdout.write('\n🌐 Checking external services...')
        
        # Check OpenAI API
        if hasattr(settings, 'OPENAI_API_KEY'):
            self.stdout.write('   OpenAI API: Configured')
        else:
            self.stdout.write(self.style.WARNING('   OpenAI API: Not configured'))
        
        # Check internet connectivity
        self.stdout.write('   Internet connectivity: ', ending='')
        try:
            response = requests.get('https://www.google.com', timeout=5)
            response.raise_for_status()
            self.stdout.write(self.style.SUCCESS('OK'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'ERROR: {e}'))
    
    def check_system_resources(self):
        """Check system resources."""
        self.stdout.write('\n💻 System resources:')
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_status = self.get_status_emoji(cpu_percent, 80, 95)
        self.stdout.write(f'   CPU Usage: {cpu_percent:.1f}% {cpu_status}')
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_status = self.get_status_emoji(memory_percent, 80, 95)
        self.stdout.write(
            f'   Memory Usage: {memory_percent:.1f}% ' \
            f'({memory.used / (1024*1024):.1f} MB / {memory.total / (1024*1024):.1f} MB) {memory_status}'
        )
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_status = self.get_status_emoji(disk_percent, 80, 95)
        self.stdout.write(
            f'   Disk Usage: {disk_percent:.1f}% ' \
            f'({disk.used / (1024*1024*1024):.1f} GB / {disk.total / (1024*1024*1024):.1f} GB) {disk_status}'
        )
    
    @staticmethod
    def get_status_emoji(value, warning_threshold, error_threshold):
        """Get status emoji based on threshold values."""
        if value >= error_threshold:
            return '🔴'  # Red for critical
        elif value >= warning_threshold:
            return '🟡'  # Yellow for warning
        else:
            return '🟢'  # Green for good
