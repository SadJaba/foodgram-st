#!/bin/bash

# Wait for database to be ready
echo "Waiting for database..."
sleep 5

# Run migrations
echo "Running migrations..."
python manage.py makemigrations api --noinput
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser (if not exists)
echo "Creating superuser (if not exists)..."
python manage.py createsuperuser --noinput || true

# Load ingredients
echo "Loading ingredients..."
python manage.py load_ingredients || true

# Start server
echo "Starting server..."
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --access-logfile - --error-logfile - --log-level info 