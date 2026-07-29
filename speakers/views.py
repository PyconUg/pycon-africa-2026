import re

from os import name
from urllib import request
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.models import User
from django.views.generic import ListView
from django.template import RequestContext
from django.views.generic.detail import DetailView
from .forms import SpeakerForm
from django.shortcuts import get_object_or_404
from hitcount.views import HitCountDetailView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from next_prev import next_in_order, prev_in_order
from django.utils.text import Truncator
from registration.models import Profile 
from talks.models import Proposal
from conference_schedule.models import Schedule

from home.models import EventYear  
from event.models import Event 
from django.db.models import Q, F, Exists, OuterRef, Case, When, IntegerField
 
 
class Speakers(ListView):
    model = Profile
    context_object_name = 'speakers'

    def get_template_names(self):
        year = self.kwargs.get('year', 'default')
        return [f'{year}/speakers/speaker_list.html']

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter speakers based on accepted proposals and user response
        queryset = queryset.filter(
            Q(user__proposals__status='A', user__proposals__user_response='A') |
            Q(user__speaking_proposals__status='A', user__speaking_proposals__user_response='A')
        ).annotate(
            is_keynote_speaker=Exists(
                Proposal.objects.filter(
                    user=OuterRef('user'),
                    talk_type="Keynote Speaker",
                    status='A',
                    user_response='A'
                )
            ),
            sort_priority=Case(
                When(user__proposals__talk_type="Sponsored Talk", then=1),
                When(user__proposals__talk_type__in=["Short Talk", "Long Talk"], then=2),
                When(user__proposals__talk_type="Lightning Talk", then=3),
                default=4,
                output_field=IntegerField(),
            )
        ).order_by('sort_priority', 'user', 'date_created')

        # Remove duplicate speakers
        seen_users = set()
        unique_speakers = []
        for speaker in queryset:
            if speaker.user_id not in seen_users:
                seen_users.add(speaker.user_id)
                unique_speakers.append(speaker)

        return unique_speakers

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        speakers = context['speakers']
        keynote_speakers = [speaker for speaker in speakers if speaker.is_keynote_speaker]
        other_speakers = [speaker for speaker in speakers if not speaker.is_keynote_speaker]

        # Meta Information
        meta_description = "Meet the incredible speakers at PyCon Uganda. From keynotes to sponsored talks, our speakers bring a wealth of knowledge and insight to the stage."
        meta_title = f"Speakers at PyCon Uganda {self.kwargs.get('year', 'default')}" if keynote_speakers else f"Speakers at PyCon Uganda {self.kwargs.get('year', 'default')}"

        context.update({
            'keynote_speakers': keynote_speakers,
            'other_speakers': other_speakers,
            'meta_title': meta_title,
            'meta_description': meta_description,
        })
        return context




class SpeakerDetailView(HitCountDetailView):
    model = Profile
    context_object_name = 'speaker'
    slug_field = 'profile_id'
    pk_url_kwarg = 'profile_id'
    count_hit = True

    def get_template_names(self):
        year = self.kwargs.get('year', 'default')
        return [f'{year}/speakers/speaker_details.html']

    def get_context_data(self, **kwargs):
        context = super(SpeakerDetailView, self).get_context_data(**kwargs)
        year = self.kwargs.get('year')
        event_year = get_object_or_404(EventYear, year=year)

        # Get accepted talks for the speaker
        talks = Proposal.objects.filter(user=self.object.user, status="A", event_year=event_year)

        # Collect related speakers without duplication
        related_speakers = Profile.objects.filter( 
            user__proposals__status='A',  
            user__proposals__event_year=event_year
        ).annotate(
            user_accepted=Exists(
                Proposal.objects.filter(
                    user=OuterRef('user'),
                    user_response='A',
                    status='A',
                    event_year=event_year
                )
            )
        ).filter(user_accepted=True).exclude(profile_id=self.object.profile_id).distinct()

        # Other accepted talks (with their speaker) to feature in the sidebar
        other_talks = Proposal.objects.filter(
            status='A',
            user_response='A',
            event_year=event_year,
        ).exclude(user=self.object.user).select_related('user__user_profile')[:5]

        # Truncate biography to 30 words
        truncated_biography = Truncator(self.object.biography).words(50, truncate='...')

        # Meta tags information
        meta_title = f"{self.object.name} {self.object.surname} | PyCon Uganda {year}"
        meta_description = f"Meet {self.object.name}, a speaker at PyCon Uganda {year}. {truncated_biography}"
        meta_author = "PyCon Uganda"

        # todo: find a fallback og image 
        meta_og_image = self.object.profile_image.url if self.object.profile_image else ""

        context.update({
            'talks': talks,
            'related_speakers': related_speakers,
            'other_talks': other_talks,
            'events': Event.objects.all(),
            'speakers': Profile.objects.filter(is_visible=True),
            'schedule': Schedule.objects.all(),
            'meta_title': meta_title,
            'meta_description': meta_description,
            'meta_author': meta_author,
            'meta_og_image': meta_og_image,
        })
        return context


def _normalize_name(value):
    value = re.sub(r"[_\-]+", " ", value.strip().lower())
    return re.sub(r"\s+", " ", value)


def speaker_search(request, year):
    """Look up a Profile by full name (e.g. from a schedule speaker label) and
    send the visitor to their canonical speaker detail page."""
    query = request.GET.get('name', '').strip()
    target = _normalize_name(query) if query else ''

    match = None
    if target:
        confirmed_speakers = Profile.objects.filter(
            Q(user__proposals__status='A', user__proposals__user_response='A') |
            Q(user__speaking_proposals__status='A', user__speaking_proposals__user_response='A')
        ).distinct()
        for profile in confirmed_speakers:
            if _normalize_name(profile.get_full_name()) == target:
                match = profile
                break

    if match:
        return redirect('speakers:speaker_detail', year=year, profile_id=match.profile_id)

    return render(
        request,
        f'{year}/speakers/speaker_not_found.html',
        {'name': query},
        status=404,
    )