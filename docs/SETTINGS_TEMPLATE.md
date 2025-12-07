"""Sample production settings template.

This file is a template for creating instance-specific production settings.
Copy this to /opt/emol_config/emol_production.py on your production server
to override any settings from emol.settings.prod.

Example usage:
    from emol.settings.prod import *

    # Override specific settings
    ALLOWED_HOSTS = ["your-domain.com"]
    BASE_URL = "https://your-domain.com"
"""

from emol.settings.prod import *  # noqa: F403, F401

# Override settings here as needed
# ALLOWED_HOSTS = ["your-domain.com"]
# BASE_URL = "https://your-domain.com"

