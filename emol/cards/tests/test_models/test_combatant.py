from datetime import datetime

from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase

from cards.models.authorization import Authorization
from cards.models.combatant import Combatant
from cards.models.discipline import Discipline


class CombatantModelTestCase(TestCase):
    def setUp(self):
        self.discipline = Discipline.objects.create(name="Fencing")
        self.authorization = Authorization.objects.create(
            name="Heavy Rapier", discipline=self.discipline, is_primary=True
        )
        self.combatant = Combatant.objects.create(
            sca_name="John the Blue", legal_name="John Smith"
        )

    def test_combatant_with_no_legal_name(self):
        self.combatant.legal_name = None
        with self.assertRaises(IntegrityError):
            self.combatant.save()

    def test_combatant_waiver_date(self):
        self.combatant.waiver_date = datetime(2018, 1, 1)
        self.combatant.save()
        assert (
            self.combatant.waiver_expires
            == self.combatant.waiver_date + self.combatant.waiver_duration
        )

    # A test to verify that the privacy policy code is generated correctly
    def test_combatant_privacy_policy_code(self):
        assert self.combatant.privacy_policy_code == "JtB"
