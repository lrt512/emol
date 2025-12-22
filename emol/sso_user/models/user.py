from django.contrib.auth.models import BaseUserManager
from django.db import models
from django.utils.crypto import salted_hmac
from sso_user.models.abstract import AbstractBaseUser


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, **extra_fields):
        if email is None:
            raise ValueError("An email must be provided")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.save(using=self._db)
        return user

    def create_user(self, email, **extra_fields):
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_staff", False)
        return self._create_user(email, **extra_fields)

    def create_superuser(self, email, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        return self._create_user(email, **extra_fields)


class SSOUser(AbstractBaseUser):
    email = models.EmailField(unique=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"

    objects = UserManager()

    class Meta:
        db_table = "sso_user"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email.split("@", maxsplit=1)[0]

    def get_session_auth_hash(self):
        """
        Return an HMAC of the password field.
        """
        key_salt = "django.contrib.auth.models.AbstractBaseUser.get_session_auth_hash"
        return salted_hmac(
            key_salt,
            self.email,
            algorithm="sha256",
        ).hexdigest()

    def has_module_perms(self, package_name):  # noqa: ARG002
        """Unused in this context, we use our own permissions systems"""
        return True

    def has_perm(self, perm, obj=None):  # noqa: ARG002
        """Unused in this context, we use our own permissions systems"""
        return True
