#!/bin/bash

set -e
echo "Starting container entrypoint script..."

cleanup() {
    echo "Received shutdown signal, stopping services..."
    service cron stop 2>/dev/null || true
    if [ -f /var/run/emol.pid ]; then
        kill $(cat /var/run/emol.pid) 2>/dev/null || true
        rm -f /var/run/emol.pid
    fi
    nginx -s quit 2>/dev/null || true
    exit 0
}

trap cleanup SIGTERM SIGINT

mkdir -p /var/log/emol /var/log/nginx /run/nginx
chown -R www-data:www-data /var/log/emol /var/log/nginx /run/nginx

touch /var/log/emol/gunicorn-access.log /var/log/emol/gunicorn-error.log /var/log/emol/emol.log
chown www-data:www-data /var/log/emol/gunicorn-access.log /var/log/emol/gunicorn-error.log /var/log/emol/emol.log
chmod 644 /var/log/emol/gunicorn-access.log /var/log/emol/gunicorn-error.log /var/log/emol/emol.log

cd /opt/emol/emol

export NGINX_LOG_PATH="/var/log/nginx"
export STATIC_ROOT="/opt/emol/static"
export SOCKET_PATH="/opt/emol/emol.sock"

template_file="/opt/emol/setup_files/configs/nginx.prod.conf"

mkdir -p /etc/nginx/sites-enabled
envsubst < "$template_file" > /etc/nginx/sites-enabled/emol.conf
cp /opt/emol/setup_files/configs/proxy_params /etc/nginx/proxy_params

if ! nginx -t; then
    echo "Nginx configuration test failed"
    exit 1
fi

echo "Running database operations..."
cd /opt/emol/emol

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

echo "Running reminder hygiene..."
poetry run python manage.py reminder_hygiene --fix || {
    echo "Warning: Reminder hygiene failed, continuing..."
}

echo "Setting up cron jobs..."
POETRY_BIN=$(which poetry)
cat > /etc/cron.d/emol << EOF
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
0 3 * * * root cd /opt/emol/emol && ${POETRY_BIN} run python manage.py send_reminders >> /var/log/emol/cron.log 2>&1
0 4 * * * root cd /opt/emol/emol && ${POETRY_BIN} run python manage.py clean_expired >> /var/log/emol/cron.log 2>&1
EOF
chmod 644 /etc/cron.d/emol
touch /var/log/emol/cron.log
service cron start
echo "Cron jobs configured"

echo "Starting gunicorn..."
cd /opt/emol/emol
poetry run gunicorn \
    --pid /var/run/emol.pid \
    --workers 2 \
    --bind unix:/opt/emol/emol.sock \
    --access-logfile /var/log/emol/gunicorn-access.log \
    --error-logfile /var/log/emol/gunicorn-error.log \
    --daemon \
    emol.wsgi:application

echo "Starting nginx..."
exec nginx -g 'daemon off;'

