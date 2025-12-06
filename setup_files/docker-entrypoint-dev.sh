#!/bin/bash

set -e  # Exit on error
set -x  # Print commands as they're executed
echo "Starting entrypoint script..."

# Trap SIGTERM and handle graceful shutdown
cleanup() {
    echo "Received shutdown signal, stopping services..."
    /etc/init.d/emol stop
    nginx -s quit
    exit 0
}

trap cleanup SIGTERM

# Create required directories
echo "Creating required directories..."
mkdir -p /var/log/emol /var/log/nginx /run/nginx
chown -R www-data:www-data /var/log/emol /var/log/nginx /run/nginx

# Create log files with proper permissions
touch /var/log/emol/gunicorn-access.log /var/log/emol/gunicorn-error.log /var/log/emol/emol.log
chown www-data:www-data /var/log/emol/gunicorn-access.log /var/log/emol/gunicorn-error.log /var/log/emol/emol.log
chmod 644 /var/log/emol/gunicorn-access.log /var/log/emol/gunicorn-error.log /var/log/emol/emol.log

# Configure services for startup
echo "Configuring services for startup..."

cd /opt/emol/emol

# Always configure services (container filesystem doesn't persist)
echo "Configuring nginx and gunicorn services..."

# Configure nginx
export NGINX_LOG_PATH="/var/log/nginx"
export STATIC_ROOT="/opt/emol/static"
export SOCKET_PATH="/opt/emol/emol.sock"

template_file="/opt/emol/setup_files/configs/nginx.dev.conf"

mkdir -p /etc/nginx/sites-enabled
envsubst < "$template_file" > /etc/nginx/sites-enabled/emol.conf
cp /opt/emol/setup_files/configs/proxy_params /etc/nginx/proxy_params

# Configure gunicorn service
cp /opt/emol/setup_files/configs/emol /etc/init.d/emol
chmod +x /etc/init.d/emol

echo "Services configured successfully"

echo "Testing nginx configuration..."
if ! nginx -t; then
    echo "Nginx configuration test failed"
    exit 1
fi

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

echo "Starting services..."
/etc/init.d/emol start

echo "Tailing logs to stdout..."
nginx
tail -f /var/log/emol/gunicorn-access.log /var/log/emol/gunicorn-error.log /var/log/emol/emol.log 2>/dev/null &
sleep 2
tail -f /var/log/emol/*.log 2>/dev/null