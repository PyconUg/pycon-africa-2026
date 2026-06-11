"""Service layer for the fin_aid app.

Provides the opportunity grant review assignment algorithm.
"""

from collections import defaultdict
from typing import Iterable, Optional

from django.db import transaction
from django.db.models import Count, Exists, OuterRef

from .models import (
    FinAidApplicationReview,
    FinAidReviewAssignment,
    FinAidReviewer,
    OpportunityGrantApplication,
)


def _eligible_applications_for(
    reviewer: FinAidReviewer,
    applications: Iterable[OpportunityGrantApplication],
) -> list:
    """Filter out applications submitted by the reviewer themselves."""
    return [a for a in applications if a.user_id != reviewer.user_id]


def _target_reviews_per_application(num_reviewers: int) -> int:
    """Target 3 reviews per application."""
    return min(num_reviewers, 3)


@transaction.atomic
def assign_applications(
    event_year,
    *,
    applications: Optional[Iterable[OpportunityGrantApplication]] = None,
    reviewers: Optional[Iterable[FinAidReviewer]] = None,
    assigned_by=None,
    soft_reassign: bool = False,
) -> dict:
    """Assign opportunity grant applications to reviewers for a given event year.

    Rules:
      * A reviewer is never assigned an application they submitted themselves.
      * Reviewers with ``review_load='all'`` receive every eligible application.
      * Reviewers with ``review_load='equal'`` share the workload via round-robin.
        Each application targets multiple reviews (min 2, scales with reviewer
        count: floor(N/2) for N >= 4).
      * Idempotent: existing assignments are preserved.
      * When ``soft_reassign=True``, only unreviewed assignments are removed before
        redistributing. Completed reviews stay in place and count toward each
        reviewer's load so they are not piled on again.

    Args:
        event_year: ``home.EventYear`` instance the assignment is scoped to.
        applications: Optional explicit queryset/iterable of applications to assign.
            Defaults to all submitted/in-review applications for ``event_year``.
        reviewers: Optional explicit queryset/iterable of reviewers to use.
            Defaults to all active reviewers.
        assigned_by: Optional ``User`` who triggered the assignment (audit trail).
        soft_reassign: If True, delete unreviewed assignments before reassigning.
            Completed reviews are preserved and count toward each reviewer's load.

    Returns:
        dict with keys:
          ``created`` (int),
          ``deleted`` (int — unreviewed assignments removed during soft reassign),
          ``reviews_per_application`` (int — target used for equal-load reviewers),
          ``unassignable`` (list of application PKs no eligible reviewer could take),
          ``per_reviewer`` (dict mapping reviewer username -> new assignment count).
    """
    if applications is None:
        applications = list(
            OpportunityGrantApplication.objects.filter(
                fin_aid__event_year=event_year,
                status__in=[
                    OpportunityGrantApplication.STATUS_SUBMITTED,
                    OpportunityGrantApplication.STATUS_IN_REVIEW,
                ],
            ).select_related('user')
        )
    else:
        applications = list(applications)

    if reviewers is None:
        reviewers = list(
            FinAidReviewer.objects.filter(is_active=True).select_related('user')
        )
    else:
        reviewers = list(reviewers)

    application_ids = [a.pk for a in applications]
    deleted = 0

    if soft_reassign and application_ids:
        to_delete = FinAidReviewAssignment.objects.filter(
            application_id__in=application_ids,
        ).annotate(
            has_review=Exists(
                FinAidApplicationReview.objects.filter(
                    application=OuterRef('application'),
                    reviewer=OuterRef('reviewer'),
                )
            )
        ).filter(has_review=False)
        deleted, _ = to_delete.delete()

    existing_pairs = set(
        FinAidReviewAssignment.objects.filter(
            application_id__in=application_ids
        ).values_list('reviewer_id', 'application_id')
    )

    new_assignments = []
    per_reviewer_counts = defaultdict(int)

    all_mode_reviewers = [r for r in reviewers if r.review_load == FinAidReviewer.LOAD_ALL]
    equal_mode_reviewers = [r for r in reviewers if r.review_load == FinAidReviewer.LOAD_EQUAL]

    for reviewer in all_mode_reviewers:
        for application in _eligible_applications_for(reviewer, applications):
            pair = (reviewer.id, application.pk)
            if pair in existing_pairs:
                continue
            new_assignments.append(
                FinAidReviewAssignment(
                    reviewer=reviewer,
                    application=application,
                    assigned_by=assigned_by,
                )
            )
            existing_pairs.add(pair)
            per_reviewer_counts[reviewer.user.username] += 1

    unassignable = []
    reviews_target = 0

    if equal_mode_reviewers:
        equal_reviewer_ids = {r.id for r in equal_mode_reviewers}
        reviews_target = _target_reviews_per_application(len(equal_mode_reviewers))

        load_by_reviewer = {r.id: 0 for r in equal_mode_reviewers}
        existing_loads = (
            FinAidReviewAssignment.objects.filter(
                reviewer__in=equal_mode_reviewers,
                application__fin_aid__event_year=event_year,
            )
            .values('reviewer_id')
            .annotate(n=Count('id'))
        )
        for entry in existing_loads:
            load_by_reviewer[entry['reviewer_id']] = entry['n']

        # Build map: application_id → set of equal-reviewer IDs already assigned
        app_to_equal_reviewers = defaultdict(set)
        for r_id, app_id in existing_pairs:
            if r_id in equal_reviewer_ids:
                app_to_equal_reviewers[app_id].add(r_id)

        for application in applications:
            already_assigned = app_to_equal_reviewers[application.pk]
            still_needed = reviews_target - len(already_assigned)

            if still_needed <= 0:
                continue

            candidates = [
                r for r in equal_mode_reviewers
                if r.user_id != application.user_id
                and r.id not in already_assigned
            ]

            if not candidates:
                if not already_assigned:
                    unassignable.append(application.pk)
                continue

            for _ in range(min(still_needed, len(candidates))):
                chosen = min(candidates, key=lambda r: load_by_reviewer[r.id])
                new_assignments.append(
                    FinAidReviewAssignment(
                        reviewer=chosen,
                        application=application,
                        assigned_by=assigned_by,
                    )
                )
                existing_pairs.add((chosen.id, application.pk))
                already_assigned.add(chosen.id)
                load_by_reviewer[chosen.id] += 1
                per_reviewer_counts[chosen.user.username] += 1
                candidates = [r for r in candidates if r.id != chosen.id]

    if new_assignments:
        FinAidReviewAssignment.objects.bulk_create(new_assignments, ignore_conflicts=True)

    return {
        'created': len(new_assignments),
        'deleted': deleted,
        'reviews_per_application': reviews_target,
        'unassignable': unassignable,
        'per_reviewer': dict(per_reviewer_counts),
    }
