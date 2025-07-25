#!/bin/bash

set -e  # Exit on error
set -x  # Print commands as they're executed
echo "Starting entrypoint script..."

# Source asdf
source ${ASDF_DIR}/asdf.sh

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

# Run bootstrap script in dev mode
echo "Running bootstrap script..."
EMOL_DEV=1 /opt/emol/setup_files/bootstrap.sh
echo "Bootstrap script completed with status $?"

echo "Testing nginx configuration..."
if ! nginx -t; then
    echo "Nginx configuration test failed"
    exit 1
fi

# Start services
echo "Starting services..."
/etc/init.d/emol start
nginx -g 'daemon off;'  # Run nginx in foreground

# No need for tail since nginx is running in foreground 