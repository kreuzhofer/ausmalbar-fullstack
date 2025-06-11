# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Compile i18n messages
RUN python manage.py compilemessages

# Run the application
# Development/Debugging version (single worker, single thread)
# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "ausmalbar.wsgi:application"]

# Production version - optimized for 6-core CPU
# Workers = (2 x num_cores) + 1 = 13
# Threads = 2-4 per worker (using 3 as a balanced value)
# Timeout set to 120 seconds to handle longer-running requests like image generation
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "13", "--threads", "3", "--timeout", "120", "ausmalbar.wsgi:application"]
