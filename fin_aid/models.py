from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.utils.formats import date_format
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

    def format_window_datetime(self, dt):
        """Format an application window time in project local time (EAT)."""
        return f"{date_format(timezone.localtime(dt), 'j F Y, H:i')} (EAT)"

    def get_form_status_message(self):
        if self.is_form_not_open_yet():
            return "The financial aid application form will open on {}".format(
                self.format_window_datetime(self.fin_open_date),
            )
        elif self.is_form_closed():
            return "The financial aid application form closed on {}".format(
                self.format_window_datetime(self.fin_close_date),
            )
        else:
            return "The financial aid application form is currently open."


class FinAidReviewer(models.Model):
    LOAD_ALL = 'all'
    LOAD_EQUAL = 'equal'
    REVIEW_LOAD_CHOICES = (
        (LOAD_ALL, 'All — review every application'),
        (LOAD_EQUAL, 'Equal — fair share via round-robin'),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fin_aid_reviewer_profile',
    )
    review_load = models.CharField(
        max_length=16,
        choices=REVIEW_LOAD_CHOICES,
        default=LOAD_EQUAL,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Opportunity grant reviewer'
        verbose_name_plural = 'Opportunity grant reviewers'

    def __str__(self):
        return self.user.get_username()


class FinAidReviewAssignment(models.Model):
    reviewer = models.ForeignKey(
        FinAidReviewer,
        on_delete=models.CASCADE,
        related_name='assignments',
    )
    application = models.ForeignKey(
        'OpportunityGrantApplication',
        on_delete=models.CASCADE,
        related_name='review_assignments',
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fin_aid_assignments_made',
    )

    class Meta:
        verbose_name = 'Opportunity grant review assignment'
        verbose_name_plural = 'Opportunity grant review assignments'
        constraints = [
            models.UniqueConstraint(
                fields=('reviewer', 'application'),
                name='unique_fin_aid_review_assignment',
            ),
        ]

    def __str__(self):
        return f'{self.reviewer} → application {self.application_id}'


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


class FinAidApplicationReview(models.Model):
    RECOMMEND_ACCEPT = 'accept'
    RECOMMEND_PARTIAL = 'partial'
    RECOMMEND_REJECT = 'reject'
    RECOMMEND_UNSURE = 'unsure'

    RECOMMENDATION_CHOICES = (
        (RECOMMEND_ACCEPT, 'Accept / fund'),
        (RECOMMEND_PARTIAL, 'Partial grant'),
        (RECOMMEND_REJECT, 'Reject'),
        (RECOMMEND_UNSURE, 'Unsure / needs discussion'),
    )

    REGION_UGANDA = 'uganda'
    REGION_EAST_AFRICA = 'east_africa'
    REGION_OTHER_AFRICA = 'other_africa'
    REGION_OUTSIDE_AFRICA = 'outside_africa'

    REGION_CHOICES = (
        (REGION_UGANDA, 'Uganda'),
        (REGION_EAST_AFRICA, 'East Africa (not Uganda)'),
        (REGION_OTHER_AFRICA, 'Other Africa'),
        (REGION_OUTSIDE_AFRICA, 'Outside Africa'),
    )

    ALIGNMENT_CHOICES = [(i, str(i)) for i in range(6)]

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

    # Scoring: Impactful contributors (raw 0-3, weight ×3)
    is_speaker = models.BooleanField(default=False, verbose_name='Speaker')
    is_organizer = models.BooleanField(default=False, verbose_name='Organizer')
    is_local_contributor = models.BooleanField(default=False, verbose_name='Local contributor')

    # Scoring: Regional attendee (raw 0-1, weight ×3)
    region = models.CharField(
        max_length=20,
        choices=REGION_CHOICES,
        blank=True,
        default='',
        verbose_name='Region',
    )

    # Scoring: Diversity (raw 0-4.5, weight ×5)
    is_woman = models.BooleanField(default=False, verbose_name='Woman')
    is_professional_cant_afford = models.BooleanField(
        default=False, verbose_name='Professional who cannot afford to attend'
    )
    has_disability = models.BooleanField(default=False, verbose_name='Person with disability')
    is_motivated_student = models.BooleanField(default=False, verbose_name='Motivated student')
    is_student = models.BooleanField(default=False, verbose_name='Student')

    # Scoring: Alignment (0–5)
    alignment_score = models.IntegerField(
        choices=ALIGNMENT_CHOICES,
        default=0,
        verbose_name='Alignment score (0–5)',
    )

    # Persisted total score — computed and stored on every save() (float due to 0.5 student score)
    total_score = models.FloatField(default=0, editable=False)

    # Amount by which the applicant's budget request exceeds the regional flight cap (USD)
    amount_exceeded = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Amount exceeded (USD)',
        help_text='How much the applicant\'s requested budget exceeds the regional flight cap, in USD.',
    )

    # Scoring: Grant type (reviewer-confirmed, pre-filled from application)
    grant_type = models.CharField(
        max_length=32,
        choices=OpportunityGrantApplication.SUPPORT_TYPE_CHOICES,
        blank=True,
        default='',
        verbose_name='Grant type',
    )

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

    @property
    def contributor_score(self):
        return sum([self.is_speaker, self.is_organizer, self.is_local_contributor]) * 3

    @property
    def regional_score(self):
        return {
            self.REGION_UGANDA: 3,
            self.REGION_EAST_AFRICA: 2,
            self.REGION_OTHER_AFRICA: 1,
            self.REGION_OUTSIDE_AFRICA: 0,
        }.get(self.region, 0)

    @property
    def diversity_score(self):
        if self.is_motivated_student:
            student_raw = 1
        elif self.is_student:
            student_raw = 0.5
        else:
            student_raw = 0
        raw = (
            (1 if self.is_woman else 0)
            + (1 if self.is_professional_cant_afford else 0)
            + (1 if self.has_disability else 0)
            + student_raw
        )
        return raw * 5

    @property
    def grant_type_score(self):
        mapping = {
            OpportunityGrantApplication.SUPPORT_TICKET: 3,
            OpportunityGrantApplication.SUPPORT_ACCOMMODATION: 2,
            OpportunityGrantApplication.SUPPORT_TRAVEL: 1,
            OpportunityGrantApplication.SUPPORT_OTHER: 0,
        }
        source = self.grant_type if self.grant_type else self.application.support_type
        return mapping.get(source, 0)

    def save(self, *args, **kwargs):
        self.total_score = (
            self.contributor_score
            + self.regional_score
            + self.diversity_score
            + self.alignment_score
            + self.grant_type_score
        )
        super().save(*args, **kwargs)