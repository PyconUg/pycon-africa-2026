import operator
from collections import OrderedDict

from django.shortcuts import render, get_object_or_404, redirect 
from django.contrib import messages
from django.db.models import Q, Count 
from django.template import RequestContext
from django.views.generic.detail import DetailView
from django.views.generic import (
    DetailView,
    ListView,
)
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from functools import reduce


from django.contrib.auth.models import User
from datetime import datetime  
from django.contrib.auth import authenticate, login, get_user_model 
from django.views.generic.edit import UpdateView
from django.views.generic.base import TemplateView
from django.urls import reverse_lazy
from django.views import generic
from django.http import HttpResponseRedirect 

from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import get_template
from django.urls import reverse
from django.utils.translation import gettext as _
from .models import (
    Fin_aid,
    FinAidReviewer,
    FinAidApplicationReview,
    OpportunityGrantApplication,
)
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from home.models import EventYear

from django.contrib.auth.mixins import PermissionRequiredMixin
from .email_notifications import send_opportunity_grant_submission_confirmation
from .forms import Fin_aidForm, OpportunityGrantApplicationForm, FinAidApplicationReviewForm


def _public_fin_aid_url(year):
    if year == 2026:
        return reverse('pycon2026:fin_aid')
    return reverse('fin_aid:fin_aid', kwargs={'year': year})


def _fin_aid_reviews_list_url(year):
    if year == 2026:
        return reverse('pycon2026:fin_aid_reviews')
    return reverse('fin_aid:fin_aid_reviews', kwargs={'year': year})


def _fin_aid_review_success_url(year):
    if year == 2026:
        return reverse('pycon2026:fin_aid_review_success')
    return reverse('fin_aid:fin_aid_review_success', kwargs={'year': year})


def _fin_aid_my_application_url(year):
    if year == 2026:
        return reverse('pycon2026:fin_aid_my_application')
    return reverse('fin_aid:fin_aid_my_application', kwargs={'year': year})


def _fin_aid_application_edit_url(year):
    if year == 2026:
        return reverse('pycon2026:fin_aid_application_edit')
    return reverse('fin_aid:fin_aid_application_edit', kwargs={'year': year})


def _fin_aid_apply_url(year):
    if year == 2026:
        return reverse('pycon2026:fin_aid_apply')
    return reverse('fin_aid:fin_aid_apply', kwargs={'year': year})


def _fin_aid_for_event_year(event_year):
    return Fin_aid.objects.filter(event_year=event_year).order_by('-date_created').first()


def _fin_aid_subpage_template(year, basename):
    path = f'{year}/fin_aid/{basename}'
    try:
        get_template(path)
        return path
    except TemplateDoesNotExist:
        return f'2026/fin_aid/{basename}'


def fin_aid(request, year):
    event_year = get_object_or_404(EventYear, year=year)
    fin_aids = Fin_aid.objects.filter(event_year=event_year).order_by('-date_created')
    for fin_aid in fin_aids:
        fin_aid.is_open = fin_aid.is_form_open()
        fin_aid.is_closed = fin_aid.is_form_closed()
        fin_aid.not_open_yet = fin_aid.is_form_not_open_yet()
        fin_aid.form_status_message = fin_aid.get_form_status_message()
    is_fin_aid_reviewer = (
        request.user.is_authenticated
        and FinAidReviewer.objects.filter(user=request.user).exists()
    )
    fin_round = _fin_aid_for_event_year(event_year)
    user_og_application = None
    if request.user.is_authenticated and fin_round is not None:
        user_og_application = OpportunityGrantApplication.objects.filter(
            fin_aid=fin_round,
            user=request.user,
        ).first()
    has_opportunity_grant_application = user_og_application is not None
    can_edit_opportunity_grant_application = (
        user_og_application is not None
        and fin_round is not None
        and fin_round.is_form_open()
        and not user_og_application.is_locked_for_applicant_edits()
    )
    return render(
        request,
        f'{year}/fin_aid/fin_aid.html',
        {
            'fin_aids': fin_aids,
            'year': year,
            'is_fin_aid_reviewer': is_fin_aid_reviewer,
            'has_opportunity_grant_application': has_opportunity_grant_application,
            'can_edit_opportunity_grant_application': can_edit_opportunity_grant_application,
        },
    )

@login_required
def fin_aid_edit(request, year, pk):
    fin_aid = get_object_or_404(Fin_aid, pk=pk)
    if not request.user.has_perm('fin_aid.can_edit_fin_aid'):
        return redirect('fin_aid', year=year)
    if request.method == "POST":
        form = Fin_aidForm(request.POST, instance=fin_aid)
        if form.is_valid():
            form.save()
            return redirect('fin_aid', year=year)
    else:
        form = Fin_aidForm(instance=fin_aid)
    return render(request, f'{year}/fin_aid/update_fin_aid.html', {'form': form, 'year': year})

class Fin_aidView(PermissionRequiredMixin, UpdateView):
    form_class = Fin_aidForm
    model = Fin_aid
    template_name = "fin_aid/update_fin_aid.html"
    permission_required = 'fin_aid.can_edit_fin_aid'

    def get_success_url(self):
        return reverse_lazy('fin_aid', kwargs={'year': self.object.event_year.year})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Fin_aid'
        context['year'] = timezone.now().year
        context['fin_aid'] = self.object
        context['is_open'] = self.object.is_form_open()
        context['is_closed'] = self.object.is_form_closed()
        context['not_open_yet'] = self.object.is_form_not_open_yet()
        context['form_status_message'] = self.object.get_form_status_message()
        return context

@login_required
def fin_aid_update_view(request, year, id):
    obj = get_object_or_404(Fin_aid, id=id)
    if not request.user.has_perm('fin_aid.can_edit_fin_aid'):
        return redirect('fin_aid', year=year)
    if request.method == "POST":
        form = Fin_aidForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('fin_aid', year=year)
    else:
        form = Fin_aidForm(instance=obj)
    context = {
        'form': form,
        'is_open': obj.is_form_open(),
        'is_closed': obj.is_form_closed(),
        'not_open_yet': obj.is_form_not_open_yet(),
        'form_status_message': obj.get_form_status_message(),
        'year': year
    }
    return render(request, f'{year}/fin_aid/update_fin_aid.html', context)


@login_required
def fin_aid_apply(request, year):
    event_year = get_object_or_404(EventYear, year=year)
    fin_aid_obj = _fin_aid_for_event_year(event_year)
    template = _fin_aid_subpage_template(year, 'apply.html')

    if not fin_aid_obj:
        return render(
            request,
            template,
            {'year': year, 'no_program': True},
        )

    existing = OpportunityGrantApplication.objects.filter(
        fin_aid=fin_aid_obj,
        user=request.user,
    ).first()
    if existing:
        return redirect(_fin_aid_my_application_url(year))

    if not fin_aid_obj.is_form_open():
        return render(
            request,
            template,
            {
                'year': year,
                'applications_closed': True,
                'fin_aid_obj': fin_aid_obj,
            },
        )

    if request.method == 'POST':
        form = OpportunityGrantApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.fin_aid = fin_aid_obj
            application.user = request.user
            application.save()
            send_opportunity_grant_submission_confirmation(
                application,
                request,
                year,
            )
            messages.success(
                request,
                _('Thank you. Your opportunity grant application has been submitted.'),
            )
            return redirect(_fin_aid_my_application_url(year))
    else:
        form = OpportunityGrantApplicationForm()

    return render(
        request,
        template,
        {
            'year': year,
            'form': form,
            'fin_aid_obj': fin_aid_obj,
        },
    )


@login_required
def fin_aid_my_application(request, year):
    event_year = get_object_or_404(EventYear, year=year)
    fin_aid_obj = _fin_aid_for_event_year(event_year)
    template = _fin_aid_subpage_template(year, 'my_application.html')

    if not fin_aid_obj:
        messages.info(
            request,
            _('There is no active opportunity grant program for this event year yet.'),
        )
        return redirect(_public_fin_aid_url(year))

    application = (
        OpportunityGrantApplication.objects.filter(
            fin_aid=fin_aid_obj,
            user=request.user,
        )
        .select_related('fin_aid', 'fin_aid__event_year')
        .first()
    )
    if not application:
        messages.info(
            request,
            _('You have not submitted an application for this round yet.'),
        )
        return redirect(_fin_aid_apply_url(year))

    locked_by_review = application.is_locked_for_applicant_edits()
    can_edit = fin_aid_obj.is_form_open() and not locked_by_review
    return render(
        request,
        template,
        {
            'year': year,
            'application': application,
            'fin_aid_obj': fin_aid_obj,
            'can_edit': can_edit,
            'locked_by_review': locked_by_review,
        },
    )


@login_required
def fin_aid_application_edit(request, year):
    event_year = get_object_or_404(EventYear, year=year)
    fin_aid_obj = _fin_aid_for_event_year(event_year)
    template = _fin_aid_subpage_template(year, 'application_edit.html')

    if not fin_aid_obj:
        return redirect(_public_fin_aid_url(year))

    application = OpportunityGrantApplication.objects.filter(
        fin_aid=fin_aid_obj,
        user=request.user,
    ).first()
    if not application:
        return redirect(_fin_aid_apply_url(year))

    if application.is_locked_for_applicant_edits():
        messages.info(
            request,
            _('Your application is under review and can no longer be edited.'),
        )
        return redirect(_fin_aid_my_application_url(year))

    if not fin_aid_obj.is_form_open():
        messages.warning(
            request,
            _(
                'The application period has closed. You can view your submission but not change it.'
            ),
        )
        return redirect(_fin_aid_my_application_url(year))

    if request.method == 'POST':
        form = OpportunityGrantApplicationForm(
            request.POST,
            instance=application,
        )
        if form.is_valid():
            form.save()
            messages.success(request, _('Your application has been updated.'))
            return redirect(_fin_aid_my_application_url(year))
    else:
        form = OpportunityGrantApplicationForm(
            instance=application,
        )

    return render(
        request,
        template,
        {
            'year': year,
            'form': form,
            'application': application,
            'fin_aid_obj': fin_aid_obj,
        },
    )


@login_required
def fin_aid_review_success(request, year):
    get_object_or_404(EventYear, year=year)
    template = _fin_aid_subpage_template(year, 'review_success.html')
    return render(request, template, {'year': year})


@login_required
def fin_aid_reviews_list(request, year):
    event_year = get_object_or_404(EventYear, year=year)
    template = _fin_aid_subpage_template(year, 'reviews_list.html')

    try:
        reviewer = FinAidReviewer.objects.get(user=request.user)
    except FinAidReviewer.DoesNotExist:
        messages.error(
            request,
            'You are not registered as an opportunity grant reviewer. Contact an administrator if you need access.',
        )
        return render(
            request,
            template,
            {'year': year, 'no_reviewer_rights': True},
        )

    fin_aids = Fin_aid.objects.filter(event_year=event_year)
    applications = OpportunityGrantApplication.objects.filter(
        fin_aid__in=fin_aids,
    ).select_related('user', 'fin_aid').annotate(
        review_count=Count('reviews')
    )

    reviewed_ids = set(
        FinAidApplicationReview.objects.filter(reviewer=reviewer).values_list(
            'application_id',
            flat=True,
        )
    )
    awaiting = [a for a in applications if a.pk not in reviewed_ids]
    reviewed = [a for a in applications if a.pk in reviewed_ids]
    # Sort awaiting by review_count ascending (fewest reviews first), then by submitted_at descending
    awaiting.sort(key=lambda a: (a.review_count, -a.submitted_at.timestamp()))
    reviewed.sort(key=lambda a: a.submitted_at, reverse=True)

    applications_by_support_type = OrderedDict()
    for _code, label in OpportunityGrantApplication.SUPPORT_TYPE_CHOICES:
        applications_by_support_type[label] = []
    for app in awaiting:
        applications_by_support_type[app.get_support_type_display()].append(app)
    applications_by_support_type = OrderedDict(
        (k, v) for k, v in applications_by_support_type.items() if v
    )

    review_by_app_id = {
        r.application_id: r
        for r in FinAidApplicationReview.objects.filter(
            reviewer=reviewer,
            application__in=applications,
        ).select_related('application')
    }
    reviewed_with_reviews = [(app, review_by_app_id[app.pk]) for app in reviewed]

    return render(
        request,
        template,
        {
            'year': year,
            'awaiting': awaiting,
            'reviewed': reviewed,
            'reviewed_ids': reviewed_ids,
            'applications_by_support_type': applications_by_support_type,
            'reviewed_with_reviews': reviewed_with_reviews,
        },
    )


@login_required
def fin_aid_review_detail(request, year, pk):
    event_year = get_object_or_404(EventYear, year=year)
    application = get_object_or_404(
        OpportunityGrantApplication.objects.select_related('user', 'fin_aid'),
        pk=pk,
        fin_aid__event_year=event_year,
    )
    template = _fin_aid_subpage_template(year, 'review_detail.html')

    try:
        reviewer = FinAidReviewer.objects.get(user=request.user)
    except FinAidReviewer.DoesNotExist:
        return render(
            request,
            template,
            {'year': year, 'no_reviewer_rights': True},
        )

    existing_review = FinAidApplicationReview.objects.filter(
        application=application,
        reviewer=reviewer,
    ).first()
    already_reviewed = existing_review is not None

    if request.method == 'POST' and not already_reviewed:
        form = FinAidApplicationReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.application = application
            review.reviewer = reviewer
            review.save()
            return redirect(_fin_aid_review_success_url(year))
    else:
        form = FinAidApplicationReviewForm()

    return render(
        request,
        template,
        {
            'year': year,
            'application': application,
            'form': form,
            'already_reviewed': already_reviewed,
            'existing_review': existing_review,
        },
    )