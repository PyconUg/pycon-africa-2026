from django.shortcuts import render, get_object_or_404, reverse
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect, HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail, BadHeaderError
from django.core.exceptions import PermissionDenied

from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage, default_storage
from django.shortcuts import render, redirect, HttpResponse
from django.template import loader

from datetime import datetime

from django.utils import timezone
from django.utils.translation import gettext as gettext_fn
from rest_framework import viewsets

from .serializers import TalkSerializer
from .models import *
from .models import Document
from .forms import *
from .forms import ProposalForm
from .mixins import EditOwnTalksMixin
import logging
from django.views.generic import ListView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView 
from django.views.generic import TemplateView, UpdateView, ListView  
from django.contrib.auth.decorators import login_required, permission_required
from talks.decorators import reviewer_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from hitcount.views import HitCountDetailView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from next_prev import next_in_order, prev_in_order
from django.contrib import messages
#Sending html emails to user
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMessage 
from django.http import Http404
from .resources import ProposalResource
from home.models import EventYear   
from registration.models import Profile   
from django.db.models import Avg, F, Q, Count  
from django.contrib.sites.models import Site
from django.utils.text import Truncator


logger = logging.getLogger(__name__)

@login_required
def submit_talk(request, year):
    # Check if the user has a profile
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        return redirect(reverse('profiles:create_profile'))

    try:
        event_year = EventYear.objects.get(year=year)
        submission_periods = CFPSubmissionPeriod.objects.filter(event_year=event_year, submission_type='talks').order_by('start_date')
        active_period = None
        upcoming_period = None

        for period in submission_periods:
            if period.start_date <= timezone.now() <= period.end_date:
                active_period = period
                break
            elif timezone.now() < period.start_date and not upcoming_period:
                upcoming_period = period

        context = {
            'title': 'Submit a Talk',
            'year': year,
            'active_period': active_period,
            'upcoming_period': upcoming_period,
            'is_sponsor_or_keynote': profile.is_a_sponsor_or_keynote_speaker,
        }

        if request.method == "POST":
            if active_period or profile.is_a_sponsor_or_keynote_speaker:
                form = ProposalForm(request.POST, user=request.user)
                if form.is_valid():
                    proposal = form.save(commit=False)
                    proposal.user = request.user
                    proposal.event_year = event_year
                    proposal.save()

                    # Send confirmation email
                    subject = 'Talk Submission Confirmation'
                    html_content = render_to_string('emails/talks/submission_confirmation.html', {'user': request.user, 'proposal': proposal})
                    text_content = strip_tags(html_content)
                    email = EmailMultiAlternatives(subject, text_content, to=[request.user.email])
                    email.attach_alternative(html_content, "text/html")
                    email.send()

                    return redirect(reverse('talks:submitted', kwargs={'year': event_year.year}) + '?type=talk')
                else:
                    logger.debug(f"Form errors: {form.errors}")
                    context['form'] = form
            else:
                context['form'] = ProposalForm(user=request.user)
        else:
            context['form'] = ProposalForm(user=request.user)
            logger.debug("Form added to context for GET request.")

    except EventYear.DoesNotExist:
        return redirect(reverse_lazy('talks:no_event_year_error'))

    template_path = f"{year}/talks/talk_form.html"
    logger.debug(f"Rendering template: {template_path} with context: {context}")
    return render(request, template_path, context)




@login_required
def submit_poster(request, year):
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        return redirect(reverse('profiles:create_profile'))

    try:
        event_year = EventYear.objects.get(year=year)
        poster_periods = CFPSubmissionPeriod.objects.filter(event_year=event_year, submission_type='posters').order_by('start_date')
        active_period = None
        upcoming_period = None

        for period in poster_periods:
            if period.start_date <= timezone.now() <= period.end_date:
                active_period = period
                break
            elif timezone.now() < period.start_date and not upcoming_period:
                upcoming_period = period

        context = {
            'title': 'Submit a Poster',
            'year': year,
            'active_period': active_period,
            'upcoming_period': upcoming_period,
            'is_sponsor_or_keynote': profile.is_a_sponsor_or_keynote_speaker,
        }

        if request.method == 'POST':
            if active_period:
                form = PosterProposalForm(request.POST, request.FILES, user=request.user)
                if form.is_valid():
                    proposal = form.save(commit=False)
                    proposal.user = request.user
                    proposal.event_year = event_year
                    proposal.talk_type = 'Poster'
                    proposal.save()

                    subject = 'Poster Submission Confirmation'
                    html_content = render_to_string('emails/talks/submission_confirmation.html', {'user': request.user, 'proposal': proposal})
                    text_content = strip_tags(html_content)
                    email = EmailMultiAlternatives(subject, text_content, to=[request.user.email])
                    email.attach_alternative(html_content, "text/html")
                    email.send()

                    return redirect(reverse('talks:submitted', kwargs={'year': event_year.year}) + '?type=poster')
                else:
                    logger.debug(f"Poster form errors: {form.errors}")
                    context['form'] = form
            else:
                context['form'] = PosterProposalForm(user=request.user)
        else:
            context['form'] = PosterProposalForm(user=request.user)

    except EventYear.DoesNotExist:
        return redirect(reverse_lazy('talks:no_event_year_error'))

    return render(request, f"{year}/talks/poster_form.html", context)


@login_required
def edit_talk(request, pk, year=None):
    proposal = get_object_or_404(Proposal, pk=pk)
    if year is not None and str(proposal.event_year.year) != str(year):
        raise Http404("Proposal does not exist for the given year.")
    if proposal.user_id != request.user.id and not request.user.is_staff:
        raise Http404("Proposal does not exist.")

    # Authors cannot edit after programme decision or once any review exists.
    if not request.user.is_staff:
        if proposal.status in ('A', 'W', 'R', 'RS') or proposal.reviews.exists():
            raise PermissionDenied(
                "This proposal can no longer be edited once it has reviewer feedback "
                "or a programme decision (accepted, waitlist, or rejected)."
            )

    is_poster = proposal.talk_type == 'Poster'
    FormClass = PosterProposalForm if is_poster else ProposalForm
    template_name = 'edit_poster.html' if is_poster else 'edit_talk.html'

    if request.method == "POST":
        form = FormClass(request.POST, request.FILES, instance=proposal, user=request.user)
        if form.is_valid():
            saved = form.save(commit=False)
            if is_poster:
                saved.talk_type = 'Poster'
                new_file = request.FILES.get('poster_attachment')
                if new_file and proposal.poster_attachment:
                    old_file = proposal.poster_attachment
                    if old_file and default_storage.exists(old_file.name):
                        default_storage.delete(old_file.name)
            saved.save()
            return redirect('talks:talk_list', year=proposal.event_year.year)
    else:
        form = FormClass(instance=proposal, user=request.user)

    template_prefix = f"{proposal.event_year.year}/talks/"
    context = {
        'form': form,
        'year': year,
        'proposal': proposal,
        'is_poster': is_poster,
    }
    return render(request, template_prefix + template_name, context)




class TalkList(TemplateView):
    def get_context_data(self, **kwargs):
        context = super(TalkList, self).get_context_data(**kwargs)
        year = self.kwargs.get('year', timezone.now().year)
        context['year'] = year

        event_year = get_object_or_404(EventYear, year=year)
        submission_periods = CFPSubmissionPeriod.objects.filter(event_year=event_year, submission_type='talks').order_by('start_date')
        poster_periods = CFPSubmissionPeriod.objects.filter(event_year=event_year, submission_type='posters').order_by('start_date')

        active_period = None
        for period in submission_periods:
            if period.start_date <= timezone.now() <= period.end_date:
                active_period = period
                break

        active_poster_period = None
        for period in poster_periods:
            if period.start_date <= timezone.now() <= period.end_date:
                active_poster_period = period
                break

        # Get the user's profile to check if they are a sponsor or keynote speaker
        profile = Profile.objects.get(user=self.request.user)

        context.update({
            'submitted_talks': Proposal.objects.filter(user=self.request.user, event_year__year=year),
            'submission_periods': submission_periods,
            'active_period': active_period,
            'active_poster_period': active_poster_period,
            'is_editable': active_period is not None or active_poster_period is not None or profile.is_a_sponsor_or_keynote_speaker,
            'is_sponsor_or_keynote': profile.is_a_sponsor_or_keynote_speaker
        })

        return context

    def get_template_names(self):
        year = self.kwargs.get('year', timezone.now().year)
        template_path = f"{year}/talks/talk_list.html"
        return [template_path]

    
     
class TalkView(UpdateView):
    form_class = ProposalForm
    model = Proposal
    slug_field = 'slug'

    def get_success_url(self):
        proposal = self.get_object()
        return reverse_lazy('talks:submitted', kwargs={'year': proposal.event_year.year})

    def get_template_names(self):
        proposal = self.get_object()
        return [f"{proposal.event_year.year}/talks/talk.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        proposal = self.get_object()
        context.update({
            'title': "Talk Details",
            'year': proposal.event_year.year,
            'speakers': proposal.speakers.all()  # Include speakers in the context
        })
        return context




def _program_slides_change_mailto(proposal):
    """mailto: link for requesting a materials change after the one allowed self-serve upload."""
    from urllib.parse import quote

    # Programme inbox for slide/material change requests (talk details page).
    program_email = "program@pycon.ug"
    subject = f"Slide update request: {proposal.title}"[:200]
    body = (
        f"Session: {proposal.title}\n"
        f"Proposal ID: {proposal.proposal_id}\n\n"
        "I need the following change to my uploaded materials:\n\n"
    )
    return f"mailto:{program_email}?subject={quote(subject)}&body={quote(body)}"


class TalkDetailView(TemplateView):
    def get_template_names(self):
        proposal = get_object_or_404(Proposal, proposal_id=self.kwargs.get('pk'))
        event_year = proposal.event_year.year
        return [f"{event_year}/talks/talk_details.html"]

    def get_context_data(self, **kwargs):
        bound_form = kwargs.pop('form', None)
        context = super().get_context_data(**kwargs)
        proposal = get_object_or_404(Proposal, proposal_id=self.kwargs.get('pk'))
        submission_periods = CFPSubmissionPeriod.objects.filter(event_year=proposal.event_year, submission_type='talks').order_by('start_date')
        poster_periods = CFPSubmissionPeriod.objects.filter(event_year=proposal.event_year, submission_type='posters').order_by('start_date')

        active_period = None
        for period in submission_periods:
            if period.start_date <= timezone.now() <= period.end_date:
                active_period = period
                break

        active_poster_period = None
        for period in poster_periods:
            if period.start_date <= timezone.now() <= period.end_date:
                active_poster_period = period
                break

        # Determine if the user can upload documents
        can_upload = proposal.status == 'A'
        is_primary_speaker = self.request.user == proposal.user
        is_invited_speaker = self.request.user in proposal.speakers.all()
        can_upload = can_upload and (is_primary_speaker or is_invited_speaker)

        # Slide uploads for this proposal (newest first). Only the latest is shown on 2026 talk details.
        all_slides = list(
            Document.objects.filter(proposal=proposal, document_type='Slide').order_by('-uploaded_at')[:25]
        )
        has_uploaded_slide = bool(all_slides)
        latest_slide = all_slides[0] if all_slides else None
        slide_documents = all_slides[:1]

        doc_form = bound_form
        if doc_form is None:
            doc_form = None if slide_documents else TalkSlideUploadForm(proposal=proposal)

        context.update({
            'title': "Accepted Talks",
            'year': proposal.event_year.year,
            'talk': proposal,
            'speakers': proposal.speakers.all(),
            'submission_periods': submission_periods,
            'active_period': active_period,
            'active_poster_period': active_poster_period,
            'is_editable': active_period is not None or (proposal.talk_type == 'Poster' and active_poster_period is not None),
            'can_upload': can_upload,
            'has_uploaded_slide': has_uploaded_slide,
            'latest_slide': latest_slide,
            'slide_documents': slide_documents,
            'form': doc_form,
            'program_slides_mailto': _program_slides_change_mailto(proposal),
        })
        return context

    def post(self, request, *args, **kwargs):
        proposal = get_object_or_404(Proposal, proposal_id=self.kwargs.get('pk'))
        if Document.objects.filter(proposal=proposal, document_type='Slide').exists():
            messages.warning(
                request,
                gettext_fn(
                    'Materials have already been uploaded for this session. '
                    'To request a change, please contact the program team using the link on this page.'
                ),
            )
            return redirect(
                reverse(
                    'talks:talk_details',
                    kwargs={'year': proposal.event_year.year, 'pk': proposal.proposal_id.hashid},
                )
            )
        form = TalkSlideUploadForm(request.POST, request.FILES, proposal=proposal)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                gettext_fn('Your slides have been uploaded successfully.'),
            )
            return redirect(reverse('talks:talk_details', kwargs={'year': proposal.event_year.year, 'pk': proposal.proposal_id.hashid}))
        # If the form is not valid, re-render the page with form errors
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

class TalksDetailView(DetailView):
    model = Proposal
    context_object_name = 'talk'
    slug_field = 'proposal_id'
    slug_url_kwarg = 'proposal_id'

    def get_template_names(self):
        proposal = self.get_object()
        return [f"{proposal.event_year.year}/schedule/talk_details.html"]

    def get_context_data(self, **kwargs):
        context = super(TalksDetailView, self).get_context_data(**kwargs)
        proposal = self.get_object()

        # Fetch the Profile objects for all speakers (main and additional)
        speakers = [proposal.user] + list(proposal.speakers.all())
        speaker_profiles = Profile.objects.filter(user__in=speakers)

        # Generate the meta tags dynamically
        meta_title = f"{proposal.title} | PyCon Uganda {proposal.event_year.year}"
        meta_description = Truncator(proposal.talk_abstract).words(30, truncate='...') if proposal.talk_abstract else "Join us at PyCon Uganda for an insightful talk."
                
        # todo: find a fallback og image 
        meta_og_image = speaker_profiles.first().profile_image.url if speaker_profiles.exists() and speaker_profiles.first().profile_image else '' 

        context.update({
            'title': "Talk Details",
            'year': proposal.event_year.year,
            'related_talks': Proposal.objects.filter(status='A', event_year=proposal.event_year).order_by('?')[:5],
            'speakers': speaker_profiles,  # Pass Profile objects instead of users
            'meta_title': meta_title,
            'meta_description': meta_description,
            'meta_og_image': meta_og_image,
        })
        return context








class SuccessView(TemplateView):
    def get_template_names(self):
        # Attempt to fetch the event year from URL kwargs
        year = self.kwargs.get('year', timezone.now().year)
        # Verify if the EventYear exists, raise 404 if not
        if not EventYear.objects.filter(year=year).exists():
            raise Http404("Event year does not exist.")
        # Construct the template path using the event year
        return [f"{year}/talks/success.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs.get('year', timezone.now().year)
        submission_type = self.request.GET.get('type', 'talk')
        context['title'] = 'Submission Successful'
        context['year'] = year
        context['submission_type'] = submission_type
        return context


class TalkViewsSets(viewsets.ReadOnlyModelViewSet):
    serializer_class = TalkSerializer
    queryset = Proposal.objects.all()


class AcceptedTalksView(TemplateView):
    template_name = "talks/accepted_talks.html"

    def get_context_data(self, **kwargs):
        context = super(AcceptedTalksView, self).get_context_data(**kwargs)
        context['title'] = "Accepted Talks"
        context['year'] = datetime.now().year
        talks_list = Proposal.objects.filter(status='A').select_related('user')

        paginator = Paginator(talks_list, 10)  # Show 10 posts per page
        page = self.request.GET.get('page')
        try:
            accepted_talks = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            accepted_talks = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            accepted_talks = paginator.page(paginator.num_pages)
        context['accepted_talks'] = accepted_talks
        return context



def export(request):
    proposal_resource = ProposalResource()
    dataset = proposal_resource.export()
    response = HttpResponse(dataset.csv, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="proposals.csv"'
    return response
 


def model_form_upload(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = DocumentForm()
    return render(request, 'model_form_upload.html', {
        'form': form
    })



def home(request):
    documents = Document.objects.all()
    return render(request, 'upload/home.html', { 'documents': documents })
 
def redirect_to_current_year_speaking(request):
    current_year = timezone.now().year
    return redirect('speaking', year=current_year)
 
def redirect_to_current_year_proposing(request):
    current_year = timezone.now().year
    return redirect('proposing', year=current_year)

def redirect_to_current_year_recording(request):
    current_year = timezone.now().year
    return redirect('recording', year=current_year)

def speaking(request, year=None):
    year = year or timezone.now().year
    event_year = get_object_or_404(EventYear, year=year)
    speaks = Speak.objects.filter(event_year=event_year).order_by('-date_created')
    template_name = f'{year}/talks/talks.html'
    return render(request, template_name, {'speaks': speaks, 'event_year': event_year})

def recording(request, year=None):
    year = year or timezone.now().year
    event_year = get_object_or_404(EventYear, year=year)
    recordings = Recording.objects.filter(event_year=event_year).order_by('-date_created')
    template_name = f'{year}/talks/recordings.html'
    return render(request, template_name, {'recordings': recordings, 'event_year': event_year})

def proposing(request, year=None):
    year = year or timezone.now().year
    event_year = get_object_or_404(EventYear, year=year)
    proposing_talks = Proposing_talk.objects.filter(event_year=event_year).order_by('-date_created')
    template_name = f'{year}/talks/proposing_a_talk.html'
    return render(request, template_name, {'proposing_talks': proposing_talks, 'event_year': event_year})
 
 
@login_required
def send_speaker_invitation(request, pk, year=None):
    raise Http404("Co-speaker invitations are no longer available.")
 

@login_required
def accept_invitation(request, pk, year=None):
    proposal = get_object_or_404(Proposal, pk=pk)
    invitation = get_object_or_404(SpeakerInvitation, talk=proposal, invitee=request.user)
    if invitation.status == 'Pending':
        invitation.status = 'Accepted'
        invitation.save()
        proposal.speakers.add(request.user)
        return redirect('profiles:profile_home')
    return redirect('profiles:profile_home')


@login_required
def reject_invitation(request, pk, year=None):
    proposal = get_object_or_404(Proposal, pk=pk)
    invitation = get_object_or_404(SpeakerInvitation, talk=proposal, invitee=request.user)
    if invitation.status == 'Pending':
        invitation.status = 'Rejected'
        invitation.save()
        return redirect('profiles:profile_home')
    return redirect('profiles:profile_home')





@reviewer_required
def list_talks_to_review(request, year):
    try:
        event_year = EventYear.objects.get(year=year)
    except EventYear.DoesNotExist:
        raise Http404("Event year does not exist.")

    try:
        reviewer = Reviewer.objects.get(user=request.user)
        reviewed_talk_ids = list(
            Review.objects.filter(reviewer=reviewer, talk__event_year=event_year)
                          .values_list('talk__proposal_id', flat=True)
        )

        has_any_assignments = reviewer.assignments.filter(proposal__event_year=event_year).exists()

        if has_any_assignments:
            # Show ONLY proposals assigned to this reviewer (excluding ones already reviewed)
            assigned_proposal_ids = list(
                reviewer.assignments
                        .filter(proposal__event_year=event_year)
                        .exclude(proposal__proposal_id__in=reviewed_talk_ids)
                        .values_list('proposal__proposal_id', flat=True)
            )
            talks_awaiting_review = (
                Proposal.objects.filter(proposal_id__in=assigned_proposal_ids)
                                .order_by('talk_type', 'title')
            )
        else:
            # Legacy fallback: reviewer has no assignments yet -> show all unreviewed
            talks_awaiting_review = (
                Proposal.objects.filter(event_year=event_year, status='S')
                                .exclude(proposal_id__in=reviewed_talk_ids)
                                .order_by('talk_type')
            )

        talks_by_type = {}
        for talk in talks_awaiting_review:
            talks_by_type.setdefault(talk.talk_type, []).append(talk)

        # Fetch reviewed talks with their scores
        talks_reviewed_with_scores = []
        for talk_id in reviewed_talk_ids:
            talk = Proposal.objects.get(proposal_id=talk_id)
            avg_score_dict = Review.objects.filter(talk=talk).aggregate(
                avg_speaker_expertise=Avg('sub_scores__speaker_expertise'),
                avg_depth_of_topic=Avg('sub_scores__depth_of_topic'),
                avg_relevancy=Avg('sub_scores__relevancy'),
                avg_value_or_impact=Avg('sub_scores__value_or_impact')
            )
            avg_speaker_expertise = avg_score_dict['avg_speaker_expertise'] or 0
            avg_depth_of_topic = avg_score_dict['avg_depth_of_topic'] or 0
            avg_relevancy = avg_score_dict['avg_relevancy'] or 0
            avg_value_or_impact = avg_score_dict['avg_value_or_impact'] or 0
            avg_score = (avg_speaker_expertise + avg_depth_of_topic + avg_relevancy + avg_value_or_impact) / 4
            talks_reviewed_with_scores.append((talk, avg_score))

        context = {
            'talks_by_type': talks_by_type,
            'talks_reviewed_with_scores': talks_reviewed_with_scores,
            'has_assignments': has_any_assignments,
            'year': year
        }

    except Reviewer.DoesNotExist:
        logger.error(f"Reviewer does not exist for user {request.user}")
        messages.error(request, "You don't yet have rights to review proposals, contact the admin to give you the rights")
        context = {
            'year': year,
            'no_reviewer_rights': True
        }

    return render(request, '2025/talks/reviews/talk_list.html', context)
 
@reviewer_required
def review_talk(request, pk, year=None):
    talk = get_object_or_404(Proposal.objects.select_related('event_year'), pk=pk)
    event_year = talk.event_year
    if year is not None and str(event_year.year) != str(year):
        raise Http404("Proposal does not exist for the given year.")
    year = event_year.year

    reviewer = Reviewer.objects.get(user=request.user)

    # Block reviewers from reviewing proposals they authored or co-speak on.
    if reviewer.user_id == talk.user_id or talk.speakers.filter(id=reviewer.user_id).exists():
        raise PermissionDenied("You cannot review your own proposal.")

    # If assignments exist for this reviewer in this year, restrict review to assigned proposals only.
    # Reviewers without any assignments retain legacy access (back-compat).
    has_assignments = ReviewAssignment.objects.filter(
        reviewer=reviewer, proposal__event_year=event_year
    ).exists()
    if has_assignments:
        is_assigned = ReviewAssignment.objects.filter(reviewer=reviewer, proposal=talk).exists()
        if not is_assigned:
            raise PermissionDenied("This proposal was not assigned to you.")

    already_reviewed = Review.objects.filter(talk=talk, reviewer=reviewer).exists()

    if request.method == 'POST' and not already_reviewed:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.talk = talk
            review.reviewer = reviewer
            review.save()
            # Save sub-scores
            sub_score = SubScore(
                review=review,
                speaker_expertise=form.cleaned_data['speaker_expertise'],
                depth_of_topic=form.cleaned_data['depth_of_topic'],
                relevancy=form.cleaned_data['relevancy'],
                value_or_impact=form.cleaned_data['value_or_impact']
            )
            sub_score.save()
            return redirect(reverse('talks:review_success', kwargs={'year': year}))
    else:
        form = ReviewForm()

    return render(request, '2025/talks/reviews/talk_review.html', {
        'form': form,
        'talk': talk,
        'year': year,
        'already_reviewed': already_reviewed,
    })

@login_required
def review_success(request, year):
    try:
        event_year = EventYear.objects.get(year=year) 
        return render(request, '2025/talks/reviews/review_success.html', {'year': year})
    except EventYear.DoesNotExist:
        return HttpResponse("The specified event year does not exist.", status=404)
     
     

 
@reviewer_required
def reviewed_talks_by_category(request, year):
    try:
        event_year = EventYear.objects.get(year=year)
    except EventYear.DoesNotExist:
        raise Http404("Event year does not exist.")

    category_talks_scores = []
    for category_code, category_label in Proposal.TALK_CATEGORY:
        talks = Proposal.objects.filter(
            event_year=event_year,
            talk_category=category_code,
            reviews__isnull=False
        ).annotate(
            avg_speaker_expertise=Avg('reviews__sub_scores__speaker_expertise'),
            avg_depth_of_topic=Avg('reviews__sub_scores__depth_of_topic'),
            avg_relevancy=Avg('reviews__sub_scores__relevancy'),
            avg_value_or_impact=Avg('reviews__sub_scores__value_or_impact'),
            avg_score=(
                F('avg_speaker_expertise') + F('avg_depth_of_topic') + F('avg_relevancy') + F('avg_value_or_impact')
            ) / 4,
            submission_count=Count('user__proposals', distinct=True)  # Ensure distinct count
        ).order_by('-avg_score')

        # Adding user's name and surname to each talk
        for talk in talks:
            user_profile = Profile.objects.get(user=talk.user)
            talk.user_name = user_profile.name
            talk.user_surname = user_profile.surname

        # Calculate the rank for each talk
        for i, talk in enumerate(talks):
            talk.rank = i + 1

        if talks.exists():
            category_talks_scores.append((category_label, talks))

    return render(request, '2025/talks/reviews/reviewed_talks_by_category.html', {
        'category_talks_scores': category_talks_scores,
        'year': year
    })


@reviewer_required
def reviewed_talks_by_type(request, year):
    try:
        event_year = EventYear.objects.get(year=year)
    except EventYear.DoesNotExist:
        raise Http404("Event year does not exist.")

    type_talks_scores = []
    # Grouping by talk_type and calculating the average score
    for talk_type_code, talk_type_label in Proposal.TALK_TYPES:
        talks = Proposal.objects.filter(
            event_year=event_year,
            talk_type=talk_type_code,
            reviews__isnull=False
        ).annotate(
            avg_speaker_expertise=Avg('reviews__sub_scores__speaker_expertise'),
            avg_depth_of_topic=Avg('reviews__sub_scores__depth_of_topic'),
            avg_relevancy=Avg('reviews__sub_scores__relevancy'),
            avg_value_or_impact=Avg('reviews__sub_scores__value_or_impact'),
            submission_count=Count('user__proposals', distinct=True)  # Ensure distinct count
        ).annotate(
            avg_score=(
                F('avg_speaker_expertise') + F('avg_depth_of_topic') + F('avg_relevancy') + F('avg_value_or_impact')
            ) / 4
        ).order_by('-avg_score')

        # Adding user's name and surname to each talk
        for talk in talks:
            user_profile = Profile.objects.get(user=talk.user)
            talk.user_name = user_profile.name
            talk.user_surname = user_profile.surname

        if talks.exists():
            # Adding rank to each talk
            for rank, talk in enumerate(talks, start=1):
                talk.rank = rank
            type_talks_scores.append((talk_type_label, talks))

    return render(request, '2025/talks/reviews/reviewed_talks_by_type.html', {
        'type_talks_scores': type_talks_scores,
        'year': year
    })

# Class-based
'''
@login_required
@permission_required('reviews.add_review', raise_exception=True) 
class TalksToReviewListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Proposal
    template_name = '2025/talks/reviews/talk_list.html'
    context_object_name = 'talks'
    permission_required = ('talks.view_talk',)  

    def get_queryset(self):
        # Filter talks that are submitted and pending review
        return Proposal.objects.filter(status='Submitted').order_by('-created_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional context if necessary
        return context
     

@login_required
@permission_required('reviews.add_review', raise_exception=True)
class ReviewTalkView(UpdateView):
    model = Review
    form_class = ReviewForm
    template_name = '2025/talks/reviews/talk_review.html'
    context_object_name = 'review'

    def get_object(self, queryset=None):
        talk = get_object_or_404(Proposal, pk=self.kwargs.get('pk'))
        review, created = Review.objects.get_or_create(talk=talk, reviewer=self.request.user)
        return review

    def form_valid(self, form):
        response = super().form_valid(form) 
        return response

    def get_success_url(self):
        return reverse_lazy('reviews:review_list')  # Redirect to the list of talks after submitting a review
'''

@reviewer_required
class TalkReviewDetailView(DetailView):
    model = Proposal
    template_name = '2025/talks/reviews/talk_review_detail.html'
    context_object_name = 'talk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reviews = self.object.reviews.all()
        context['reviews'] = reviews
        if reviews.exists():
            context['average_score'] = reviews.aggregate(Avg('score'))['score__avg']
            context['is_accepted'] = context['average_score'] >= 4  # Example criteria (I will have to chnage this)
        return context



def simple_upload(request):
    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)
        return render(request, 'upload/simple_upload.html', {
            'uploaded_file_url': uploaded_file_url
        })
    return render(request, 'upload/simple_upload.html')


def model_form_upload(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = DocumentForm()
    return render(request, 'upload/model_form_upload.html', {
        'form': form
    })




 
@login_required
def respond_to_invitation(request, pk, year=None):
    """Accept/decline invitation.

    ``year`` is present when this view is mounted under ``<int:year>/talks/`` (generic
    year routes). It is omitted under ``pycon2026`` URLs (``/2026/talks/...``), where the
    parent URLconf does not pass captured kwargs into the included ``talks`` patterns.
    """
    proposal = get_object_or_404(
        Proposal.objects.select_related("event_year"),
        pk=pk,
    )
    event_year = proposal.event_year
    if year is not None and event_year.year != year:
        raise Http404()

    if proposal.user_id != request.user.id:
        raise PermissionDenied(
            "This invitation link is tied to the account that submitted the proposal. "
            "Sign in with the same account the acceptance email was sent to (do not forward the link). "
            "If you are unsure which account to use, contact program@pycon.ug."
        )

    if request.method == 'POST':
        form = ProposalResponseForm(request.POST, instance=proposal)
        if form.is_valid():
            user_response = form.cleaned_data.get('user_response', '')

            if user_response == 'A':
                proposal.user_response = 'A'
                proposal.status = 'A'
            elif user_response == 'R':
                proposal.user_response = 'R'
                proposal.status = 'RS'

            proposal.save()

            site = Site.objects.get_current()
            domain = site.domain
            talk_url = f"https://{domain}{reverse('talks:talk_details', kwargs={'year': event_year.year, 'pk': proposal.proposal_id.hashid})}"

            try:
                user_profile = Profile.objects.get(user=proposal.user)
                full_name = user_profile.get_full_name()
            except Profile.DoesNotExist:
                full_name = (
                    proposal.user.get_full_name() or proposal.user.get_username()
                )

            subject = ""
            html_template = ""
            if proposal.user_response == 'A':
                subject = "Thank You for Accepting to Speak at PyCon Africa 2026"
                html_template = 'emails/talks/accepted_response.html'
            elif proposal.user_response == 'R':
                subject = "Thank You for Your Response"
                html_template = 'emails/talks/rejected_response.html'

            if html_template:
                html_content = render_to_string(html_template, {
                    'proposal': proposal,
                    'full_name': full_name,
                    'talk_url': talk_url,
                })
                text_content = strip_tags(html_content)
                from_addr = (
                    f"PyCon Africa 2026 Programme Team <{settings.DEFAULT_FROM_EMAIL}>"
                    if settings.DEFAULT_FROM_EMAIL
                    else None
                )
                if from_addr and proposal.user.email:
                    email = EmailMultiAlternatives(
                        subject,
                        text_content,
                        from_addr,
                        [proposal.user.email],
                    )
                    email.attach_alternative(html_content, "text/html")
                    try:
                        email.send(fail_silently=False)
                    except Exception:
                        logger.exception(
                            "respond_to_invitation: failed to send email to %s",
                            proposal.user.email,
                        )
                        messages.warning(
                            request,
                            "Your response was saved, but we could not send the confirmation "
                            "email. If this keeps happening, contact the programme team.",
                        )
                elif not from_addr:
                    logger.warning(
                        "respond_to_invitation: DEFAULT_FROM_EMAIL not set; skipping email"
                    )

            messages.success(request, 'Your response has been recorded.')
            return redirect('talks:talk_details', year=event_year.year, pk=proposal.proposal_id.hashid)
    else:
        form = ProposalResponseForm(instance=proposal)

    template_path = f'{event_year.year}/talks/proposal_response_form.html'
    return render(request, template_path, {'form': form, 'proposal': proposal})
