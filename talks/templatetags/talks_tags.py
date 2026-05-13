from django import template
from django.utils import timezone
from talks.models import *
from home.models import EventYear 

register = template.Library()

@register.inclusion_tag('2025/talks/user_talks_summary.html')
def user_talks_summary(user):
    # Attempt to find the current or next CFP period
    current_year = timezone.now().year
    event_year = EventYear.objects.filter(year=current_year).first()
    submission_period = None
    if event_year:
        submission_periods = CFPSubmissionPeriod.objects.filter(event_year=event_year).order_by('start_date')
        submission_period = next((period for period in submission_periods if period.start_date <= timezone.now() <= period.end_date), None)
        if not submission_period:
            submission_period = next((period for period in submission_periods if period.start_date > timezone.now()), None)
    
    # Fetch the first 2 or 3 submitted talks for the user
    submitted_talks = Proposal.objects.filter(user=user).order_by('-created_date')[:3]
    invited_talks = Proposal.objects.filter(speakers=user).distinct().order_by('-created_date')[:3]


    return {
        'submitted_talks': submitted_talks,
        'invited_talks': invited_talks,
        'active_period': submission_period is not None and submission_period.start_date <= timezone.now() <= submission_period.end_date,
        'upcoming_period': submission_period and submission_period.start_date > timezone.now(),
        'event_year': event_year
    }

 

@register.inclusion_tag('2026/talks/invitation_list.html', takes_context=True)
def invitation_list(context):
    request = context['request']
    invitations = SpeakerInvitation.objects.filter(invitee=request.user, status='Pending')
    return {'invitations': invitations}