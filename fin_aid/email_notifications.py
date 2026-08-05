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


def _fin_aid_respond_path(year):
    if year == 2026:
        return reverse("pycon2026:fin_aid_respond")
    return reverse("fin_aid:fin_aid_respond", kwargs={"year": year})


def send_opportunity_grant_response_confirmation(application, year=None):
    user = application.user
    to_email = (user.email or "").strip()
    if not to_email:
        logger.warning(
            "Skipping opportunity grant response email: user %s has no email",
            user.pk,
        )
        return

    if year is None:
        year = application.fin_aid.event_year.year

    raw_from = getattr(settings, "DEFAULT_FROM_EMAIL", "") or ""
    from_email = raw_from.strip() or None
    if not from_email:
        logger.warning("DEFAULT_FROM_EMAIL is not set; cannot send opportunity grant response email")
        return

    applicant_name = user.get_full_name() or user.get_username()

    if application.user_response == "A":
        if application.has_travel_grant:
            subject = f"PyCon Africa {year} — Next Steps for Your Opportunity Grant"
        else:
            subject = f"PyCon Africa {year} — Redeem Your Conference Ticket"
        html_template = "emails/opportunity_grants/grant_accepted_response.html"
        text_template = "emails/opportunity_grants/grant_accepted_response.txt"
        if not application.ticket_code:
            logger.warning(
                "User %s accepted grant (pk=%s) but no ticket_code assigned yet",
                user.pk,
                application.pk,
            )
    elif application.user_response == "R":
        subject = f"PyCon Africa {year} — Thank You for Your Response"
        html_template = "emails/opportunity_grants/grant_declined_response.html"
        text_template = "emails/opportunity_grants/status_changed_body.txt"
    else:
        return

    site = Site.objects.get_current()
    domain = site.domain

    view_path = _fin_aid_my_application_path(year)
    view_url = f"https://{domain}{view_path}"

    context = {
        "application": application,
        "user": user,
        "applicant_name": applicant_name,
        "year": year,
        "view_url": view_url,
    }

    html_content = render_to_string(html_template, context)
    text_body = render_to_string(text_template, {
        **context,
        "new_status_display": application.get_user_response_display(),
        "old_status_display": "",
    })

    msg = EmailMultiAlternatives(
        subject,
        text_body,
        f"PyCon Africa {year} Team <{from_email}>",
        [to_email],
        cc=list(EMAIL_CC),
    )
    msg.attach_alternative(html_content, "text/html")

    try:
        msg.send(fail_silently=False)
    except Exception:
        logger.exception(
            "Failed to send opportunity grant response email (pk=%s, response=%s, to=%s)",
            application.pk,
            application.user_response,
            to_email,
        )


def send_regional_grant_reviewer_assignment_email(user, countries) -> bool:
    """Notify a user their Regional Grant reviewer permissions/assignment changed.

    `countries` is a list of human-readable country labels (not raw choice codes).
    """
    to_email = (user.email or "").strip()
    if not to_email:
        logger.warning(
            "Skipping regional grant reviewer assignment email: user %s has no email",
            user.pk,
        )
        return False

    raw_from = getattr(settings, "DEFAULT_FROM_EMAIL", "") or ""
    from_email = raw_from.strip() or None
    if not from_email:
        logger.warning("DEFAULT_FROM_EMAIL is not set; cannot send regional grant reviewer assignment email")
        return False

    site = Site.objects.get_current()
    domain = site.domain
    review_url = f"https://{domain}{reverse('pycon2026:regional_grant_reviews')}"

    context = {
        "user": user,
        "countries": countries,
        "review_url": review_url,
    }

    subject = render_to_string(
        "emails/regional_grants/reviewer_assigned_subject.txt",
        context,
    ).strip()
    subject = "".join(subject.splitlines())

    html_body = render_to_string("emails/regional_grants/reviewer_assigned.html", context)
    text_body = render_to_string("emails/regional_grants/reviewer_assigned.txt", context)

    msg = EmailMultiAlternatives(
        subject,
        text_body,
        f"PyCon Africa 2026 Team <{from_email}>",
        [to_email],
    )
    msg.attach_alternative(html_body, "text/html")

    try:
        msg.send(fail_silently=False)
        return True
    except Exception:
        logger.exception(
            "Failed to send regional grant reviewer assignment email to %s",
            to_email,
        )
        return False


def send_regional_grant_response_confirmation(application) -> bool:
    """Send a confirmation email after an applicant accepts/declines their regional grant offer."""
    to_email = (application.email or "").strip()
    if not to_email:
        logger.warning(
            "Skipping regional grant response email: application %s has no email", application.pk
        )
        return False

    raw_from = getattr(settings, "DEFAULT_FROM_EMAIL", "") or ""
    from_email = raw_from.strip() or None
    if not from_email:
        logger.warning("DEFAULT_FROM_EMAIL is not set; cannot send regional grant response email")
        return False

    from .models import RegionalGrantApplication  # avoid circular import

    if application.user_response == RegionalGrantApplication.USER_RESPONSE_ACCEPTED:
        subject = "PyCon Africa 2026 — Thank You for Confirming Your Regional Grant"
        html_template = "emails/regional_grants/grant_accepted_response.html"
        text_template = "emails/regional_grants/grant_accepted_response.txt"
    elif application.user_response == RegionalGrantApplication.USER_RESPONSE_REJECTED:
        subject = "PyCon Africa 2026 — Thank You for Your Response"
        html_template = "emails/regional_grants/grant_declined_response.html"
        text_template = "emails/regional_grants/status_changed_body.txt"
    else:
        return False

    context = {
        "application": application,
        "applicant_name": application.full_name,
    }

    html_content = render_to_string(html_template, context)
    text_body = render_to_string(text_template, {
        **context,
        "new_status_display": application.get_user_response_display(),
        "old_status_display": "",
    })

    msg = EmailMultiAlternatives(
        subject,
        text_body,
        f"PyCon Africa 2026 Team <{from_email}>",
        [to_email],
        cc=list(EMAIL_CC),
    )
    msg.attach_alternative(html_content, "text/html")

    try:
        msg.send(fail_silently=False)
        return True
    except Exception:
        logger.exception(
            "Failed to send regional grant response email (pk=%s, response=%s, to=%s)",
            application.pk,
            application.user_response,
            to_email,
        )
        return False


def send_regional_grant_status_notification(application_pk, new_status: str) -> bool:
    """Send a status decision email to a regional grant applicant.

    Called from signals (auto) and admin resend action (manual).
    Returns True if SMTP accepted the message.
    """
    from .models import RegionalGrantApplication  # avoid circular import

    try:
        application = RegionalGrantApplication.objects.get(pk=application_pk)
    except RegionalGrantApplication.DoesNotExist:
        logger.warning("RegionalGrantApplication %s missing for status email", application_pk)
        return False

    to_email = (application.email or "").strip()
    if not to_email:
        logger.warning(
            "Skipping regional grant status email: application %s has no email", application.pk
        )
        return False

    raw_from = getattr(settings, "DEFAULT_FROM_EMAIL", "") or ""
    from_email = raw_from.strip() or None
    if not from_email:
        logger.warning("DEFAULT_FROM_EMAIL is not set; cannot send regional grant status email")
        return False

    subject_map = {
        RegionalGrantApplication.STATUS_ACCEPTED: "Congratulations! Your PyCon Africa 2026 Travel Opportunity Grant",
        RegionalGrantApplication.STATUS_REJECTED: "Update on Your PyCon Africa 2026 Travel Opportunity Grant Application",
    }
    template_map = {
        RegionalGrantApplication.STATUS_ACCEPTED: "emails/regional_grants/application_accepted.html",
        RegionalGrantApplication.STATUS_REJECTED: "emails/regional_grants/application_rejected.html",
    }

    subject = subject_map.get(new_status, "PyCon Africa 2026 — Regional Grant Status Update")
    html_template = template_map.get(new_status, "emails/regional_grants/status_changed_body.txt")

    site = Site.objects.get_current()
    domain = site.domain
    response_url = f"https://{domain}{reverse('pycon2026:regional_grant_respond')}"

    context = {
        "application": application,
        "applicant_name": application.full_name,
        "response_url": response_url,
    }

    html_content = render_to_string(html_template, context)
    text_body = render_to_string("emails/regional_grants/status_changed_body.txt", {
        **context,
        "new_status_display": application.get_application_status_display(),
        "old_status_display": "",
    })

    msg = EmailMultiAlternatives(
        subject,
        text_body,
        f"PyCon Africa 2026 Team <{from_email}>",
        [to_email],
        cc=list(EMAIL_CC),
    )
    msg.attach_alternative(html_content, "text/html")

    try:
        msg.send(fail_silently=False)
        return True
    except Exception:
        logger.exception(
            "Failed to send regional grant status email (pk=%s, status=%s, to=%s)",
            application_pk,
            new_status,
            to_email,
        )
        return False


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
        OpportunityGrantApplication.STATUS_PARTIAL: f"PyCon Africa {year} — Your Opportunity Grant Has Been Partially Accepted",
    }
    template_map = {
        OpportunityGrantApplication.STATUS_ACCEPTED: "emails/opportunity_grants/application_accepted.html",
        OpportunityGrantApplication.STATUS_REJECTED: "emails/opportunity_grants/application_rejected.html",
        OpportunityGrantApplication.STATUS_PARTIAL: "emails/opportunity_grants/application_partial.html",
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

    granted_items = []
    if new_status == OpportunityGrantApplication.STATUS_PARTIAL:
        grant_type = application.support_type
        latest_review = application.reviews.order_by('-pk').first()
        if latest_review and latest_review.grant_type:
            grant_type = latest_review.grant_type
        support_labels = dict(OpportunityGrantApplication.SUPPORT_TYPE_CHOICES)
        granted_items = [support_labels.get(grant_type, grant_type)]

    respond_path = _fin_aid_respond_path(year)
    response_url = f"https://{domain}{respond_path}"

    context = {
        "application": application,
        "user": user,
        "applicant_name": applicant_name,
        "year": year,
        "view_url": view_url,
        "response_url": response_url,
        "round_title": application.fin_aid.title,
        "acceptance_deadline": "Monday, 6 July 2026",
        "granted_items": granted_items,
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
        OpportunityGrantApplication.STATUS_PARTIAL,
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
