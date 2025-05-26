# Ausmalbar - AI-Powered Coloring Pages

A Django-based web application for generating, managing, and searching AI-created coloring pages using OpenAI's GPT-Image-1 model

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip
- OpenAI API key (for image generation)
- (Optional) AWS account for S3 storage

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ausmalbar.git
   cd ausmalbar
   ```

2. **Set up the environment**
   ```bash
   # Make the setup script executable
   chmod +x setup.sh
   
   # Run the setup script
   ./setup.sh
   ```

   This will:
   - Create a Python virtual environment
   - Install all dependencies
   - Create a `.env` file with default settings
   - Run database migrations
   - Create a superuser (admin/admin)

3. **Configure your environment**
   - Edit the `.env` file and add your OpenAI API key
   - (Optional) Add AWS credentials if using S3 for storage

4. **Start the development server**
   ```bash
   source venv/bin/activate  # Activate virtual environment
   python manage.py runserver
   ```

5. **Access the application**
   - Website: http://127.0.0.1:8000/
   - Admin: http://127.0.0.1:8000/admin/ (admin/admin)

## ⚙️ Configuration

### Environment Variables

Edit the `.env` file to configure the application:

```env
# Django
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True

# Database
DB_NAME=db.sqlite3

# AWS S3 (optional)
# AWS_ACCESS_KEY_ID=your_access_key
# AWS_SECRET_ACCESS_KEY=your_secret_key
# AWS_STORAGE_BUCKET_NAME=your_bucket_name
# AWS_S3_REGION_NAME=your_region

# OpenAI API Key (required for generating images)
OPENAI_API_KEY=your_openai_api_key

# Admin user (created during setup)
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=admin
```

## 🎨 Using the Application

### For Admins

1. **Generate New Coloring Pages**
   - Log in to the admin panel
   - Click "Generate New Coloring Page"
   - Enter a title, description, and detailed prompt (e.g., "A cute teddy bear having a picnic")
   - Click "Generate" and wait for the AI to create your coloring page

2. **Manage Content**
   - View all coloring pages in the admin panel
   - Edit or delete existing pages
   - Monitor usage and activity

### For Users

1. **Browse Coloring Pages**
   - View the latest coloring pages on the homepage
   - Click on any image to see details

2. **Search**
   - Use the search bar to find specific coloring pages
   - Results are paginated for easy browsing

3. **Download**
   - Click the "Download" button on any coloring page
   - Or right-click and "Save image as..."

## 🚀 Deployment

### Production Setup

1. **Web Server**
   - Use Nginx as a reverse proxy
   - Configure Gunicorn as the application server

2. **Database**
   - For production, use PostgreSQL instead of SQLite
   - Configure database connection in settings.py

3. **Static Files**
   - Use WhiteNoise for serving static files
   - Or configure your web server to serve them directly

4. **Media Files**
   - For production, use S3 or another cloud storage solution
   - Update the storage settings in settings.py

### Docker Deployment

A `Dockerfile` and `docker-compose.yml` are provided for containerized deployment:

```bash
# Build and start containers
docker-compose up --build -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

## 🛠 Development

### Running Tests

```bash
python manage.py test
```

### Code Style

This project uses:
- Black for code formatting
- Flake8 for linting
- isort for import sorting

```bash
# Install development dependencies
pip install black flake8 isort

# Format code
black .

# Lint code
flake8
# Sort imports
isort .
```

## 🤝 Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Django and Bootstrap 5
- Powered by OpenAI's DALL-E for image generation
- Icons from Font Awesome
