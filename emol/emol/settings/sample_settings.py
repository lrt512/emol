"""Base settings for production deployment"""

import os

from emol.secrets import get_secret
from .defaults import *  # noqa: F403, F401

# -------------------------------------------------------------------------------------
# !!! Configure these settings for your deployment

# Your AWS region.
# If you aren't hosting in AWS, you've got a lot of work to do.
AWS_REGION = "ca-central-1"

# This is the secret key for your Django application. It should be a long
# random string. It is used for cryptographic signing. Keep it secret!
# Here are some possible ways to handle it:
SECRET_KEY = get_secret("/emol/secret_key")
# - or -
# SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
# - or -
# SECRET_KEY = "!!! REPLACE WITH A RANDOM STRING !!!"

# This is the base URL for your site. It is whatever you have configured
# in your web server to point to the Django application. For example, if
# you have configured your web server to point to the Django application
# at http://yourdomain.com, then this should be "http://yourdomain.com".
# If it's at http://yourdomain.com/emol, then this should be
# "http://yourdomain.com/emol".
# If it's a subdomain like http://emol.yourdomain.com, then this should be
# "http://emol.yourdomain.com".
BASE_URL = "http://yourdomain.com"

# ALLOWED_HOSTS is a list of host/domain names that this Django site can serve.
# This is a security measure to prevent HTTP Host header attacks, which are
# possible even under many seemingly-safe web server configurations.
# For example, if you have configured your web server to point to the Django
# application at http://yourdomain.com, then this should be ["yourdomain.com"].
# If it's at http://yourdomain.com/emol, then this should be ["yourdomain.com"].
# If it's a subdomain like http://emol.yourdomain.com, then this should be
# ["emol.yourdomain.com"].
# You really SHOULD NOT use ["*"] here.
ALLOWED_HOSTS = ["CHANGE_THIS_TO_YOUR_DOMAIN_NAME"]

# Timezone identifier for your locale
# See https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
TIME_ZONE = "America/Toronto"

# Address that emails are sent from. This is what will show up in the
# "From" field of the email. This should be an email address that is
# configured to send email from your server. If you are using a service
# like AWS SES, then this probably needs to be an email address that is verified
# in the service.
MAIL_DEFAULT_SENDER = "emol@kingdom.org"

# Email address for your kingdom MOL
MOL_EMAIL = "minister.of.lists@kingdom.org"

# Configure Google authentication
AUTHLIB_OAUTH_CLIENTS = {
    "google": {
        "client_id": get_secret("/emol/oauth_client_id"),
        "client_secret": get_secret("/emol/oauth_client_secret"),
    }
}

# Configure your database. This is for MySQL
# See https://docs.djangoproject.com/en/4.2/ref/settings/#databases for others
#
# For the database password, if you can inject it into the environment
# that is a best practice. If you can't, you can put it here like
# below but be sure to keep it secret.
# DATABASE_PASSWORD = "your_password"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": get_secret("/emol/db_name"),
        "USER": get_secret("/emol/db_user"),
        "PASSWORD": get_secret("/emol/db_password"),
        "HOST": get_secret("/emol/db_host"),
        "PORT": "3306",
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            "charset": "utf8mb4",
        },
    }
}


# -------------------------------------------------------------------------------------
# !!! Default values that can be changed if desired
# These are the default values for various things that you
# can change if you want.

# Number of days before expiry for reminder emails
REMINDER_DAYS = [60, 30, 14, 0]

# Global throttle config
# This is for limiting the effect of a DDOS attack or web crawlers
# that are hitting the site too hard. It will limit the number of
# requests that can be made in a given window of time.
# The default is 20 requests in 1 hour.
# Don't set it so tight that it affects normal users!
# But also note that authenticated users are not throttled.
GLOBAL_THROTTLE_LIMIT = 20
GLOBAL_THROTTLE_WINDOW = 3600

# If you're not using AWS SES, you'll need to write your own emailer.
# If you are using AWS SES, make sure AWS_REGION is set to your region.
EMAILER = "emol.emailer.AWSEmailer"
