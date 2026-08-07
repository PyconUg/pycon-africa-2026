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
    STATUS_PARTIAL = STATUS_WAITLIST

    STATUS_CHOICES = (
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_IN_REVIEW, 'In review'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_WAITLIST, 'Partially accepted'),
    )

    USER_RESPONSE_PENDING = 'P'
    USER_RESPONSE_ACCEPTED = 'A'
    USER_RESPONSE_REJECTED = 'R'

    USER_RESPONSE_CHOICES = (
        (USER_RESPONSE_PENDING, 'Pending'),
        (USER_RESPONSE_ACCEPTED, 'Accepted'),
        (USER_RESPONSE_REJECTED, 'Declined'),
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
    user_response = models.CharField(
        max_length=1,
        choices=USER_RESPONSE_CHOICES,
        default=USER_RESPONSE_PENDING,
    )
    ticket_code = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text='Ticket redemption code from Quicket.',
    )
    travel_grant_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text='Travel support amount in USD. Leave blank for ticket-only grants.',
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status_email_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the accept/reject notification email for the current status was last sent successfully.',
    )

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
            models.UniqueConstraint(
                fields=('ticket_code',),
                condition=~models.Q(ticket_code=''),
                name='unique_nonempty_ticket_code',
            ),
        ]

    def __str__(self):
        return f'{self.legal_name} ({self.get_support_type_display()})'

    @property
    def has_travel_grant(self):
        return self.travel_grant_amount is not None and self.travel_grant_amount > 0

    def is_locked_for_applicant_edits(self):
        return self.reviews.exists()


REGIONAL_GRANT_CLOSED = True


def is_regional_grant_closed():
    return REGIONAL_GRANT_CLOSED


REGIONAL_GRANT_COUNTRIES = (
    ('kenya', 'Kenya'),
    ('rwanda', 'Rwanda'),
    ('tanzania', 'Tanzania'),
    ('south_sudan', 'South Sudan'),
    ('other', 'Other'),
)

REGIONAL_GRANT_STATUS_CHOICES = (
    ('student', 'Student'),
    ('employed', 'Employed'),
    ('freelancer', 'Freelancer'),
    ('other', 'Other'),
)

REGIONAL_GRANT_PYTHON_LEVEL_CHOICES = (
    ('beginner', 'Beginner'),
    ('intermediate', 'Intermediate'),
    ('advanced', 'Advanced'),
)

REGIONAL_GRANT_PYTHON_DURATION_CHOICES = (
    ('lt_6m', '< 6 months'),
    ('6_12m', '6–12 months'),
    ('1_2y', '1–2 years'),
    ('2y_plus', '2+ years'),
)

REGIONAL_GRANT_INTEREST_CHOICES = (
    ('ai_ml', 'AI / Machine Learning'),
    ('web_dev', 'Web Development'),
    ('data_science', 'Data Science'),
    ('open_source', 'Open Source'),
    ('devops_cloud', 'DevOps / Cloud'),
)

REGIONAL_GRANT_FINANCIAL_SUPPORT_CHOICES = (
    ('travel', 'Travel'),
    ('accommodation', 'Accommodation'),
    ('conference_ticket', 'Conference Ticket'),
    ('none', 'None'),
)

REGIONAL_GRANT_YES_NO_CHOICES = (
    ('yes', 'Yes'),
    ('no', 'No'),
)

REGIONAL_GRANT_GENDER_CHOICES = (
    ('female', 'Female'),
    ('male', 'Male'),
    ('prefer_not_to_say', 'Prefer not to say'),
)


class RegionalGrantApplication(models.Model):
    """Regional Opportunity Grant application for applicants from neighbouring East African countries.

    Mirrors the public, login-free application form previously hosted on pssu.ug
    (the diversity_applications app), now hosted directly on this site.
    """

    STATUS_SUBMITTED = 'submitted'
    STATUS_REVIEWED = 'reviewed'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = (
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_REVIEWED, 'Reviewed'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
    )

    USER_RESPONSE_PENDING = 'P'
    USER_RESPONSE_ACCEPTED = 'A'
    USER_RESPONSE_REJECTED = 'R'

    USER_RESPONSE_CHOICES = (
        (USER_RESPONSE_PENDING, 'Pending'),
        (USER_RESPONSE_ACCEPTED, 'Accepted'),
        (USER_RESPONSE_REJECTED, 'Declined'),
    )

    country = models.CharField(
        max_length=32,
        choices=REGIONAL_GRANT_COUNTRIES,
        help_text='Country of residence',
    )
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=32)
    city = models.CharField(max_length=255)
    gender = models.CharField(max_length=32, choices=REGIONAL_GRANT_GENDER_CHOICES)
    dob = models.DateField('Date of Birth')
    is_18 = models.BooleanField(
        'I confirm that I am 18 years or older',
        help_text='Applicant must be 18 or older',
    )
    status = models.CharField(
        max_length=32,
        choices=REGIONAL_GRANT_STATUS_CHOICES,
        help_text='Current employment/student status',
    )
    field = models.CharField(
        'Field of study or work',
        max_length=255,
        help_text='Your field of study or professional field',
    )
    python_level = models.CharField(
        max_length=32,
        choices=REGIONAL_GRANT_PYTHON_LEVEL_CHOICES,
        verbose_name='Python proficiency level',
    )
    python_duration = models.CharField(
        max_length=32,
        choices=REGIONAL_GRANT_PYTHON_DURATION_CHOICES,
        verbose_name='How long have you been using Python?',
    )
    why_attend = models.TextField(
        'Why do you want to attend PyCon Africa?',
        help_text='Tell us about your motivation for attending',
    )
    hope_to_gain = models.TextField(
        'What do you hope to gain from the conference?',
        help_text='What skills, knowledge, or connections are you looking for?',
    )
    interests = models.CharField(
        max_length=255,
        verbose_name='Areas of interest (comma-separated)',
        help_text='e.g., AI/ML, Web Development, Data Science, Open Source, DevOps/Cloud',
    )
    community = models.TextField(
        blank=True,
        verbose_name='Are you part of any community or organization?',
        help_text='Optional: Tell us about your involvement in tech communities',
    )
    contributions = models.TextField(
        blank=True,
        verbose_name='How have you contributed to the tech community?',
        help_text='Optional: Open source, mentoring, organizing events, etc.',
    )
    knowledge_sharing = models.TextField(
        blank=True,
        verbose_name='How do you share knowledge with others?',
        help_text='Optional: Blogging, teaching, talks, etc.',
    )
    attend_all = models.BooleanField(
        'I can attend all days of the conference',
        help_text='Confirm your commitment to attend the full conference',
    )
    represent_professionally = models.BooleanField(
        'I will represent the regional grant program professionally',
        help_text='Agree to represent the event and community professionally',
    )
    share_publicly = models.BooleanField(
        'I agree to share my experience publicly',
        help_text='Permission to share your experience on social media, etc.',
    )
    represent_how = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='How will you represent the event?',
        help_text='Optional: Social media, blog posts, presentations, etc.',
    )
    has_national_id = models.BooleanField(
        default=False,
        verbose_name='I have a valid national ID',
        help_text='Confirm you have a national ID',
    )
    has_passport = models.BooleanField(
        default=False,
        verbose_name='I have a valid passport',
        help_text='Confirm you have a valid passport',
    )
    can_travel = models.BooleanField(
        default=False,
        verbose_name='I can obtain travel documents if needed',
        help_text='Confirm you can get travel documents for attending',
    )
    can_cover_expenses_with_ticket = models.CharField(
        max_length=8,
        choices=REGIONAL_GRANT_YES_NO_CHOICES,
        default='yes',
        verbose_name=(
            'If given a to-and-return bus ticket to the event, would you be able '
            'to cover all your other expenses?'
        ),
        help_text='e.g. accommodation, food, and other personal costs',
    )
    can_attend_with_travel_support = models.CharField(
        max_length=8,
        choices=REGIONAL_GRANT_YES_NO_CHOICES,
        default='yes',
        verbose_name='Would you be able to get a conference ticket if given travel support?',
        help_text='Let us know if travel support alone would enable you to attend',
    )
    financial_support = models.CharField(
        max_length=32,
        choices=REGIONAL_GRANT_FINANCIAL_SUPPORT_CHOICES,
        verbose_name='Do you need financial support?',
        help_text='Select the type of support you may need',
    )
    additional_notes = models.TextField(
        blank=True,
        verbose_name='Additional notes',
        help_text='Optional: Additional information about yourself',
    )
    application_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_SUBMITTED,
    )
    user_response = models.CharField(
        max_length=1,
        choices=USER_RESPONSE_CHOICES,
        default=USER_RESPONSE_PENDING,
    )
    proof_of_ticket = models.FileField(
        upload_to='regional_grant_proofs/',
        blank=True,
        null=True,
        help_text='Proof of PyCon Africa conference ticket registration (PDF or image).',
    )
    status_email_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the accept/reject notification email for the current status was last sent successfully.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Regional grant application'
        verbose_name_plural = 'Regional grant applications'

    def __str__(self):
        return f'{self.full_name} ({self.get_country_display()})'

    def get_interests_list(self):
        return [interest.strip() for interest in self.interests.split(',') if interest.strip()]


class RegionalGrantCountryAssignment(models.Model):
    """Manual assignment of a country to a reviewer for Regional Grant review.

    The reviewer can be any user account — not limited to the Opportunity Grant
    reviewer pool (FinAidReviewer) — so any user can be picked for this role.
    """

    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='regional_country_assignments',
    )
    country = models.CharField(max_length=32, choices=REGIONAL_GRANT_COUNTRIES)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='regional_grant_country_assignments_made',
    )

    class Meta:
        verbose_name = 'Regional grant country assignment'
        verbose_name_plural = 'Regional grant country assignments'
        constraints = [
            models.UniqueConstraint(
                fields=('reviewer', 'country'),
                name='unique_regional_grant_country_assignment',
            ),
        ]

    def __str__(self):
        return f'{self.reviewer} → {self.get_country_display()}'


class RegionalGrantReviewAssignment(models.Model):
    """Per-application assignment, independent of RegionalGrantCountryAssignment's per-country grant."""

    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='regional_grant_review_assignments',
    )
    application = models.ForeignKey(
        RegionalGrantApplication,
        on_delete=models.CASCADE,
        related_name='review_assignments',
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='regional_grant_review_assignments_made',
    )

    class Meta:
        verbose_name = 'Regional grant review assignment'
        verbose_name_plural = 'Regional grant review assignments'
        constraints = [
            models.UniqueConstraint(
                fields=('reviewer', 'application'),
                name='unique_regional_grant_review_assignment',
            ),
        ]

    def __str__(self):
        return f'{self.reviewer} → application {self.application_id}'


class RegionalGrantApplicationReview(models.Model):
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

    ALIGNMENT_CHOICES = [(i, str(i)) for i in range(6)]

    application = models.ForeignKey(
        RegionalGrantApplication,
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='regional_grant_application_reviews',
    )
    recommendation = models.CharField(
        max_length=16,
        choices=RECOMMENDATION_CHOICES,
        default=RECOMMEND_UNSURE,
    )
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Scoring: Community & contribution (raw 0-3, weight x3)
    is_community_member = models.BooleanField(default=False, verbose_name='Active in a tech community')
    is_active_contributor = models.BooleanField(default=False, verbose_name='Contributes to the tech community')
    is_knowledge_sharer = models.BooleanField(default=False, verbose_name='Shares knowledge with others')

    # Scoring: Python engagement (reviewer-confirmed, pre-filled from application; weight x2)
    python_level = models.CharField(
        max_length=32,
        choices=REGIONAL_GRANT_PYTHON_LEVEL_CHOICES,
        blank=True,
        default='',
        verbose_name='Python proficiency level (confirm/override)',
    )
    python_duration = models.CharField(
        max_length=32,
        choices=REGIONAL_GRANT_PYTHON_DURATION_CHOICES,
        blank=True,
        default='',
        verbose_name='Python experience duration (confirm/override)',
    )

    # Scoring: Financial need (reviewer-confirmed, pre-filled from application.financial_support; weight x3)
    financial_need = models.CharField(
        max_length=32,
        choices=REGIONAL_GRANT_FINANCIAL_SUPPORT_CHOICES,
        blank=True,
        default='',
        verbose_name='Financial need (confirm/override)',
    )

    # Scoring: Diversity (raw 0-3 booleans, weight x5)
    is_woman = models.BooleanField(default=False, verbose_name='Woman')
    has_disability = models.BooleanField(default=False, verbose_name='Person with disability')
    is_student = models.BooleanField(default=False, verbose_name='Student')

    # Scoring: Alignment (reviewer's holistic 0-5 judgment)
    alignment_score = models.IntegerField(
        choices=ALIGNMENT_CHOICES,
        default=0,
        verbose_name='Alignment score (0–5)',
    )

    # Persisted total score - recomputed on every save()
    total_score = models.FloatField(default=0, editable=False)

    class Meta:
        verbose_name = 'Regional grant application review'
        verbose_name_plural = 'Regional grant application reviews'
        constraints = [
            models.UniqueConstraint(
                fields=('application', 'reviewer'),
                name='unique_regional_grant_application_review_per_reviewer',
            ),
        ]

    def __str__(self):
        return f'Review by {self.reviewer} on regional application {self.application_id}'

    @property
    def community_score(self):
        return sum([self.is_community_member, self.is_active_contributor, self.is_knowledge_sharer]) * 3

    @property
    def python_engagement_score(self):
        level_map = {'beginner': 0, 'intermediate': 1, 'advanced': 2}
        duration_map = {'lt_6m': 0, '6_12m': 1, '1_2y': 2, '2y_plus': 3}
        level = self.python_level or self.application.python_level
        duration = self.python_duration or self.application.python_duration
        return (level_map.get(level, 0) + duration_map.get(duration, 0)) * 2

    @property
    def financial_need_score(self):
        mapping = {'travel': 3, 'accommodation': 2, 'conference_ticket': 1, 'none': 0}
        source = self.financial_need or self.application.financial_support
        return mapping.get(source, 0) * 3

    @property
    def diversity_score(self):
        return sum([self.is_woman, self.has_disability, self.is_student]) * 5

    def save(self, *args, **kwargs):
        self.total_score = (
            self.community_score
            + self.python_engagement_score
            + self.financial_need_score
            + self.diversity_score
            + self.alignment_score
        )
        super().save(*args, **kwargs)


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