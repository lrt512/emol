# -*- coding: utf-8 -*-
"""Model for a discipline's marshal."""

from cards.models.discipline import Discipline
from django.db import models
from django.utils.text import slugify

__all__ = ["Marshal"]


class Marshal(models.Model):
    """Model a type of marshal for a discipline.

    Often just "Marshal", but some places have specific marshal types
    e.g. "Cut and Thrust Marshal"

    """

    slug = models.CharField(max_length=255, null=False)
    name = models.CharField(max_length=255, null=False)
    discipline = models.ForeignKey(
        Discipline, on_delete=models.CASCADE, related_name="marshals"
    )

    def __str__(self):
        return f"<Marshal: {self.discipline.slug}.{self.slug}>"

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @classmethod
    def find(cls, discipline, marshal):
        """Look up an marshal.

        Args:
            discipline: A discipline slug (string) or id (int) or
                Discipline object
            marshal: An marshal slug (string) or id (int)
                or Marshal object

        Returns:
            Marshal object

        Raises:
            Marshal.DoesNotExist
            Discipline.DoesNotExist

        """
        #  Null case
        if isinstance(marshal, Marshal):
            return marshal

        discipline = Discipline.find(discipline)
        query = models.Q(slug=marshal) | models.Q(name=marshal)
        return cls.objects.get(query, discipline=discipline)
