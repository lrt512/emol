from cards.admin.authorization import AuthorizationAdmin  # noqa: F401
from cards.admin.card import CardAdmin  # noqa: F401
from cards.admin.combatant import CombatantAdmin  # noqa: F401
from cards.admin.discipline import DisciplineAdmin  # noqa: F401
from cards.admin.marshal import MarshalAdmin  # noqa: F401
from cards.admin.one_time_code import OneTimeCodeAdmin  # noqa: F401
from cards.admin.permission import Permission  # noqa: F401
from cards.admin.privacy import PrivacyAcceptanceAdmin  # noqa: F401
from cards.admin.privacy import PrivacyPolicyAdmin  # noqa: F401
from cards.admin.region import RegionAdmin  # noqa: F401
from cards.admin.reminder import ReminderAdmin  # noqa: F401
from cards.admin.user_permission import UserPermission  # noqa: F401
from cards.admin.waiver import WaiverAdmin  # noqa: F401
from django.contrib import admin
from django.contrib.auth.models import Group

# We don't use the native group stuff so remove it from admin
admin.site.unregister(Group)
