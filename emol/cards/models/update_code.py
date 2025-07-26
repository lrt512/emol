import uuid
from datetime import datetime
from urllib.parse import urljoin

from cards.utility.time import utc_tomorrow
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from .combatant import Combatant


class UpdateCode(models.Model):
    combatant = models.OneToOneField(Combatant, on_delete=models.CASCADE)
    code = models.UUIDField(default=uuid.uuid4, unique=True)
    expires_at = models.DateTimeField(default=utc_tomorrow)

    def __str__(self):
        email = self.combatant.email
        code_str = str(self.code)[:4] + "..." + str(self.code)[-4:]
        expires_at_str = self.expires_at.astimezone(
            timezone.get_current_timezone()
        ).strftime("%Y-%m-%d %H:%M")

        return f"<UpdateCode: {email} ({code_str}) {expires_at_str}>"

    @property
    def url(self):
        """The URL for this update code."""
        return urljoin(
            settings.BASE_URL, reverse("self-serve-update", args=[self.code])
        )
