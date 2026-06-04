import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

logger = logging.getLogger(__name__)

EMAIL_CC = [
    "team@pycon.africa",
    "fin-aid@pycon.ug",
]


def _fin_aid_my_application_path(year):
    if year == 2026:
        return reverse("pycon2026:fin_aid_my_application")
    return reverse("fin_aid:fin_aid_my_application", kwargs={"year": year})


def send_opportunity_grant_submission_confirmation(application, request, year):
    user = application.user
    to_email = (user.email or "").strip()
    if not to_email:
        logger.warning(
            "Skipping opportunity grant submission email: user %s has no email",
            user.pk,
        )
        return

    site = get_current_site(request)
    view_url = request.build_absolute_uri(_fin_aid_my_application_path(year))

    context = {
        "user": user,
        "application": application,
        "site": site,
        "view_url": view_url,
        "year": year,
    }

    subject = render_to_string(
        "emails/opportunity_grants/submission_confirmation_subject.txt",
        context,
    ).strip()
    subject = "".join(subject.splitlines())

    html_body = render_to_string(
        "emails/opportunity_grants/submission_confirmation.html",
        context,
    )
    text_body = render_to_string(
        "emails/opportunity_grants/submission_confirmation.txt",
        context,
    )

    raw_from = getattr(settings, "DEFAULT_FROM_EMAIL", "") or ""
    from_email = raw_from.strip() or None
    msg = EmailMultiAlternatives(
        subject,
        text_body,
        from_email,
        [to_email],
    )
    msg.attach_alternative(html_body, "text/html")

    try:
        msg.send(fail_silently=False)
    except Exception:
        logger.exception(
            "Failed to send opportunity grant submission confirmation to %s",
            to_email,
        )


def send_opportunity_grant_status_notification(application_pk, new_status: str) -> bool:
    """Send a status decision email to the applicant.

    Called from signals (auto) and admin resend action (manual).
    Returns True if SMTP accepted the message.
    """
    from .models import OpportunityGrantApplication  # avoid circular import

    try:
        application = OpportunityGrantApplication.objects.select_related(
            'user', 'fin_aid', 'fin_aid__event_year'
        ).get(pk=application_pk)
    except OpportunityGrantApplication.DoesNotExist:
        logger.warning("OpportunityGrantApplication %s missing for status email", application_pk)
        return False

    user = application.user
    to_email = (user.email or "").strip()
    if not to_email:
        logger.warning(
            "Skipping opportunity grant status email: user %s has no email", user.pk
        )
        return False

    raw_from = getattr(settings, "DEFAULT_FROM_EMAIL", "") or ""
    from_email = raw_from.strip() or None
    if not from_email:
        logger.warning("DEFAULT_FROM_EMAIL is not set; cannot send opportunity grant status email")
        return False

    year = application.fin_aid.event_year.year

    subject_map = {
        OpportunityGrantApplication.STATUS_ACCEPTED: f"PyCon Africa {year} — Your Opportunity Grant Application Has Been Accepted",
        OpportunityGrantApplication.STATUS_REJECTED: f"PyCon Africa {year} — Update on Your Opportunity Grant Application",
        OpportunityGrantApplication.STATUS_WAITLIST: f"PyCon Africa {year} — Your Opportunity Grant Application Is on the Waitlist",
    }
    template_map = {
        OpportunityGrantApplication.STATUS_ACCEPTED: "emails/opportunity_grants/application_accepted.html",
        OpportunityGrantApplication.STATUS_REJECTED: "emails/opportunity_grants/application_rejected.html",
        OpportunityGrantApplication.STATUS_WAITLIST: "emails/opportunity_grants/application_waitlisted.html",
    }

    subject = subject_map.get(new_status, f"PyCon Africa {year} — Opportunity Grant Status Update")
    html_template = template_map.get(new_status, "emails/opportunity_grants/status_changed_body.txt")

    site = Site.objects.get_current()
    domain = site.domain

    if year == 2026:
        view_path = reverse("pycon2026:fin_aid_my_application")
    else:
        view_path = reverse("fin_aid:fin_aid_my_application", kwargs={"year": year})
    view_url = f"https://{domain}{view_path}"

    applicant_name = user.get_full_name() or user.get_username()

    context = {
        "application": application,
        "user": user,
        "applicant_name": applicant_name,
        "year": year,
        "view_url": view_url,
        "round_title": application.fin_aid.title,
    }

    html_content = render_to_string(html_template, context)
    text_body = render_to_string("emails/opportunity_grants/status_changed_body.txt", {
        **context,
        "new_status_display": application.get_status_display(),
        "old_status_display": "",
    })

    cc = list(EMAIL_CC) if new_status in (
        OpportunityGrantApplication.STATUS_ACCEPTED,
        OpportunityGrantApplication.STATUS_REJECTED,
        OpportunityGrantApplication.STATUS_WAITLIST,
    ) else []

    msg = EmailMultiAlternatives(
        subject,
        text_body,
        f"PyCon Africa {year} Team <{from_email}>",
        [to_email],
        cc=cc,
    )
    msg.attach_alternative(html_content, "text/html")

    try:
        msg.send(fail_silently=False)
        return True
    except Exception:
        logger.exception(
            "Failed to send opportunity grant status email (pk=%s, status=%s, to=%s)",
            application_pk,
            new_status,
            to_email,
        )
        return False
