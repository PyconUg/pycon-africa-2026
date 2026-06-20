from django.core.management.base import BaseCommand

from fin_aid.flight_budgets import get_review_region
from fin_aid.models import FinAidApplicationReview


class Command(BaseCommand):
    help = (
        "Fix opportunity grant reviews where the region was saved incorrectly "
        "(empty or mismatched) and recalculate total_score."
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

            region_wrong = old_region != expected_region and (
                not old_region or old_region == ""
            )

            if region_wrong:
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

            if region_wrong or score_changed:
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
