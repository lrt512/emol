from uuid import uuid4

from django.db import models


class CombatantAuthorization(models.Model):
    """
    Model for the through table between Card and Authorization.
    Declared in the Card model's authorization attribute.
    """

    class Meta:
        db_table = "cards_combatant_authorization"
        indexes = [models.Index(fields=["uuid"])]
        constraints = [
            models.UniqueConstraint(
                name="combatant_authorization", fields=["card", "authorization"]
            )
        ]

    card = models.ForeignKey("Card", on_delete=models.CASCADE)
    authorization = models.ForeignKey("Authorization", on_delete=models.DO_NOTHING)
    uuid = models.UUIDField(default=uuid4, editable=False)

    def __str__(self):
        return "<Authorization: %s => %s/%s>" % (
            self.card.combatant.name,
            self.card.discipline.name,
            self.authorization.name,
        )
