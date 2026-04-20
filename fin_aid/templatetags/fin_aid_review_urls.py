from django import template
from django.urls import reverse

register = template.Library()


def _year(context):
    y = context.get('year')
    return 2026 if y is None else y


@register.simple_tag(takes_context=True)
def fin_aid_reviews_url(context):
    y = _year(context)
    if y == 2026:
        return reverse('pycon2026:fin_aid_reviews')
    return reverse('fin_aid:fin_aid_reviews', kwargs={'year': y})


@register.simple_tag(takes_context=True)
def fin_aid_review_detail_url(context, pk):
    y = _year(context)
    if y == 2026:
        return reverse('pycon2026:fin_aid_review_detail', kwargs={'pk': pk})
    return reverse('fin_aid:fin_aid_review_detail', kwargs={'year': y, 'pk': pk})


@register.simple_tag(takes_context=True)
def fin_aid_public_url(context):
    y = _year(context)
    if y == 2026:
        return reverse('pycon2026:fin_aid')
    return reverse('fin_aid:fin_aid', kwargs={'year': y})


@register.simple_tag(takes_context=True)
def fin_aid_review_success_url(context):
    y = _year(context)
    if y == 2026:
        return reverse('pycon2026:fin_aid_review_success')
    return reverse('fin_aid:fin_aid_review_success', kwargs={'year': y})


@register.simple_tag(takes_context=True)
def fin_aid_apply_url(context):
    y = _year(context)
    if y == 2026:
        return reverse('pycon2026:fin_aid_apply')
    return reverse('fin_aid:fin_aid_apply', kwargs={'year': y})


@register.simple_tag(takes_context=True)
def fin_aid_my_application_url(context):
    y = _year(context)
    if y == 2026:
        return reverse('pycon2026:fin_aid_my_application')
    return reverse('fin_aid:fin_aid_my_application', kwargs={'year': y})


@register.simple_tag(takes_context=True)
def fin_aid_application_edit_url(context):
    y = _year(context)
    if y == 2026:
        return reverse('pycon2026:fin_aid_application_edit')
    return reverse('fin_aid:fin_aid_application_edit', kwargs={'year': y})


@register.simple_tag(takes_context=True)
def fin_aid_submitted_application_url(context):
    request = context.get('request')
    if not request or not getattr(request.user, 'is_authenticated', False):
        return ''
    y = _year(context)
    from home.models import EventYear
    from fin_aid.models import Fin_aid, OpportunityGrantApplication

    try:
        event_year = EventYear.objects.get(year=y)
    except EventYear.DoesNotExist:
        return ''
    fin_round = (
        Fin_aid.objects.filter(event_year=event_year).order_by('-date_created').first()
    )
    if not fin_round:
        return ''
    if not OpportunityGrantApplication.objects.filter(
        fin_aid=fin_round,
        user=request.user,
    ).exists():
        return ''
    if y == 2026:
        return reverse('pycon2026:fin_aid_my_application')
    return reverse('fin_aid:fin_aid_my_application', kwargs={'year': y})
