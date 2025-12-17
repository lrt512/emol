from uuid import uuid4

from django.db import models

from .card import Card
from .marshal import Marshal


class CombatantWarrant(models.Model):
    """
    Model for the through table between Card and Marshal.
    The through table relates to warrants to match our nomenclature
    Declared in the Card model's authorization attribute.
    """

    class Meta:
        db_table = "cards_combatant_warrant"
        indexes = [models.Index(fields=["uuid"])]
        constraints = [
            models.UniqueConstraint(
                name="combatant_warrant", fields=["card", "marshal"]
            )
        ]

    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    marshal = models.ForeignKey(Marshal, on_delete=models.DO_NOTHING)
    uuid = models.UUIDField(default=uuid4, editable=False)

    def __str__(self):
        return "<Warrant: %s => %s/%s>" % (
            self.card.combatant.name,
            self.card.discipline.name,
            self.marshal.name,
        )
