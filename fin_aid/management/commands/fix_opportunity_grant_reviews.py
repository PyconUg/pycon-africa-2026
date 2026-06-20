from django.core.management.base import BaseCommand

from fin_aid.flight_budgets import get_review_region
from fin_aid.models import FinAidApplicationReview


class Command(BaseCommand):
    help = (
        "Fix opportunity grant reviews: fill in missing regions from the "
        "applicant's country and recalculate total_score using the corrected "
        "regional scoring (Uganda=3, East Africa=2, Other Africa=1, Outside=0)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without writing to the database.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        reviews = FinAidApplicationReview.objects.select_related("application").all()

        fixed_region = 0
        fixed_score = 0

        for review in reviews:
            country_code = str(review.application.country.code)
            expected_region = get_review_region(country_code)
            old_region = review.region
            old_score = review.total_score

            if not old_region:
                review.region = expected_region
                fixed_region += 1

            new_score = (
                review.contributor_score
                + review.regional_score
                + review.diversity_score
                + review.alignment_score
                + review.grant_type_score
            )
            score_changed = new_score != old_score

            if not old_region or score_changed:
                self.stdout.write(
                    f"  Review {review.pk} "
                    f"(country={country_code}): "
                    f"region {old_region!r} -> {review.region!r}, "
                    f"score {old_score} -> {new_score}"
                )
                if score_changed:
                    fixed_score += 1
                if not dry_run:
                    review.save()

        action = "Would fix" if dry_run else "Fixed"
        self.stdout.write(
            self.style.SUCCESS(
                f"\n{action} {fixed_region} region(s) and "
                f"{fixed_score} score(s) across {reviews.count()} reviews."
            )
        )
        if dry_run:
            self.stdout.write(
                self.style.WARNING("Dry run — no changes written. Remove --dry-run to apply.")
            )
