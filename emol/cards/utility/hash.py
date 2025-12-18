# -*- coding: utf-8 -*-
"""Hash utility using SHA256."""

import hashlib

from django.conf import settings


class SHA256:
    """SHA256 hashing class.

    Provides hash generation and verification.

    The salt value used is defined as HASH_SALT in config.py

    """

    @classmethod
    def generate_hash(cls, payload):
        """Generate a salted hash for the given payload."""
        salt = bytes(settings.HASH_SALT, "UTF-8")
        return hashlib.sha256(bytes(str(payload), "UTF-8") + salt).hexdigest()

    @classmethod
    def validate_hash(cls, payload, compare):
        """Validate a hash."""
        return cls.generate_hash(str(payload)) == compare
