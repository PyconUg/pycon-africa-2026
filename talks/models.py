from django.db import models
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import User
from markdownx.models import MarkdownxField 
from django.utils import timezone
from  embed_video.fields  import  EmbedVideoField
from django.core.exceptions import ValidationError
from hashids import Hashids
from django.conf import settings 
from hashid_field import HashidAutoField
from hashid_field import HashidField 
from home.models import EventYear
 
 
class CFPSubmissionPeriod(models.Model):
    SUBMISSION_TYPES = (
        ('talks', 'Talks & Workshops'),
        ('posters', 'Posters'),
    )

    event_year = models.ForeignKey(EventYear, on_delete=models.CASCADE, default="2025", related_name='submission_periods', help_text="The event year this submission period is for")
    start_date = models.DateTimeField(help_text="Date and time when proposal submissions start")
    end_date = models.DateTimeField(help_text="Date and time when proposal submissions end")
    submission_type = models.CharField(max_length=20, choices=SUBMISSION_TYPES, default='talks', help_text="Type of submission this period covers")

    def __str__(self):
        return f"{self.get_submission_type_display()} Submission Period for {self.event_year.year}"

    def is_active(self):
        """Check if the submission period is currently active."""
        now = timezone.now()
        return self.start_date <= now <= self.end_date
    

class Speak(models.Model):
    title =  models.CharField(max_length=250, null=False, blank=False, help_text='Speak at PyCon Uganda') 
    content = MarkdownxField(default='', help_text = "[Supports Markdown] - Content for speaking at PyCon Uganda.", null=False, blank=False
                             )
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='speak',default=User) 
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    event_year = models.ForeignKey(EventYear, on_delete=models.CASCADE, default="2025", related_name='speaks')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("speak")
 
 

class Proposing_talk(models.Model):
    title =  models.CharField(max_length=250, null=False, blank=False, help_text='Speak at PyCon Uganda') 
    content = MarkdownxField(default='', help_text = "[Supports Markdown] - Content.", null=False, blank=False
                             )
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='proposing_talk',default=User) 
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True) 
    event_year = models.ForeignKey(EventYear, on_delete=models.CASCADE, default="2025", related_name='proposing_talks')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("proposing_talk")
 
 

class Recording(models.Model):
    title =  models.CharField(max_length=250, null=False, blank=False, help_text='Recording GL at PyCon Uganda') 
    content = MarkdownxField(default='', help_text = "[Supports Markdown] - Content.", null=False, blank=False
                             )
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='recording',default=User) 
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    event_year = models.ForeignKey(EventYear, on_delete=models.CASCADE, default="2025", related_name='recordings')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("recording")
 

class Proposal(models.Model):
    TALK_TYPES = (
        ('Lightning Talk', "Lightning Talk - 5 mins"),
        ('Short Talk', "Short Talk - 30 mins"),
        ('Long Talk', "Long Talk - 45 mins"),
        ('Tutorial', "Tutorial - 2 hours"),
        ('Poster', "Poster"),
        ('Sponsored Talk', "Sponsored Talk"),
        ('Keynote Speaker', "Keynote Speaker"),
    )

    TALK_CATEGORY = (
        ('GP / Web', "General Python, Web/DevOps"),
        ('GC', "General Community"),
        ('ET', "Emerging Technologies"),
        ('Education', "Education"),
        ('O', "Other"),
    )

    STATUS = (
        ('S', 'Submitted'),
        ('A', 'Accepted'),
        ('W', 'Waiting List'),
        ('R', 'Rejected'),
        ('RS', 'Rejected by Speaker'), 
    )

    PROGRAMMING_EXPERIENCE = (
        ('BGN-L', 'Beginner Level'),
        ('INT-L', 'Intermediate Level'),
        ('EXP-L', 'Expert Level'),
        ('GEN-L', 'General'),
    )
 
    USER_RESPONSE_CHOICES = [
        ('P', 'Pending'),   
        ('A', 'Accepted'),
        ('R', 'Rejected'),
    ]
    
    title = models.CharField(max_length=1024, help_text="Public title. What topic/project is it all about?")
    talk_type = models.CharField(max_length=50, choices=TALK_TYPES)
    talk_category = models.CharField(max_length=50, choices=TALK_CATEGORY)
    proposal_id = HashidAutoField(primary_key=True, salt=f"talks_proposal{settings.HASHID_FIELD_SALT}", default=None)
    
    elevator_pitch = MarkdownxField(blank=True, null=True, help_text="[Supports Markdown] - Describe your Talk to your targeted audience.")
    talk_abstract = MarkdownxField(blank=True, null=True, help_text="[Supports Markdown] - Your talk_abstract.")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="proposals", on_delete=models.CASCADE)
    status = models.CharField(max_length=2, choices=STATUS, default='S')
    intended_audience = models.CharField(max_length=50, choices=PROGRAMMING_EXPERIENCE, blank=True, null=True)
    link_to_preview_video_url = models.URLField(blank=True, help_text='Link to Preview video on your Youtube or Google drive')
    anything_else_you_want_to_tell_us = MarkdownxField(blank=True, null=True, help_text="Kindly add anything else you want to tell us?")
    special_requirements = MarkdownxField(blank=True, null=True, help_text="If you have any special requirements such as needing travel assistance, accessibility needs, or anything else please let us know here so that we may plan accordingly. (This is not made public nor will the review committee have access to view it.)")
    recording_release = models.BooleanField(default=True, help_text="By submitting your talk proposal, you agree to give permission to the conference organizers to record, edit, and release audio and/or video of your presentation. If you do not agree to this, please uncheck this box.")
    poster_attachment = models.FileField(upload_to='poster_attachments/', blank=True, null=True, help_text="Upload a PDF, PPT, or image of your poster (optional but recommended).")
    youtube_video_url = models.URLField(blank=True, help_text='Link to Talk on youtube Video')
    youtube_iframe_url = models.URLField(max_length=300, blank=True, help_text='Link to Youtube Iframe')
    speakers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='speaking_proposals', blank=True)
    event_year = models.ForeignKey(EventYear, on_delete=models.CASCADE, default="", related_name='proposals', help_text="The event year this proposal is for")
    user_response = models.CharField(
        max_length=1,
        choices=USER_RESPONSE_CHOICES,
        default='P',
        help_text="User's response to the invitation to present their proposal."
    )
    created_date = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("talk_list") 
   
    def average_review_score(self):
        reviews = self.reviews.all()
        if not reviews.exists():
            return 0  # or handle the case where there are no reviews
        total_score = sum(review.average_score() for review in reviews)
        return total_score / reviews.count()


class SpeakerInvitation(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    )
    talk = models.ForeignKey('Proposal', related_name='invitations', on_delete=models.CASCADE)
    invitee = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='talk_invitations', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    invitation_sent = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Invitation to {self.invitee.email} for {self.talk.title}"
 

class Reviewer(models.Model):
    LOAD_MODES = (
        ('all', 'Review all proposals'),
        ('equal', 'Review an equal share'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='reviewer_profile')
    review_load = models.CharField(
        max_length=10,
        choices=LOAD_MODES,
        default='equal',
        help_text="'all' = assigned every eligible proposal. 'equal' = receives a fair share alongside other equal-share reviewers.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive reviewers are skipped during assignment.",
    )

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_review_load_display()})"


class ReviewAssignment(models.Model):
    reviewer = models.ForeignKey(Reviewer, on_delete=models.CASCADE, related_name='assignments')
    proposal = models.ForeignKey('Proposal', on_delete=models.CASCADE, related_name='review_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignments_created',
    )

    class Meta:
        unique_together = ('reviewer', 'proposal')
        ordering = ['-assigned_at']

    def __str__(self):
        return f"{self.reviewer.user.username} -> {self.proposal.title}"


class SubScore(models.Model):
    review = models.ForeignKey('Review', on_delete=models.CASCADE, related_name='sub_scores')
    speaker_expertise = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=1)
    depth_of_topic = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=1)
    relevancy = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=1)
    value_or_impact = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=1)

    def __str__(self):
        return f"SubScores for {self.review}"

    def average_score(self):
        total = self.speaker_expertise + self.depth_of_topic + self.relevancy + self.value_or_impact
        return total / 4



class Review(models.Model):
    talk = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(Reviewer, on_delete=models.CASCADE, related_name='reviews')
    comments = models.TextField(blank=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Review by {self.reviewer.user.username} for {self.talk.title}"

    def average_score(self):
        sub_scores = self.sub_scores.all()
        if not sub_scores.exists():
            return 0  # or handle the case where there are no sub-scores
        total_score = sum(sub_score.average_score() for sub_score in sub_scores)
        return total_score / sub_scores.count()

 

class Document(models.Model):
    DOCUMENT_TYPES = (
        ('Slide', 'Slide'),
        ('Handout', 'Handout'),
        ('Other', 'Other'),
    )

    name = models.CharField(max_length=255, blank=True, default='', help_text="Brief name/title of the document.")
    document = models.FileField(upload_to='documents/', default='', help_text="Upload the document file here.")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    proposal = models.ForeignKey(Proposal, default=1, on_delete=models.CASCADE, related_name='documents', help_text="Associated proposal for which this document is uploaded.")
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES, default='Slide', help_text="Type of document (e.g., Slide, Handout).")

    def __str__(self):
        return f"{self.get_document_type_display()} for {self.proposal.title}"

    def get_absolute_url(self):
        return reverse("document_detail", kwargs={"pk": self.pk})
