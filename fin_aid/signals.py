import logging
from functools import partial

from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import OpportunityGrantApplication, RegionalGrantApplication

logger = logging.getLogger(__name__)

NOTIFY_STATUSES = {
    OpportunityGrantApplication.STATUS_ACCEPTED,
    OpportunityGrantApplication.STATUS_REJECTED,
    OpportunityGrantApplication.STATUS_PARTIAL,
}

REGIONAL_NOTIFY_STATUSES = {
    RegionalGrantApplication.STATUS_ACCEPTED,
    RegionalGrantApplication.STATUS_REJECTED,
}


@receiver(pre_save, sender=OpportunityGrantApplication)
def og_application_stash_prev_status(sender, instance, **kwargs):
    """Remember previous status so post_save can detect transitions."""
    if not instance.pk:
        instance._og_prev_status = None
        return
    try:
        instance._og_prev_status = sender.objects.only("status").get(pk=instance.pk).status
    except sender.DoesNotExist:
        instance._og_prev_status = None


@receiver(post_save, sender=OpportunityGrantApplication)
def og_application_queue_status_change_email(sender, instance, created, **kwargs):
    """Queue status decision email after the DB transaction commits."""
    if created:
        return
    old = getattr(instance, "_og_prev_status", None)
    if old is None or old == instance.status:
        return
    if instance.status not in NOTIFY_STATUSES:
        return

    from .email_notifications import send_opportunity_grant_status_notification

    application_pk = instance.pk
    new_status = instance.status
    transaction.on_commit(
        partial(send_opportunity_grant_status_notification, application_pk, new_status)
    )


@receiver(pre_save, sender=RegionalGrantApplication)
def rg_application_stash_prev_status(sender, instance, **kwargs):
    """Remember previous application_status so post_save can detect transitions."""
    if not instance.pk:
        instance._rg_prev_status = None
        return
    try:
        instance._rg_prev_status = sender.objects.only("application_status").get(pk=instance.pk).application_status
    except sender.DoesNotExist:
        instance._rg_prev_status = None


@receiver(post_save, sender=RegionalGrantApplication)
def rg_application_queue_status_change_email(sender, instance, created, **kwargs):
    """Queue status decision email after the DB transaction commits."""
    if created:
        return
    old = getattr(instance, "_rg_prev_status", None)
    if old is None or old == instance.application_status:
        return
    if instance.application_status not in REGIONAL_NOTIFY_STATUSES:
        return

    from .email_notifications import send_regional_grant_status_notification

    application_pk = instance.pk
    new_status = instance.application_status
    transaction.on_commit(
        partial(send_regional_grant_status_notification, application_pk, new_status)
    )
