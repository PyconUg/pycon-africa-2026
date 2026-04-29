from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required


def reviewer_required(view_func):
    """
    Restricts a view to users who have a Reviewer profile.
    Implies login_required — unauthenticated users are redirected to the login page.
    Authenticated non-reviewers receive a 403 PermissionDenied.
    """
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        # Import here to avoid circular imports
        from talks.models import Reviewer
        if not Reviewer.objects.filter(user=request.user).exists():
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped
