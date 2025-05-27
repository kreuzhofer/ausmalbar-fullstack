import os
import django

def create_admin():
    # Set up Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ausmalbar.settings')
    django.setup()
    
    from django.contrib.auth import get_user_model
    
    # Get environment variables with defaults
    admin_username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
    admin_email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
    admin_password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin')
    
    User = get_user_model()
    
    # Create admin user if it doesn't exist
    if not User.objects.filter(username=admin_username).exists():
        print(f"Creating superuser {admin_username}")
        User.objects.create_superuser(
            username=admin_username,
            email=admin_email,
            password=admin_password
        )
        print("Superuser created successfully!")
    else:
        print("Superuser already exists.")

if __name__ == "__main__":
    create_admin()
