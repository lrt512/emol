from django.contrib import admin
from django.contrib.auth.models import Group

from .authorization import AuthorizationAdmin  # noqa: F401
from .card import CardAdmin  # noqa: F401
from .combatant import CombatantAdmin  # noqa: F401
from .discipline import DisciplineAdmin  # noqa: F401
from .marshal import MarshalAdmin  # noqa: F401
from .one_time_code import OneTimeCodeAdmin  # noqa: F401
from .permission import Permission  # noqa: F401
from .privacy import PrivacyAcceptanceAdmin  # noqa: F401
from .privacy import PrivacyPolicyAdmin  # noqa: F401
from .region import RegionAdmin  # noqa: F401
from .reminder import ReminderAdmin  # noqa: F401
from .user_permission import UserPermission  # noqa: F401
from .waiver import WaiverAdmin  # noqa: F401

# We don't use the native group stuff so remove it from admin
admin.site.unregister(Group)
