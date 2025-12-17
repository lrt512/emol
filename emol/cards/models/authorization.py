from django.db import models
from django.utils.text import slugify

from .discipline import Discipline


class Authorization(models.Model):
    """Model an authorization for a discipline.

    Authorizations are referenced by the Card model through the
    CombatantAuthorization association model. See Card model docs for detail.

    Attributes:
        id: Primary key in the database
        slug: Slugified name for the authorization
        name: Full name of the authorization
        discipline: FK to the discipline this card is for
        is_primary: Authorization can be a primary authorization

    """

    class Meta:
        # Add a unique constraint for the combination of slug and discipline
        unique_together = ("slug", "discipline")

    slug = models.SlugField(max_length=255, editable=False)
    name = models.CharField(max_length=255, null=False)
    is_primary = models.BooleanField(default=False, null=False)
    discipline = models.ForeignKey(
        Discipline, related_name="authorizations", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"<Authorization: {self.discipline.slug}.{self.slug}>"

    def save(self, *args, **kwargs):
        if not self.pk and not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @classmethod
    def find(cls, discipline, authorization):
        """Look up an authorization.

        Args:
            discipline: A discipline slug, id, or Discipline object
            authorization: An authorization slug, id, or Authorization object

        Returns:
            Authorization object

        Raises:
            Authorization.DoesNotExist, Discipline.DoesNotExist
        """
        if isinstance(authorization, Authorization):
            return authorization

        discipline = Discipline.find(discipline)
        query = models.Q(slug=authorization) | models.Q(name=authorization)
        return cls.objects.get(query, discipline=discipline)
