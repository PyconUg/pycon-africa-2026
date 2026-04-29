from django.shortcuts import render, get_object_or_404, reverse
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect, HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail, BadHeaderError

from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect, HttpResponse
from django.template import loader

from datetime import datetime

from django.utils import timezone
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
        submission_periods = CFPSubmissionPeriod.objects.filter(event_year=event_year).order_by('start_date')
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

                    return redirect('talks:submitted', year=event_year.year)
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
def edit_talk(request, year, pk):
    proposal = get_object_or_404(Proposal, pk=pk)
    if str(proposal.event_year.year) != str(year):
        raise Http404("Proposal does not exist for the given year.")
    
    if request.method == "POST":
        form = ProposalForm(request.POST, instance=proposal)
        if form.is_valid():
            form.save()
            return redirect('talks:talk_list', year=proposal.event_year.year)
    else:
        form = ProposalForm(instance=proposal)
    
    template_prefix = f"{proposal.event_year.year}/talks/"
    context = {
        'form': form,
        'year': year,
        'proposal': proposal,  # Add the proposal to the context
    }
    return render(request, template_prefix + 'edit_talk.html', context)




class TalkList(TemplateView):
    def get_context_data(self, **kwargs):
        context = super(TalkList, self).get_context_data(**kwargs)
        year = self.kwargs.get('year', timezone.now().year)
        context['year'] = year

        event_year = get_object_or_404(EventYear, year=year)
        submission_periods = CFPSubmissionPeriod.objects.filter(event_year=event_year).order_by('start_date')

        active_period = None
        for period in submission_periods:
            if period.start_date <= timezone.now() <= period.end_date:
                active_period = period
                break

        # Get the user's profile to check if they are a sponsor or keynote speaker
        profile = Profile.objects.get(user=self.request.user)

        context.update({
            'submitted_talks': Proposal.objects.filter(user=self.request.user, event_year__year=year),
            'submission_periods': submission_periods,
            'active_period': active_period,
            'is_editable': active_period is not None or profile.is_a_sponsor_or_keynote_speaker,
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




class TalkDetailView(TemplateView):
    def get_template_names(self):
        proposal = get_object_or_404(Proposal, proposal_id=self.kwargs.get('pk'))
        event_year = proposal.event_year.year
        return [f"{event_year}/talks/talk_details.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        proposal = get_object_or_404(Proposal, proposal_id=self.kwargs.get('pk'))
        submission_periods = CFPSubmissionPeriod.objects.filter(event_year=proposal.event_year).order_by('start_date')

        active_period = None
        for period in submission_periods:
            if period.start_date <= timezone.now() <= period.end_date:
                active_period = period
                break

        # Determine if the user can upload documents
        can_upload = proposal.status == 'A'
        is_primary_speaker = self.request.user == proposal.user
        is_invited_speaker = self.request.user in proposal.speakers.all()
        can_upload = can_upload and (is_primary_speaker or is_invited_speaker)

        # Check if a slide has already been uploaded
        uploaded_documents = Document.objects.filter(proposal=proposal, document_type='Slide')
        has_uploaded_slide = uploaded_documents.exists()
        latest_slide = uploaded_documents.latest('uploaded_at') if has_uploaded_slide else None

        # Add the form to the context
        context.update({
            'title': "Accepted Talks",
            'year': proposal.event_year.year,
            'talk': proposal,
            'speakers': proposal.speakers.all(),
            'submission_periods': submission_periods,
            'active_period': active_period,
            'is_editable': active_period is not None,
            'can_upload': can_upload,
            'has_uploaded_slide': has_uploaded_slide,
            'latest_slide': latest_slide,
            'form': DocumentForm(proposal=proposal),  # Pass the proposal instance
        })
        return context

    def post(self, request, *args, **kwargs):
        proposal = get_object_or_404(Proposal, proposal_id=self.kwargs.get('pk'))
        form = DocumentForm(request.POST, request.FILES, proposal=proposal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your slides have been uploaded successfully.')
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
        # Assuming 'year' is passed as a URL parameter, otherwise default to the current year
        year = self.kwargs.get('year', timezone.now().year)
        context['title'] = 'Talk Submission Successful'
        context['year'] = year
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
def send_speaker_invitation(request, year, pk):
    if request.method == 'POST':
        user_email = request.POST.get('user_email')
        event_year = get_object_or_404(EventYear, year=year)
        proposal = get_object_or_404(Proposal, pk=pk, event_year=event_year)
        user = get_object_or_404(User, email=user_email)
        sender_name = request.user.get_full_name() or request.user.username  
        invitation, created = SpeakerInvitation.objects.get_or_create(talk=proposal, invitee=user)

        if created:
            email_body = f"Dear Speaker,\n\nYou have been invited by {sender_name} to join a session titled '{proposal.title}' during PyCon Africa 2026.\n\nPlease visit our site (https://africa.pycon.org/) to respond to this invitation.\n\nBest,\nPyCon Africa 2026 Team"
            send_mail(
                f'Invitation to Speak at PyCon Africa 2026 - {proposal.title}',
                email_body,
                'noreply@pycon.ug',
                [user_email],
                fail_silently=False,
            ) 
        return redirect('talks:talk_details', year=year, pk=pk)
    else:
        # Handle the case for GET request or show an error message
        return render(request, '2025/talks/speaker_invite_error.html', {'error': 'This action requires a POST request.'})
 

@login_required
def accept_invitation(request, year, pk): 
    proposal = get_object_or_404(Proposal, pk=pk) 
    invitation = get_object_or_404(SpeakerInvitation, talk=proposal, invitee=request.user)
    if invitation.status == 'Pending':
        invitation.status = 'Accepted'
        invitation.save()
        proposal.speakers.add(request.user) 
        return redirect('profiles:profile_home')

@login_required
def reject_invitation(request, year, pk):
    proposal = get_object_or_404(Proposal, pk=pk)
    invitation = get_object_or_404(SpeakerInvitation, talk=proposal, invitee=request.user)
    if invitation.status == 'Pending':
        invitation.status = 'Rejected'
        invitation.save()
        return redirect('profiles:profile_home')





@reviewer_required
def list_talks_to_review(request, year):
    try:
        event_year = EventYear.objects.get(year=year)
    except EventYear.DoesNotExist:
        raise Http404("Event year does not exist.")

    try:
        reviewer = Reviewer.objects.get(user=request.user)
        # Fetch all reviews by this reviewer for talks in this event year
        reviewed_talk_ids = Review.objects.filter(reviewer=reviewer, talk__event_year=event_year).values_list('talk__proposal_id', flat=True)
        # Filter out talks that have been reviewed by this reviewer
        talks_awaiting_review = Proposal.objects.filter(event_year=event_year, status='S').exclude(proposal_id__in=reviewed_talk_ids).order_by('talk_type')

        # Group talks by talk type
        talks_by_type = {}
        for talk in talks_awaiting_review:
            if talk.talk_type not in talks_by_type:
                talks_by_type[talk.talk_type] = []
            talks_by_type[talk.talk_type].append(talk)

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
def review_talk(request, year, pk):
    event_year = get_object_or_404(EventYear, year=year)
    talk = get_object_or_404(Proposal, pk=pk, event_year=event_year)
    
    reviewer = Reviewer.objects.get(user=request.user)
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
def respond_to_invitation(request, year, pk):
    # Get the event year and proposal based on the provided year and proposal ID
    event_year = get_object_or_404(EventYear, year=year)
    proposal = get_object_or_404(Proposal, pk=pk, event_year=event_year)

    if request.method == 'POST':
        form = ProposalResponseForm(request.POST, instance=proposal)
        if form.is_valid():
            # Determine the user's response
            user_response = form.cleaned_data.get('user_response', '')

            # Update the proposal's status and user_response based on the user's response
            if user_response == 'A':
                proposal.user_response = 'A'
                proposal.status = 'A'  # Set status to 'Accepted' if it wasn't set before
            elif user_response == 'R':
                proposal.user_response = 'R'
                proposal.status = 'RS'  # Set status to 'Rejected by Speaker'
            
            proposal.save()  # Save the updated proposal

            # Get the current site domain
            site = Site.objects.get_current()
            domain = site.domain

            # Generate the URL to the talk detail page
            talk_url = f"https://{domain}{reverse('talks:talk_details', kwargs={'year': year, 'pk': proposal.proposal_id.hashid})}"

            # Send appropriate email based on user response
            subject = ""
            html_template = ""
            
            if proposal.user_response == 'A':
                subject = "Thank You for Accepting to Speak at PyCon Africa 2026"
                html_template = 'emails/talks/accepted_response.html'
            elif proposal.user_response == 'R':
                subject = "Thank You for Your Response"
                html_template = 'emails/talks/rejected_response.html'
            
            html_content = render_to_string(html_template, {
                'proposal': proposal,
                'full_name': Profile.objects.get(user=proposal.user).get_full_name(),
                'talk_url': talk_url,  # Include talk_url in context
            })
            text_content = strip_tags(html_content)
            email = EmailMultiAlternatives(
                subject,
                text_content,
                'PyCon Africa 2026 Programme Team <program@pycon.ug>',
                [proposal.user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()

            messages.success(request, 'Your response has been recorded.')
            # Redirect to the talk details page with the correct year
            return redirect('talks:talk_details', year=event_year.year, pk=proposal.pk)
    else:
        form = ProposalResponseForm(instance=proposal)

    template_path = f'{event_year.year}/talks/proposal_response_form.html'
    return render(request, template_path, {'form': form, 'proposal': proposal})
