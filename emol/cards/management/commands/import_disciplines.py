import json

from cards.models import Authorization, Discipline, Marshal
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Load disciplines, authorizations, and marshals from a JSON file"

    def add_arguments(self, parser):
        parser.add_argument("json_file", type=str, help="Path to the JSON file")

    def handle(self, *args, **options):
        json_file = options["json_file"]

        with open(json_file, "r") as f:
            data = json.load(f)

        for discipline_data in data:
            discipline_name = discipline_data["name"]
            discipline, created = Discipline.objects.get_or_create(name=discipline_name)
            result = "created" if created else "already exists"
            self.stdout.write(
                self.style.SUCCESS(f"Discipline `{discipline_name}` {result}")
            )

            for authorization_data in discipline_data.get("authorizations", []):
                authorization_name = authorization_data["name"]
                is_primary = authorization_data.get("is_primary", False)
                _, auth_created = Authorization.objects.get_or_create(
                    name=authorization_name,
                    discipline=discipline,
                    defaults={"is_primary": is_primary},
                )
                result = "created" if auth_created else "already exists"
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Authorization `{authorization_name}` {result}"
                    )
                )

            for marshal_data in discipline_data.get("marshals", []):
                marshal_name = marshal_data["name"]
                _, marshal_created = Marshal.objects.get_or_create(
                    name=marshal_name, discipline=discipline
                )
                result = "created" if marshal_created else "already exists"
                self.stdout.write(
                    self.style.SUCCESS(f"  Marshal `{marshal_name}` {result}")
                )

        self.stdout.write(self.style.SUCCESS("Data loaded successfully"))
