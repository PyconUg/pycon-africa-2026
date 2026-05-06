"""Service layer for the talks app.

Currently provides the proposal review assignment algorithm.
"""

from talks.models import Reviewer


from collections import defaultdict
from typing import Iterable, Optional

from django.db import transaction
from django.db.models import Count

from .models import Proposal, ReviewAssignment, Reviewer


def _proposal_speaker_user_ids(proposal: Proposal) -> set:
    """Return the set of user IDs that authored or are co-speakers on a proposal."""
    speaker_ids = set(proposal.speakers.values_list('id', flat=True))
    speaker_ids.add(proposal.user_id)
    return speaker_ids


def _eligible_proposals_for(reviewer: Reviewer, proposals: Iterable[Proposal]) -> list:
    """Filter proposals so the reviewer never gets one they authored or co-speak on."""
    eligible = []
    for proposal in proposals:
        if reviewer.user_id in _proposal_speaker_user_ids(proposal):
            continue
        eligible.append(proposal)
    return eligible


@transaction.atomic
def assign_proposals(
    event_year,
    *,
    proposals: Optional[Iterable[Proposal]] = None,
    reviewers: Optional[Iterable[Reviewer]] = None,
    assigned_by=None,
    reset: bool = False,
) -> dict:
    """Assign proposals to reviewers for a given event year.

    Rules:
      * A reviewer is never assigned a proposal they authored or co-speak on.
      * Reviewers with ``review_load='all'`` receive every eligible proposal.
      * Reviewers with ``review_load='equal'`` share the workload via round-robin.
      * Idempotent: existing assignments are preserved unless ``reset=True``.

    Args:
        event_year: ``home.EventYear`` instance the assignment is scoped to.
        proposals: Optional explicit queryset/iterable of proposals to assign.
            Defaults to all submitted proposals for ``event_year``.
        reviewers: Optional explicit queryset/iterable of reviewers to use.
            Defaults to all active reviewers.
        assigned_by: Optional ``User`` who triggered the assignment (audit trail).
        reset: If True, delete existing assignments for this event year before
            assigning. Use with care.

    Returns:
        dict with keys: ``created`` (int), ``skipped`` (int),
        ``unassignable`` (list of proposal IDs that no eligible reviewer could take),
        ``per_reviewer`` (dict mapping reviewer username -> assignment count gained).
    """
    if proposals is None:
        proposals = list(
            Proposal.objects.filter(event_year=event_year, status='S')
            .select_related('user')
            .prefetch_related('speakers')
        )
    else:
        proposals = list(proposals)

    if reviewers is None:
        reviewers = list(
            Reviewer.objects.filter(is_active=True).select_related('user')
        )
    else:
        reviewers = list[Reviewer](reviewers)

    proposal_ids = [p.proposal_id for p in proposals]

    if reset:
        ReviewAssignment.objects.filter(
            proposal__event_year=event_year,
            proposal__proposal_id__in=proposal_ids,
        ).delete()

    existing_pairs = set(
        ReviewAssignment.objects.filter(
            proposal__proposal_id__in=proposal_ids
        ).values_list('reviewer_id', 'proposal_id')
    )

    new_assignments = []
    per_reviewer_counts = defaultdict(int)

    all_mode_reviewers = [r for r in reviewers if r.review_load == 'all']
    equal_mode_reviewers = [r for r in reviewers if r.review_load == 'equal']

    for reviewer in all_mode_reviewers:
        for proposal in _eligible_proposals_for(reviewer, proposals):
            pair = (reviewer.id, proposal.proposal_id)
            if pair in existing_pairs:
                continue
            new_assignments.append(
                ReviewAssignment(
                    reviewer=reviewer,
                    proposal=proposal,
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
            ReviewAssignment.objects.filter(
                reviewer__in=equal_mode_reviewers,
                proposal__event_year=event_year,
            )
            .values('reviewer_id')
            .annotate(n=Count('id'))
        )
        for entry in existing_loads:
            load_by_reviewer[entry['reviewer_id']] = entry['n']

        proposals_already_covered_by_equal = {
            p_id for r_id, p_id in existing_pairs if r_id in equal_reviewer_ids
        }

        unassigned_proposals = [
            p for p in proposals
            if p.proposal_id not in proposals_already_covered_by_equal
        ]

        for proposal in unassigned_proposals:
            forbidden_user_ids = _proposal_speaker_user_ids(proposal)
            candidate_reviewers = [
                r for r in equal_mode_reviewers
                if r.user_id not in forbidden_user_ids
            ]

            if not candidate_reviewers:
                unassignable.append(proposal.proposal_id)
                continue

            chosen = min(candidate_reviewers, key=lambda r: load_by_reviewer[r.id])

            new_assignments.append(
                ReviewAssignment(
                    reviewer=chosen,
                    proposal=proposal,
                    assigned_by=assigned_by,
                )
            )
            existing_pairs.add((chosen.id, proposal.proposal_id))
            load_by_reviewer[chosen.id] += 1
            per_reviewer_counts[chosen.user.username] += 1

    if new_assignments:
        ReviewAssignment.objects.bulk_create(new_assignments, ignore_conflicts=True)

    return {
        'created': len(new_assignments),
        'skipped': 0,
        'unassignable': unassignable,
        'per_reviewer': dict(per_reviewer_counts),
    }
