import os

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def settings_notice():
    if settings.SETTINGS_MODULE == "emol.settings.dev_settings":
        return mark_safe(
            '<span class="warning">Using default development settings</span>'
        )

    return ""


@register.simple_tag
def app_version():
    """Read and return the application version from VERSION file."""
    # VERSION file is at /opt/emol/VERSION in the container
    # Try multiple possible locations for flexibility
    possible_paths = [
        "/opt/emol/VERSION",  # Container path
        os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            ),
            "VERSION",
        ),  # Dev path
    ]

    for version_file in possible_paths:
        if os.path.exists(version_file):
            try:
                with open(version_file, "r") as f:
                    version = f.read().strip()
                    return f"v{version}" if version else ""
            except (IOError, OSError):
                continue
    return ""
