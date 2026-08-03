"""Management command to assign a specific number of Regional Grant applications to a reviewer."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from fin_aid.models import REGIONAL_GRANT_COUNTRIES
from fin_aid.services import assign_regional_grant_reviews

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Give a user a lot of N Regional Grant applications total, independent of "
        "country-based access. N is a target total, not an increment: if the user "
        "already holds some assignments, only the shortfall is added, and re-running "
        "with the same N is a no-op once they've reached it. Never removes assignments."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--user",
            required=True,
            metavar="USERNAME",
            help="Username of the reviewer to assign applications to.",
        )
        parser.add_argument(
            "--count",
            type=int,
            required=True,
            metavar="N",
            help="Target total number of applications this user should hold (e.g. --count=15).",
        )
        parser.add_argument(
            "--country",
            nargs="+",
            metavar="COUNTRY",
            help=(
                "Restrict assignment to these country code(s) "
                f"({', '.join(code for code, _label in REGIONAL_GRANT_COUNTRIES)}). "
                "Defaults to any country (e.g. --country kenya rwanda)."
            ),
        )

    def handle(self, *args, **options):
        username = options["user"]
        count = options["count"]
        country_codes = options["country"]

        if count <= 0:
            raise CommandError("--count must be a positive integer.")

        valid_countries = {code for code, _label in REGIONAL_GRANT_COUNTRIES}
        if country_codes:
            invalid = set(country_codes) - valid_countries
            if invalid:
                raise CommandError(
                    f"Invalid country code(s): {', '.join(sorted(invalid))}. "
                    f"Valid choices: {', '.join(sorted(valid_countries))}."
                )

        try:
            reviewer = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"No user found with username '{username}'.")

        if country_codes:
            self.stdout.write(f"Restricting to countries: {', '.join(country_codes)}")

        result = assign_regional_grant_reviews(reviewer, count, countries=country_codes)

        if result["created"] == 0 and result["available"] == 0 and result["current_total"] >= count:
            self.stdout.write(f"{username} already holds {result['current_total']}/{count}; nothing to do.")
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Assigned {result['created']} new application(s) to {username} "
                    f"({result['current_total']}/{count} total)."
                )
            )
        if result["current_total"] < count:
            self.stdout.write(
                self.style.WARNING(
                    f"Only {result['available']} eligible application(s) were "
                    f"available — could not reach the target of {count}."
                )
            )
