from django.contrib import admin

from .models import (
    Fin_aid,
    FinAidReviewer,
    FinAidApplicationReview,
    OpportunityGrantApplication,
)


@admin.register(Fin_aid)
class Fin_aidAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'event_year',
        'fin_open_date',
        'fin_close_date',
        'date_created',
        'date_updated',
    )
    list_filter = ('event_year',)
    search_fields = ('title',)
    ordering = ('-date_created',)
    date_hierarchy = 'fin_open_date'
    autocomplete_fields = ('event_year',)
    fieldsets = (
        (
            'About this screen',
            {
                'description': (
                    '<strong>This is not an applicant\'s form.</strong> Here you set the event year, application open/close times, '
                    'and an internal title. Public programme text for the current site is maintained in templates. '
                    'Individual requests from attendees are under <strong>Opportunity grant applications</strong> '
                    'in this admin; those records match the same fields applicants see on the website.'
                ),
                'fields': (),
            },
        ),
        (None, {'fields': ('title', 'event_year')}),
        (
            'Application window (open / close)',
            {
                'fields': ('fin_open_date', 'fin_close_date'),
                'description': (
                    'The public apply form is open when: <strong>fin_open_date</strong> ≤ now ≤ '
                    '<strong>fin_close_date</strong>. '
                    'Times use the project timezone (Django TIME_ZONE). '
                    'After close, the public opportunity-grants page shows the short “check back later” message until you change these dates.'
                ),
            },
        ),
    )


@admin.register(FinAidReviewer)
class FinAidReviewerAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    autocomplete_fields = ('user',)


class FinAidApplicationReviewInline(admin.TabularInline):
    model = FinAidApplicationReview
    extra = 0
    readonly_fields = ('reviewer', 'recommendation', 'comments', 'created_at')


@admin.register(OpportunityGrantApplication)
class OpportunityGrantApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'fin_aid',
        'status',
        'support_type',
        'submitted_at',
        'review_summary_display',
        'suggested_status_display',
    )
    list_filter = ('status', 'support_type', 'fin_aid')
    search_fields = (
        'user__username',
        'user__email',
        'legal_name',
        'country',
    )
    readonly_fields = ('submitted_at', 'updated_at')
    inlines = (FinAidApplicationReviewInline,)
    autocomplete_fields = ('user', 'fin_aid')
    fieldsets = (
        (
            'Round & account',
            {
                'fields': ('fin_aid', 'user'),
                'description': 'Must match a grant round (<strong>Fin aid</strong>) and the applicant login account.',
            },
        ),
        (
            'Application answers (same as public form)',
            {
                'fields': (
                    'legal_name',
                    'country',
                    'support_type',
                    'budget_narrative',
                    'why_need_support',
                    'community_contribution',
                    'additional_notes',
                ),
            },
        ),
        (
            'Committee',
            {'fields': ('status',)},
        ),
        (
            'Timestamps',
            {'fields': ('submitted_at', 'updated_at')},
        ),
    )

    def review_summary_display(self, obj):
        summary = obj.get_review_summary()
        return f"A:{summary['accept']} R:{summary['reject']} U:{summary['unsure']} (Total: {summary['total']})"
    review_summary_display.short_description = 'Review Summary'

    def suggested_status_display(self, obj):
        suggested = obj.get_suggested_status()
        current = obj.status
        if suggested == current:
            return f"{obj.get_status_display()} ✓"
        else:
            return f"{obj.get_status_display()} → {dict(obj.STATUS_CHOICES)[suggested]}"
    suggested_status_display.short_description = 'Status (Suggested)'


@admin.register(FinAidApplicationReview)
class FinAidApplicationReviewAdmin(admin.ModelAdmin):
    list_display = ('application', 'reviewer', 'recommendation', 'created_at')
    list_filter = ('recommendation',)
    search_fields = (
        'application__user__email',
        'reviewer__user__username',
        'comments',
    )
    readonly_fields = ('created_at',)
    autocomplete_fields = ('application', 'reviewer')
