# Ausmalbar - AI-Powered Coloring Pages

A Django-based web application for generating, managing, and searching AI-created coloring pages using OpenAI's GPT-Image-1 model

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key (for image generation)
- (Optional) AWS account for S3 storage

## 🛠 Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ausmalbar.git
   cd ausmalbar
   ```

2. **Set up environment variables**
   - Copy `.env.example` to `.env`
   - Edit `.env` and add your OpenAI API key
   - Configure other settings as needed

3. **Start the development environment**
   ```bash
   # Build and start containers
   docker-compose up -d
   
   # View logs
   docker-compose logs -f
   ```

4. **Access the application**
   - Website: http://localhost:8000/
   - Admin: http://localhost:8000/admin/
   - Default admin credentials (from .env):
     - Username: admin
     - Password: admin

5. **Development workflow**
   - The application code is mounted into the container for live reloading
   - Static files are served from `static_volume`
   - Media files are stored in `media_volume`

## 🚀 Production Deployment

1. **Prepare the production environment**
   ```bash
   # Create .env.production from .env.example
   cp .env.example .env.production
   
   # Edit .env.production with production settings
   # Make sure to set:
   # - DEBUG=False
   # - ALLOWED_HOSTS=your-domain.com,www.your-domain.com
   # - Configure database and other production settings
   ```

2. **Set up domain language mapping**
   In `.env.production`, configure:
   ```
   DOMAIN_LANGUAGE_MAPPING={"your-domain.com": "de", "en.your-domain.com": "en"}
   ```

3. **Deploy with Docker Compose**
   ```bash
   # Start production services
   docker-compose -f docker-compose.prod.yml up -d
   
   # View logs
   docker-compose -f docker-compose.prod.yml logs -f
   ```

4. **Set up a reverse proxy (Nginx example)**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com www.your-domain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

5. **Set up SSL (Let's Encrypt)**
   ```bash
   # Install certbot
   sudo apt install certbot python3-certbot-nginx
   
   # Obtain and install certificate
   sudo certbot --nginx -d your-domain.com -d www.your-domain.com
   ```

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

## 🛠 Using S3 for Media Storage (Optional)

1. Update `.env.production` with your AWS credentials:
   ```
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_STORAGE_BUCKET_NAME=your_bucket_name
   AWS_S3_REGION_NAME=your_region
   ```

2. The application will automatically use S3 for media storage when these variables are set.

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

## 🔄 Maintenance

### Managing Data

#### Backing up volumes
```bash
# Backup media files
docker run --rm -v ausmalbar-fullstack_media_volume:/source -v $(pwd):/backup alpine tar czf /backup/media_backup_$(date +%Y%m%d).tar.gz -C /source ./

# Backup database
docker-compose exec db pg_dump -U postgres ausmalbar > backup_$(date +%Y%m%d).sql
```

#### Restoring from backup
```bash
# Restore media files
docker run --rm -v ausmalbar-fullstack_media_volume:/target -v $(pwd):/backup alpine sh -c "rm -rf /target/* /target/..?* /target/.[!.]* ; tar xzf /backup/media_backup_20230527.tar.gz -C /target"

# Restore database
cat backup_20230527.sql | docker-compose exec -T db psql -U postgres ausmalbar
```

### Updating the Application

1. Pull the latest changes
   ```bash
   git pull origin main
   ```

2. Rebuild and restart the services
   ```bash
   # For development
   docker-compose up -d --build
   
   # For production
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

3. Run migrations if needed
   ```bash
   docker-compose exec web python manage.py migrate
   ```

4. Collect static files
   ```bash
   docker-compose exec web python manage.py collectstatic --noinput
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
