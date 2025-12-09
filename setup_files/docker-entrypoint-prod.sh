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
    exit 0
}

trap cleanup SIGTERM SIGINT

mkdir -p /var/log/emol
chown -R www-data:www-data /var/log/emol

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
exec poetry run gunicorn \
    --pid /var/run/emol.pid \
    --workers 2 \
    --bind 0.0.0.0:8000 \
    --access-logfile /var/log/emol/gunicorn-access.log \
    --error-logfile /var/log/emol/gunicorn-error.log \
    --forwarded-allow-ips='*' \
    emol.wsgi:application

