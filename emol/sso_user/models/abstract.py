import unicodedata

from django.db import models
from django.utils.translation import gettext_lazy as _


class AbstractBaseUser(models.Model):
    """
    Replacement AbstractBaseUser model without passwords.

    Last updated for Django 4.0.4
    """

    last_login = models.DateTimeField(_("last login"), blank=True, null=True)

    is_active = True

    REQUIRED_FIELDS: list[str] = []

    class Meta:
        abstract = True

    def __str__(self):
        return self.get_username()

    def get_username(self):
        """Return the username for this User."""
        return getattr(self, self.USERNAME_FIELD)

    def clean(self):
        setattr(self, self.USERNAME_FIELD, self.normalize_username(self.get_username()))

    def natural_key(self):
        return (self.get_username(),)

    @property
    def is_anonymous(self):
        """
        Always return False. This is a way of comparing User objects to
        anonymous users.
        """
        return False

    @property
    def is_authenticated(self):
        """
        Always return True. This is a way to tell if the user has been
        authenticated in templates.
        """
        return True

    def set_password(self, raw_password):
        pass

    def check_password(self, raw_password):  # noqa: ARG002
        return True

    def set_unusable_password(self):
        pass

    def has_usable_password(self):
        return False

    def get_session_auth_hash(self):
        raise NotImplementedError

    @classmethod
    def get_email_field_name(cls):
        try:
            return cls.EMAIL_FIELD
        except AttributeError:
            return "email"

    @classmethod
    def normalize_username(cls, username):
        return (
            unicodedata.normalize("NFKC", username)
            if isinstance(username, str)
            else username
        )
