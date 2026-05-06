"""Management command to assign proposals to reviewers."""

from django.core.management.base import BaseCommand, CommandError

from home.models import EventYear
from talks.services import assign_proposals


class Command(BaseCommand):
    help = (
        "Assign submitted proposals to reviewers for a given event year. "
        "Reviewers with review_load='all' receive every eligible proposal; "
        "reviewers with review_load='equal' share the remainder via round-robin."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            required=True,
            help="Event year to run assignment for (e.g. --year=2026).",
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help="Delete existing assignments for the year before assigning. Use with care.",
        )

    def handle(self, *args, **options):
        year = options['year']
        reset = options['reset']

        try:
            event_year = EventYear.objects.get(year=year)
        except EventYear.DoesNotExist:
            raise CommandError(f"Event year {year} does not exist.")

        if reset:
            self.stdout.write(self.style.WARNING(
                f"--reset specified: existing assignments for {year} will be deleted first."
            ))

        result = assign_proposals(event_year, reset=reset)

        self.stdout.write(self.style.SUCCESS(
            f"Created {result['created']} new review assignment(s) for {year}."
        ))

        if result['per_reviewer']:
            self.stdout.write("\nPer-reviewer breakdown:")
            for username, count in sorted(result['per_reviewer'].items(), key=lambda kv: -kv[1]):
                self.stdout.write(f"  {username}: {count}")

        if result['unassignable']:
            self.stdout.write(self.style.WARNING(
                f"\n{len(result['unassignable'])} proposal(s) could not be assigned to any reviewer:"
            ))
            for pid in result['unassignable']:
                self.stdout.write(f"  - {pid}")
