"""Abstract and Metaclass magic for ReminderMixin"""

from abc import ABCMeta

from dirtyfields import DirtyFieldsMixin
from django.db.models.base import ModelBase


class ReminderMixinMeta(ABCMeta):
    """Metaclass for ReminderMixin"""

    pass


class ReminderMixin:
    """Base class for models that have reminders

    This really should be an abstract class but the
    metaclass madness is intense.
    """

    @property
    def expiration_date(self):
        """The date this reminder expires"""
        raise NotImplementedError()

    def send_expiry(self, reminder):
        """Send a expiry notification email"""
        raise NotImplementedError()

    def send_reminder(self, reminder):
        """Send a reminder email"""
        raise NotImplementedError()


# We need a fancy metaclass for mixing Model, ReminderMixin, and DirtyFieldsMixin
class DirtyModelReminderMeta(ModelBase, ReminderMixinMeta, type(DirtyFieldsMixin)):
    """For any model that inherits from both ReminderMixin and DirtyFieldsMixin

    This works for solving the metaclass problems if ReminderMixin is abstract,
    but the metaclass error surfaces in migrations as well and isn't solved yet.

    class MyDirtyReminderModel(
        models.Model,
        ReminderMixin,
        DirtyFieldsMixin,
        metaclass=DirtyModelReminderMeta
    ):
        ...
    """

    pass
