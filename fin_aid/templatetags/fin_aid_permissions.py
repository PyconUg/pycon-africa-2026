from django import template

register = template.Library()


@register.filter
def is_fin_aid_reviewer(user):
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    from fin_aid.models import FinAidReviewer

    return FinAidReviewer.objects.filter(user=user).exists()


@register.filter
def is_regional_grant_reviewer(user):
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    from fin_aid.models import RegionalGrantCountryAssignment

    return RegionalGrantCountryAssignment.objects.filter(reviewer=user).exists()
