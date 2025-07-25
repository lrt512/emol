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

# Configure services for startup
echo "Configuring services for startup..."

# Source asdf and set up environment  
source ${ASDF_DIR}/asdf.sh
cd /opt/emol/emol

# Always configure services (container filesystem doesn't persist)
echo "Configuring nginx and gunicorn services..."

# Configure nginx
export NGINX_LOG_PATH="/var/log/nginx"
export STATIC_ROOT="/opt/emol/static"
export SOCKET_PATH="/opt/emol/emol.sock"

if [ "$EMOL_DEV" = "1" ]; then
    template_file="/opt/emol/setup_files/configs/nginx.dev.conf"
else
    template_file="/opt/emol/setup_files/configs/nginx.prod.conf"
fi

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

# Start services
echo "Starting services..."
/etc/init.d/emol start
nginx -g 'daemon off;'  # Run nginx in foreground

# No need for tail since nginx is running in foreground 