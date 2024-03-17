#!/bin/bash

apt-get update
apt-get install -y \
    nginx certbot \
    git python3-venv python3-pip \
    python3-certbot-nginx

apt-get install -y --no-install-recommends \
    build-essential pkg-config  \
    python3-dev \
    libmysqlclient-dev

mkdir -p /opt/venv
python3 -m venv /opt/venv
source /opt/venv/bin/activate

cd /opt
git clone https://github.com/lrt512/emol.git
chown -R www-data:www-data /opt/emol

pip install --upgrade pip
pip install wheel
pip install -r /opt/emol/requirements/prod.txt

chown -R www-data:www-data /opt/venv

rm /etc/nginx/sites-enabled/default
cp /docker_files/nginx.conf /etc/nginx/sites-enabled/

# apt-get purge --auto-remove -y build-essential
# apt-get clean
# rm -rf /var/lib/apt/lists/*

cd /app
echo "Apply migrations"
/opt/venv/bin/python manage.py migrate

echo "Collect static files"
/opt/venv/bin/python manage.py collectstatic --noinput

echo "Create cache table if needed"
/opt/venv/bin/python manage.py createcachetable
