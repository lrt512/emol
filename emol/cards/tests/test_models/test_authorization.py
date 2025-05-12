from django.test import TestCase

from cards.models.authorization import Authorization
from cards.models.discipline import Discipline


class AuthorizationModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up non-modified objects used by all test methods
        discipline = Discipline.objects.create(name="Heavy Rapier", slug="heavy-rapier")
        Authorization.objects.create(
            name="Armored Combat", slug="armored-combat", discipline=discipline
        )
