import logging

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

logger = logging.getLogger(__name__)


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
