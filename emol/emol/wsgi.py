"""
WSGI config for emol project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from django.core.management.base import CommandError

from emol.secrets import get_secret

settings = get_secret("/emol/django_settings_module")
if not settings:
    raise CommandError("Could not retrieve settings path from AWS Parameter Store")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings)

application = get_wsgi_application()
