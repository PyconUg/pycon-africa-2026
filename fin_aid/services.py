"""Service layer for the fin_aid app.

Provides the opportunity grant review assignment algorithm and the lookup that
flags regional grant applicants who already hold an opportunity grant.
"""

from collections import defaultdict
from typing import Iterable, Optional

from django.db import transaction
from django.db.models import Count, Exists, OuterRef
from django.db.models.functions import Lower, Trim

from .models import (
    FinAidApplicationReview,
    FinAidReviewAssignment,
    FinAidReviewer,
    OpportunityGrantApplication,
    RegionalGrantApplication,
    RegionalGrantApplicationReview,
    RegionalGrantReviewAssignment,
)


#: An opportunity grant counts as awarded once it is accepted, in full or in part.
AWARDED_OPPORTUNITY_GRANT_STATUSES = (
    OpportunityGrantApplication.STATUS_ACCEPTED,
    OpportunityGrantApplication.STATUS_WAITLIST,
)


def _normalise_email(email: Optional[str]) -> str:
    return (email or '').strip().lower()


def opportunity_grant_awards_by_email(emails: Iterable[str]) -> dict:
    """Map normalised email -> the applicant's awarded opportunity grant.

    Awarded means accepted or partially accepted. Only emails present in
    ``emails`` are returned. Emails are compared with an explicit
    Lower(Trim(...)) rather than ``__iexact``, which stays case-insensitive
    regardless of database collation and avoids ``__iexact`` compiling to LIKE
    on SQLite (where "_" and "%" would act as wildcards). When someone has been
    awarded in more than one round, the latest wins.
    """
    wanted = {_normalise_email(email) for email in emails}
    wanted.discard('')
    if not wanted:
        return {}

    awarded = (
        OpportunityGrantApplication.objects.annotate(
            _grantee_email=Lower(Trim('user__email')),
        )
        .filter(
            _grantee_email__in=wanted,
            status__in=AWARDED_OPPORTUNITY_GRANT_STATUSES,
        )
        .select_related('user', 'fin_aid__event_year')
        .order_by('submitted_at')
    )

    return {application._grantee_email: application for application in awarded}


def attach_opportunity_grant_awards(applications: Iterable) -> list:
    """Set ``opportunity_grant_award`` on each regional grant application.

    Regional grant applications need no login, so the applicant's email address
    is the only link back to an opportunity grant application. The attribute is
    ``None`` when the applicant holds no awarded opportunity grant.
    """
    applications = list(applications)
    awards = opportunity_grant_awards_by_email(a.email for a in applications)
    for application in applications:
        application.opportunity_grant_award = awards.get(_normalise_email(application.email))
    return applications


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


@transaction.atomic
def assign_regional_grant_reviews(
    reviewer,
    count,
    *,
    countries: Optional[Iterable[str]] = None,
    assigned_by=None,
) -> dict:
    """Give ``reviewer`` a lot of ``count`` applications total (target, not an increment), independent of RegionalGrantCountryAssignment.

    ``count`` is scoped to ``countries`` when given: it's the target among those
    countries specifically, not the reviewer's global total across all countries.

    Candidates are ordered by existing assignment count (fewest first) to spread load evenly.
    """
    already_assigned_ids = RegionalGrantReviewAssignment.objects.filter(
        reviewer=reviewer,
    ).values_list('application_id', flat=True)

    if countries is not None:
        current_total = RegionalGrantReviewAssignment.objects.filter(
            reviewer=reviewer, application__country__in=list(countries),
        ).count()
    else:
        current_total = len(already_assigned_ids)
    needed = count - current_total

    if needed <= 0:
        return {'created': 0, 'assigned_application_ids': [], 'available': 0, 'current_total': current_total}

    already_reviewed_ids = RegionalGrantApplicationReview.objects.filter(
        reviewer=reviewer,
    ).values_list('application_id', flat=True)

    candidate_qs = RegionalGrantApplication.objects.exclude(
        pk__in=already_reviewed_ids,
    ).exclude(
        pk__in=already_assigned_ids,
    )
    if countries is not None:
        candidate_qs = candidate_qs.filter(country__in=list(countries))

    candidates = list(
        candidate_qs.annotate(
            _assignment_count=Count('review_assignments'),
        ).order_by('_assignment_count', 'created_at')
    )

    chosen = candidates[:needed]

    new_assignments = [
        RegionalGrantReviewAssignment(
            reviewer=reviewer,
            application=application,
            assigned_by=assigned_by,
        )
        for application in chosen
    ]
    if new_assignments:
        RegionalGrantReviewAssignment.objects.bulk_create(new_assignments, ignore_conflicts=True)

    return {
        'created': len(new_assignments),
        'assigned_application_ids': [a.pk for a in chosen],
        'available': len(candidates),
        'current_total': current_total + len(new_assignments),
    }
