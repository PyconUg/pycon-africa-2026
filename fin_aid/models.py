from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django_countries.fields import CountryField
from home.models import EventYear


class Fin_aid(models.Model):
    title = models.CharField(max_length=250, null=False, blank=False, help_text='Financial Assistance PyCon Uganda')
    event_year = models.ForeignKey(EventYear, on_delete=models.CASCADE, default="2025", related_name='fin_aids')
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    fin_open_date = models.DateTimeField(help_text='Date and time when the financial aid form opens', null=False, blank=False, default=timezone.now)
    fin_close_date = models.DateTimeField(help_text='Date and time when the financial aid form closes', null=False, blank=False, default=timezone.now)

    class Meta:
        verbose_name = 'Opportunity grant configuration'
        verbose_name_plural = 'Opportunity grant configurations'
        permissions = [
            ("can_edit_fin_aid", "Can edit financial aid form"),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("fin_aid_detail", kwargs={"pk": self.pk})

    def is_form_open(self):
        now = timezone.now()
        return self.fin_open_date <= now <= self.fin_close_date

    def is_form_closed(self):
        now = timezone.now()
        return now > self.fin_close_date

    def is_form_not_open_yet(self):
        now = timezone.now()
        return now < self.fin_open_date

    def get_form_status_message(self):
        if self.is_form_not_open_yet():
            return "The financial aid application form will open on {}".format(self.fin_open_date.strftime("%Y-%m-%d %H:%M:%S"))
        elif self.is_form_closed():
            return "The financial aid application form closed on {}".format(self.fin_close_date.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            return "The financial aid application form is currently open."


class FinAidReviewer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fin_aid_reviewer_profile',
    )

    class Meta:
        verbose_name = 'Opportunity grant reviewer'
        verbose_name_plural = 'Opportunity grant reviewers'

    def __str__(self):
        return self.user.get_username()


class OpportunityGrantApplication(models.Model):
    SUPPORT_TRAVEL = 'travel'
    SUPPORT_ACCOMMODATION = 'accommodation'
    SUPPORT_TICKET = 'ticket'
    SUPPORT_OTHER = 'other'

    SUPPORT_TYPE_CHOICES = (
        (SUPPORT_TRAVEL, 'Travel'),
        (SUPPORT_ACCOMMODATION, 'Accommodation'),
        (SUPPORT_TICKET, 'Conference ticket'),
        (SUPPORT_OTHER, 'Other / combination'),
    )

    STATUS_SUBMITTED = 'submitted'
    STATUS_IN_REVIEW = 'in_review'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_WAITLIST = 'waitlist'

    STATUS_CHOICES = (
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_IN_REVIEW, 'In review'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_WAITLIST, 'Waitlist'),
    )

    fin_aid = models.ForeignKey(
        Fin_aid,
        on_delete=models.CASCADE,
        related_name='applications',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='opportunity_grant_applications',
    )
    legal_name = models.CharField(max_length=255, help_text='Name as it should appear on correspondence.')
    country = CountryField('Country', blank_label='(select country)')
    support_type = models.CharField(max_length=32, choices=SUPPORT_TYPE_CHOICES)
    budget_narrative = models.TextField(
        help_text='Describe estimated costs or how funds would be used.',
    )
    why_need_support = models.TextField(
        help_text='Why are you applying for an opportunity grant?',
    )
    community_contribution = models.TextField(
        help_text='How do you contribute to the Python or broader tech community?',
    )
    additional_notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_SUBMITTED,
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Opportunity grant application'
        verbose_name_plural = 'Opportunity grant applications'
        permissions = [
            (
                'can_review_fin_aid_application',
                'Can review opportunity grant applications',
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=('fin_aid', 'user'),
                name='unique_opportunity_grant_application_per_user_round',
            ),
        ]

    def __str__(self):
        return f'{self.legal_name} ({self.get_support_type_display()})'

    def is_locked_for_applicant_edits(self):
        return self.reviews.exists()

    def get_review_summary(self):
        """Return a dict with counts of each recommendation type."""
        reviews = self.reviews.all()
        summary = {
            'accept': 0,
            'reject': 0,
            'unsure': 0,
            'total': reviews.count(),
        }
        for review in reviews:
            summary[review.recommendation] += 1
        return summary

    def get_suggested_status(self):
        """Suggest a status based on review consensus."""
        summary = self.get_review_summary()
        total = summary['total']
        if total == 0:
            return self.STATUS_IN_REVIEW
        
        accept_count = summary['accept']
        reject_count = summary['reject']
        
        # If majority accept, suggest accepted
        if accept_count > reject_count and accept_count > total / 2:
            return self.STATUS_ACCEPTED
        # If any reject, suggest rejected (strict)
        elif reject_count > 0:
            return self.STATUS_REJECTED
    def get_suggested_status_display(self):
        """Return the display name for the suggested status."""
        return dict(self.STATUS_CHOICES)[self.get_suggested_status()]


class FinAidApplicationReview(models.Model):
    RECOMMEND_ACCEPT = 'accept'
    RECOMMEND_REJECT = 'reject'
    RECOMMEND_UNSURE = 'unsure'

    RECOMMENDATION_CHOICES = (
        (RECOMMEND_ACCEPT, 'Accept / fund'),
        (RECOMMEND_REJECT, 'Reject'),
        (RECOMMEND_UNSURE, 'Unsure / needs discussion'),
    )

    application = models.ForeignKey(
        OpportunityGrantApplication,
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    reviewer = models.ForeignKey(
        FinAidReviewer,
        on_delete=models.CASCADE,
        related_name='application_reviews',
    )
    recommendation = models.CharField(
        max_length=16,
        choices=RECOMMENDATION_CHOICES,
        default=RECOMMEND_UNSURE,
    )
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Opportunity grant application review'
        verbose_name_plural = 'Opportunity grant application reviews'
        constraints = [
            models.UniqueConstraint(
                fields=('application', 'reviewer'),
                name='unique_fin_aid_application_review_per_reviewer',
            ),
        ]

    def __str__(self):
        return f'Review by {self.reviewer} on application {self.application_id}'