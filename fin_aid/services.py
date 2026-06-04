"""Service layer for the fin_aid app.

Provides the opportunity grant review assignment algorithm.
"""

from collections import defaultdict
from typing import Iterable, Optional

from django.db import transaction
from django.db.models import Count

from .models import FinAidReviewAssignment, FinAidReviewer, OpportunityGrantApplication


def _eligible_applications_for(
    reviewer: FinAidReviewer,
    applications: Iterable[OpportunityGrantApplication],
) -> list:
    """Filter out applications submitted by the reviewer themselves."""
    return [a for a in applications if a.user_id != reviewer.user_id]


@transaction.atomic
def assign_applications(
    event_year,
    *,
    applications: Optional[Iterable[OpportunityGrantApplication]] = None,
    reviewers: Optional[Iterable[FinAidReviewer]] = None,
    assigned_by=None,
    reset: bool = False,
) -> dict:
    """Assign opportunity grant applications to reviewers for a given event year.

    Rules:
      * A reviewer is never assigned an application they submitted themselves.
      * Reviewers with ``review_load='all'`` receive every eligible application.
      * Reviewers with ``review_load='equal'`` share the workload via round-robin.
      * Idempotent: existing assignments are preserved unless ``reset=True``.

    Args:
        event_year: ``home.EventYear`` instance the assignment is scoped to.
        applications: Optional explicit queryset/iterable of applications to assign.
            Defaults to all submitted/in-review applications for ``event_year``.
        reviewers: Optional explicit queryset/iterable of reviewers to use.
            Defaults to all active reviewers.
        assigned_by: Optional ``User`` who triggered the assignment (audit trail).
        reset: If True, delete existing assignments for this event year before
            assigning. Use with care.

    Returns:
        dict with keys: ``created`` (int),
        ``unassignable`` (list of application PKs no eligible reviewer could take),
        ``per_reviewer`` (dict mapping reviewer username -> assignment count gained).
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

    if reset:
        FinAidReviewAssignment.objects.filter(
            application__fin_aid__event_year=event_year,
            application_id__in=application_ids,
        ).delete()

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

    if equal_mode_reviewers:
        equal_reviewer_ids = {r.id for r in equal_mode_reviewers}

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

        applications_already_covered = {
            app_id for r_id, app_id in existing_pairs if r_id in equal_reviewer_ids
        }

        unassigned_applications = [
            a for a in applications if a.pk not in applications_already_covered
        ]

        for application in unassigned_applications:
            candidate_reviewers = [
                r for r in equal_mode_reviewers
                if r.user_id != application.user_id
            ]

            if not candidate_reviewers:
                unassignable.append(application.pk)
                continue

            chosen = min(candidate_reviewers, key=lambda r: load_by_reviewer[r.id])

            new_assignments.append(
                FinAidReviewAssignment(
                    reviewer=chosen,
                    application=application,
                    assigned_by=assigned_by,
                )
            )
            existing_pairs.add((chosen.id, application.pk))
            load_by_reviewer[chosen.id] += 1
            per_reviewer_counts[chosen.user.username] += 1

    if new_assignments:
        FinAidReviewAssignment.objects.bulk_create(new_assignments, ignore_conflicts=True)

    return {
        'created': len(new_assignments),
        'unassignable': unassignable,
        'per_reviewer': dict(per_reviewer_counts),
    }
