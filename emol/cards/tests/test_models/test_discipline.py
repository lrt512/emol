from django.test import TestCase
from django.utils.text import slugify

from cards.models.discipline import Discipline


class DisciplineTestCase(TestCase):
    def setUp(self):
        self.heavy_rapier = Discipline.objects.create(name="Heavy Rapier")
        self.armoured_combat = Discipline.objects.create(name="Armoured Combat")

    def test_discipline_name(self):
        heavy_rapier = Discipline.objects.get(name="Heavy Rapier")
        armoured_combat = Discipline.objects.get(name="Armoured Combat")
        self.assertEqual(heavy_rapier.name, "Heavy Rapier")
        self.assertEqual(armoured_combat.name, "Armoured Combat")

    def test_discipline_slug_auto(self):
        heavy_rapier = Discipline.objects.get(name="Heavy Rapier")
        self.assertEqual(heavy_rapier.slug, slugify(heavy_rapier.name))

    def test_discipline_slug_manual(self):
        test_discipline = Discipline.objects.create(
            name="Test Discipline", slug="dumb-slug"
        )
        self.assertEqual(test_discipline.slug, "dumb-slug")

    def test_discipline_find_slug(self):
        heavy_rapier = Discipline.find("heavy-rapier")
        self.assertEqual(heavy_rapier.name, "Heavy Rapier")

    def test_discipline_find_name(self):
        heavy_rapier = Discipline.find("Heavy Rapier")
        self.assertEqual(heavy_rapier.name, "Heavy Rapier")

    def test_discipline_find_object(self):
        heavy_rapier = Discipline.find(self.heavy_rapier)
        self.assertEqual(self.heavy_rapier, heavy_rapier)
