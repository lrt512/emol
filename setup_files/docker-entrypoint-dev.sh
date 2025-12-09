#!/bin/bash

set -e  # Exit on error
set -x  # Print commands as they're executed
echo "Starting entrypoint script..."

# Create required directories
echo "Creating required directories..."
mkdir -p /var/log/emol
chown -R www-data:www-data /var/log/emol

# Create log files with proper permissions
touch /var/log/emol/gunicorn-access.log /var/log/emol/gunicorn-error.log /var/log/emol/emol.log
chown www-data:www-data /var/log/emol/gunicorn-access.log /var/log/emol/gunicorn-error.log /var/log/emol/emol.log
chmod 644 /var/log/emol/gunicorn-access.log /var/log/emol/gunicorn-error.log /var/log/emol/emol.log

cd /opt/emol/emol

echo "Running database operations..."

echo "Applying migrations..."
poetry run python manage.py migrate --noinput || {
    echo "Warning: Migrations failed, continuing anyway..."
}

echo "Collecting static files..."
poetry run python manage.py collectstatic --noinput || {
    echo "Warning: Static file collection failed, continuing anyway..."
}

echo "Creating cache table..."
poetry run python manage.py createcachetable 2>/dev/null || {
    echo "Cache table may already exist, continuing..."
}

echo "Ensuring superuser exists..."
poetry run python manage.py ensure_superuser --non-interactive || {
    echo "Warning: Superuser creation failed, continuing..."
}

echo "Loading dev disciplines..."
poetry run python manage.py import_disciplines /opt/emol/config/dev_disciplines.json || {
    echo "Warning: Discipline import failed, continuing..."
}

echo "Seeding privacy policy..."
poetry run python manage.py seed_privacy_policy || {
    echo "Warning: Privacy policy seed failed, continuing..."
}

echo "Starting Gunicorn on port 8000..."
# Start Gunicorn in foreground
exec poetry run gunicorn \
    --workers 2 \
    --bind 0.0.0.0:8000 \
    --access-logfile /var/log/emol/gunicorn-access.log \
    --error-logfile /var/log/emol/gunicorn-error.log \
    --access-logformat '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s' \
    --log-level info \
    --reload \
    emol.wsgi:application
