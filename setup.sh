#!/bin/bash

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "# Django" > .env
    echo "DJANGO_SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')" >> .env
    echo "DJANGO_DEBUG=True" >> .env
    echo "" >> .env
    echo "# Database" >> .env
    echo "DB_NAME=db.sqlite3" >> .env
    echo "" >> .env
    echo "# AWS S3 (optional, uncomment and set values as needed)" >> .env
    echo "# AWS_ACCESS_KEY_ID=your_access_key" >> .env
    echo "# AWS_SECRET_ACCESS_KEY=your_secret_key" >> .env
    echo "# AWS_STORAGE_BUCKET_NAME=your_bucket_name" >> .env
    echo "# AWS_S3_REGION_NAME=your_region" >> .env
    echo "" >> .env
    echo "# OpenAI API Key (required for generating coloring pages)" >> .env
    echo "# OPENAI_API_KEY=your_openai_api_key" >> .env
    echo "" >> .env
    echo "# Superuser (optional, uncomment and set values as needed)" >> .env
    echo "# DJANGO_SUPERUSER_USERNAME=admin" >> .env
    echo "# DJANGO_SUPERUSER_EMAIL=admin@example.com" >> .env
    echo "# DJANGO_SUPERUSER_PASSWORD=admin" >> .env
    
    echo "Created .env file. Please update it with your configuration."
fi

# Run migrations
python manage.py migrate

# Create superuser if it doesn't exist
python manage.py initdb

echo "Setup complete. To start the development server, run:"
echo "source venv/bin/activate && python manage.py runserver"
