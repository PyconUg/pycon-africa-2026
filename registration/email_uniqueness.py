from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

EMAIL_IN_USE_MESSAGE = _(
    "This email address is already in use. Please supply a different email address."
)


def email_address_in_use(email, *, exclude_user=None):
    """Return True if another account already uses this email (case-insensitive)."""
    if not email:
        return False
    qs = get_user_model().objects.filter(email__iexact=email).exclude(email="")
    if exclude_user is not None:
        qs = qs.exclude(pk=exclude_user.pk)
    return qs.exists()
