"""Management command to assign opportunity grant applications to reviewers."""

from django.core.management.base import BaseCommand, CommandError

from django.db.models import Count

from fin_aid.models import FinAidReviewer, OpportunityGrantApplication
from fin_aid.services import assign_applications
from home.models import EventYear


class Command(BaseCommand):
    help = (
        "Assign submitted opportunity grant applications to reviewers for a "
        "given event year. Reviewers with review_load='all' receive every "
        "eligible application; reviewers with review_load='equal' share the "
        "remainder via round-robin."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--year",
            type=int,
            required=True,
            help="Event year to run assignment for (e.g. --year=2026).",
        )
        parser.add_argument(
            "--reviewers",
            nargs="+",
            metavar="USERNAME",
            help="Usernames of specific reviewers to assign to (e.g. --reviewers alice bob).",
        )
        parser.add_argument(
            "--max-reviews",
            type=int,
            metavar="N",
            help="Only assign applications with fewer than N completed reviews (e.g. --max-reviews=2).",
        )
        parser.add_argument(
            "--reassign",
            action="store_true",
            help=(
                "Remove unreviewed assignments and redistribute. "
                "Completed reviews are preserved."
            ),
        )

    def handle(self, *args, **options):
        year = options["year"]
        usernames = options["reviewers"]
        max_reviews = options["max_reviews"]
        reassign = options["reassign"]

        try:
            event_year = EventYear.objects.get(year=year)
        except EventYear.DoesNotExist:
            raise CommandError(f"Event year {year} does not exist.")

        reviewers = None
        if usernames:
            reviewers = FinAidReviewer.objects.filter(
                user__username__in=usernames, is_active=True
            ).select_related("user")
            found = set(reviewers.values_list("user__username", flat=True))
            missing = set(usernames) - found
            if missing:
                raise CommandError(
                    f"No active reviewer(s) found for: {', '.join(sorted(missing))}"
                )
            self.stdout.write(
                f"Assigning to {len(found)} reviewer(s): {', '.join(sorted(found))}"
            )

        applications = None
        if max_reviews is not None:
            applications = (
                OpportunityGrantApplication.objects.filter(
                    fin_aid__event_year=event_year,
                    status__in=[
                        OpportunityGrantApplication.STATUS_SUBMITTED,
                        OpportunityGrantApplication.STATUS_IN_REVIEW,
                    ],
                )
                .annotate(review_count=Count("reviews"))
                .filter(review_count__lt=max_reviews)
                .select_related("user")
            )
            self.stdout.write(
                f"Filtering to {applications.count()} application(s) with fewer "
                f"than {max_reviews} review(s)."
            )

        if reassign:
            self.stdout.write(
                self.style.WARNING(
                    f"--reassign specified: unreviewed assignments for {year} "
                    "will be removed and redistributed."
                )
            )

        result = assign_applications(
            event_year,
            applications=applications,
            reviewers=reviewers,
            soft_reassign=reassign,
        )

        if result["deleted"]:
            self.stdout.write(
                f"Removed {result['deleted']} unreviewed assignment(s)."
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {result['created']} new assignment(s) for {year}."
            )
        )

        if result["reviews_per_application"]:
            self.stdout.write(
                f"Target reviews per application: {result['reviews_per_application']}"
            )

        if result["per_reviewer"]:
            self.stdout.write("\nPer-reviewer breakdown:")
            for username, count in sorted(
                result["per_reviewer"].items(), key=lambda kv: -kv[1]
            ):
                self.stdout.write(f"  {username}: {count}")

        if result["unassignable"]:
            self.stdout.write(
                self.style.WARNING(
                    f"\n{len(result['unassignable'])} application(s) could not "
                    "be assigned to any reviewer:"
                )
            )
            for app_id in result["unassignable"]:
                self.stdout.write(f"  - {app_id}")
