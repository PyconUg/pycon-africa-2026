import logging
from functools import partial

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags

from registration.models import Profile

from .models import Proposal

logger = logging.getLogger(__name__)

PROGRAMME_EMAIL_CC = [
    "program@pycon.ug",
]

@receiver(pre_save, sender=Proposal)
def proposal_stash_prev_status(sender, instance, **kwargs):
    """Remember previous status so post_save can detect transitions."""
    if not instance.pk:
        instance._proposal_prev_status = None
        return
    try:
        instance._proposal_prev_status = sender.objects.only("status").get(
            pk=instance.pk
        ).status
    except sender.DoesNotExist:
        instance._proposal_prev_status = None


def _send_proposal_program_email(proposal_pk, old_status: str, new_status: str) -> bool:
    """Send programme status email; runs after DB commit. Does not re-raise SMTP errors.
    Returns True if SMTP accepted the message and the sent timestamp was updated."""
    try:
        proposal = Proposal.objects.select_related("user", "event_year").get(
            pk=proposal_pk
        )
    except Proposal.DoesNotExist:
        logger.warning("Proposal %s missing for status email", proposal_pk)
        return False

    logger.info(
        "Programme status email: proposal_pk=%s title=%.80s to=%s",
        proposal_pk,
        proposal.title,
        getattr(proposal.user, "email", "") or "",
    )

    if not getattr(proposal.user, "email", None):
        logger.warning("Proposal %s user has no email address", proposal_pk)
        return False

    if not settings.DEFAULT_FROM_EMAIL:
        logger.warning("DEFAULT_FROM_EMAIL is not set; cannot send proposal email")
        return False

    is_poster = proposal.talk_type == "Poster"
    submission_label = "Poster" if is_poster else "Proposal"
    subject_templates = {
        "A": f"PyCon Africa 2026 - Congratulations, Your {submission_label} Has Been Accepted",
        "W": f"PyCon Africa 2026 - Your {submission_label} Is On The Waiting List",
        "R": f"PyCon Africa 2026 - Your {submission_label} Has Not Been Selected",
        "S": f"PyCon Africa 2026 - Your {submission_label} Has Been Submitted",
    }
    template_names = {
        "A": "emails/talks/proposal_accepted.html",
        "W": "emails/talks/proposal_waiting.html",
        "R": "emails/talks/proposal_rejected.html",
        "S": "emails/talks/proposal_submitted.html",
    }
    subject = subject_templates.get(
        new_status, "PyCon Africa 2026 - Your Proposal Status Update"
    )
    html_template = template_names.get(
        new_status, "emails/talks/proposal_status_changed.html"
    )

    try:
        user_profile = Profile.objects.get(user=proposal.user)
        full_name = user_profile.get_full_name()
    except Profile.DoesNotExist:
        full_name = proposal.user.username

    site = Site.objects.get_current()
    domain = site.domain
    talk_url = f"https://{domain}{reverse('talks:talk_details', kwargs={'year': proposal.event_year.year, 'pk': proposal.proposal_id.hashid})}"
    response_url = f"https://{domain}{reverse('talks:respond_to_invitation', kwargs={'year': proposal.event_year.year, 'pk': proposal.proposal_id.hashid})}"

    html_content = render_to_string(
        html_template,
        {
            "proposal": proposal,
            "user": proposal.user,
            "full_name": full_name,
            "talk_url": talk_url,
            "response_url": response_url,
        },
    )
    text_content = strip_tags(html_content)
    from_email = f"PyCon Africa 2026 Programme Team <{settings.DEFAULT_FROM_EMAIL}>"

    to = [proposal.user.email]
    cc = (
        list(PROGRAMME_EMAIL_CC)
        if new_status in ("A", "W", "R")
        else []
    )
    email = EmailMultiAlternatives(
        subject,
        text_content,
        from_email,
        to,
        cc=cc,
    )
    email.attach_alternative(html_content, "text/html")
    try:
        email.send()
    except Exception:
        logger.exception(
            "Proposal status email failed (pk=%s, %s -> %s, to=%s)",
            proposal_pk,
            old_status,
            new_status,
            proposal.user.email,
        )
        return False

    Proposal.objects.filter(pk=proposal_pk).update(
        last_program_status_email_sent_at=timezone.now()
    )
    return True


def send_programme_status_notification(proposal_pk) -> bool:
    """
    Send (or resend) the programme email for the proposal's *current* status.
    Use from admin when status did not change but the speaker should be emailed again.
    """
    proposal = (
        Proposal.objects.filter(pk=proposal_pk)
        .only("status")
        .first()
    )
    if not proposal:
        return False
    st = proposal.status
    return _send_proposal_program_email(proposal_pk, st, st)


@receiver(post_save, sender=Proposal)
def proposal_queue_status_change_email(sender, instance, created, **kwargs):
    """Queue status email after the admin save transaction commits."""
    if created:
        return
    old = getattr(instance, "_proposal_prev_status", None)
    if old is None or old == instance.status:
        return

    old_status = old
    new_status = instance.status
    # Freeze lookup key as a plain str so each on_commit callback is independent of
    # Hashid instance identity across multiple saves in one admin transaction.
    proposal_pk_arg = str(instance.pk)
    transaction.on_commit(
        partial(_send_proposal_program_email, proposal_pk_arg, old_status, new_status)
    )
