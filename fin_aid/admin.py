from django.contrib import admin, messages

from .models import (
    Fin_aid,
    FinAidApplicationReview,
    FinAidReviewAssignment,
    FinAidReviewer,
    OpportunityGrantApplication,
)
from .services import assign_applications


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
                    'After close, the public opportunity-grants page shows a closed-applications banner and keeps the programme guidelines visible.'
                ),
            },
        ),
    )


@admin.register(FinAidReviewer)
class FinAidReviewerAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_email', 'review_load', 'is_active', 'assignment_count')
    list_editable = ('review_load', 'is_active')
    list_filter = ('review_load', 'is_active')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    autocomplete_fields = ('user',)
    actions = ('run_assignment_for_latest_year_action', 'reassign_for_latest_year_action')

    def get_email(self, obj):
        return obj.user.email
    get_email.admin_order_field = 'user__email'
    get_email.short_description = 'Email address'

    def assignment_count(self, obj):
        return obj.assignments.count()
    assignment_count.short_description = 'Current assignments'

    def _get_latest_year(self, request):
        from home.models import EventYear
        latest_year = EventYear.objects.order_by('-year').first()
        if not latest_year:
            self.message_user(request, "No event year configured.", level=messages.ERROR)
        return latest_year

    def _report_assignment_result(self, request, result, year, soft_reassign=False):
        if soft_reassign and result['deleted']:
            self.message_user(
                request,
                f"Removed {result['deleted']} unreviewed assignment(s) before reassigning.",
                level=messages.INFO,
            )
        if result['created']:
            rpa = result['reviews_per_application']
            self.message_user(
                request,
                f"Created {result['created']} new review assignment(s) for {year.year} "
                f"(targeting {rpa} review(s) per application).",
                level=messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                "No new assignments created (all applications already have the target number of reviews).",
                level=messages.INFO,
            )
        if result['unassignable']:
            self.message_user(
                request,
                f"{len(result['unassignable'])} application(s) could not be assigned "
                f"(no eligible reviewer available — only the applicant themselves is a reviewer). "
                f"Application IDs: {', '.join(str(pk) for pk in result['unassignable'])}",
                level=messages.WARNING,
            )

    def run_assignment_for_latest_year_action(self, request, queryset):
        """Assign unassigned applications for the latest event year using the selected reviewers."""
        latest_year = self._get_latest_year(request)
        if not latest_year:
            return
        result = assign_applications(latest_year, reviewers=queryset, assigned_by=request.user)
        self._report_assignment_result(request, result, latest_year)

    run_assignment_for_latest_year_action.short_description = (
        "Assign applications for the latest event year (selected reviewers)"
    )

    def reassign_for_latest_year_action(self, request, queryset):
        """Soft-reassign: remove unreviewed assignments then redistribute across selected reviewers.

        Completed reviews are preserved and count toward each reviewer's load
        so they are not re-piled on.
        """
        latest_year = self._get_latest_year(request)
        if not latest_year:
            return
        result = assign_applications(
            latest_year,
            reviewers=queryset,
            assigned_by=request.user,
            soft_reassign=True,
        )
        self._report_assignment_result(request, result, latest_year, soft_reassign=True)

    reassign_for_latest_year_action.short_description = (
        "Reassign applications for the latest event year (soft — keeps completed reviews)"
    )


@admin.register(FinAidReviewAssignment)
class FinAidReviewAssignmentAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'application', 'event_year', 'assigned_at', 'assigned_by', 'has_review')
    list_filter = ('application__fin_aid__event_year', 'reviewer__review_load', 'assigned_at')
    search_fields = (
        'reviewer__user__username',
        'reviewer__user__email',
        'application__legal_name',
        'application__user__email',
    )
    autocomplete_fields = ('reviewer', 'application')
    readonly_fields = ('assigned_at',)

    def event_year(self, obj):
        return obj.application.fin_aid.event_year
    event_year.admin_order_field = 'application__fin_aid__event_year__year'
    event_year.short_description = 'Event year'

    def has_review(self, obj):
        return FinAidApplicationReview.objects.filter(
            reviewer=obj.reviewer, application=obj.application
        ).exists()
    has_review.boolean = True
    has_review.short_description = 'Reviewed?'


class FinAidApplicationReviewInline(admin.TabularInline):
    model = FinAidApplicationReview
    extra = 0
    fields = ('reviewer', 'recommendation', 'total_score', 'comments', 'created_at')
    readonly_fields = ('reviewer', 'recommendation', 'total_score', 'comments', 'created_at')


@admin.register(OpportunityGrantApplication)
class OpportunityGrantApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'fin_aid',
        'status',
        'user_response',
        'support_type',
        'submitted_at',
    )
    list_filter = ('status', 'user_response', 'support_type', 'fin_aid')
    search_fields = (
        'user__username',
        'user__email',
        'legal_name',
        'country',
    )
    readonly_fields = ('submitted_at', 'updated_at')
    inlines = (FinAidApplicationReviewInline,)
    autocomplete_fields = ('user', 'fin_aid')
    actions = (
        'accept_and_notify_action',
        'reject_and_notify_action',
        'partial_accept_and_notify_action',
        'resend_status_notification_action',
        'assign_to_reviewers_action',
        'reassign_to_reviewers_action',
    )
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
            {'fields': ('status', 'user_response')},
        ),
        (
            'Timestamps',
            {'fields': ('submitted_at', 'updated_at')},
        ),
    )

    # --- status + notify actions ---

    def accept_and_notify_action(self, request, queryset):
        """Set status to Accepted and trigger the applicant notification email."""
        updated = 0
        already = 0
        for pk in queryset.values_list('pk', flat=True):
            app = OpportunityGrantApplication.objects.get(pk=pk)
            if app.status == OpportunityGrantApplication.STATUS_ACCEPTED:
                already += 1
                continue
            app.status = OpportunityGrantApplication.STATUS_ACCEPTED
            app.save()
            updated += 1
        if updated:
            self.message_user(
                request,
                f"Accepted {updated} application(s). Notifications send when SMTP succeeds.",
                messages.SUCCESS,
            )
        if already:
            self.message_user(
                request,
                f"{already} application(s) were already accepted (skipped). "
                "Use 'Resend status notification' to email them again without changing status.",
                messages.INFO,
            )
        if not updated and not already:
            self.message_user(request, "No applications to update.", messages.WARNING)

    accept_and_notify_action.short_description = "Accept & notify applicant (selected)"

    def reject_and_notify_action(self, request, queryset):
        """Set status to Rejected and trigger the applicant notification email."""
        updated = 0
        already = 0
        for pk in queryset.values_list('pk', flat=True):
            app = OpportunityGrantApplication.objects.get(pk=pk)
            if app.status == OpportunityGrantApplication.STATUS_REJECTED:
                already += 1
                continue
            app.status = OpportunityGrantApplication.STATUS_REJECTED
            app.save()
            updated += 1
        if updated:
            self.message_user(
                request,
                f"Rejected {updated} application(s). Notifications send when SMTP succeeds.",
                messages.SUCCESS,
            )
        if already:
            self.message_user(
                request,
                f"{already} application(s) were already rejected (skipped). "
                "Use 'Resend status notification' to email them again without changing status.",
                messages.INFO,
            )
        if not updated and not already:
            self.message_user(request, "No applications to update.", messages.WARNING)

    reject_and_notify_action.short_description = "Reject & notify applicant (selected)"

    def partial_accept_and_notify_action(self, request, queryset):
        """Set status to Partially accepted and trigger the applicant notification email."""
        updated = 0
        already = 0
        for pk in queryset.values_list('pk', flat=True):
            app = OpportunityGrantApplication.objects.get(pk=pk)
            if app.status == OpportunityGrantApplication.STATUS_PARTIAL:
                already += 1
                continue
            app.status = OpportunityGrantApplication.STATUS_PARTIAL
            app.save()
            updated += 1
        if updated:
            self.message_user(
                request,
                f"Partially accepted {updated} application(s). Notifications send when SMTP succeeds.",
                messages.SUCCESS,
            )
        if already:
            self.message_user(
                request,
                f"{already} application(s) were already partially accepted (skipped). "
                "Use 'Resend status notification' to email them again without changing status.",
                messages.INFO,
            )
        if not updated and not already:
            self.message_user(request, "No applications to update.", messages.WARNING)

    partial_accept_and_notify_action.short_description = "Partially accept & notify applicant (selected)"

    def resend_status_notification_action(self, request, queryset):
        """Re-send the status email matching each application's current status."""
        from .email_notifications import send_opportunity_grant_status_notification

        NOTIFY_STATUSES = {
            OpportunityGrantApplication.STATUS_ACCEPTED,
            OpportunityGrantApplication.STATUS_REJECTED,
            OpportunityGrantApplication.STATUS_PARTIAL,
        }

        sent = 0
        skipped = 0
        failed = 0
        for pk, status in queryset.values_list('pk', 'status'):
            if status not in NOTIFY_STATUSES:
                skipped += 1
                continue
            if send_opportunity_grant_status_notification(pk, status):
                sent += 1
            else:
                failed += 1

        if sent:
            self.message_user(
                request,
                f"Resent status notification for {sent} application(s).",
                messages.SUCCESS,
            )
        if skipped:
            self.message_user(
                request,
                f"{skipped} application(s) skipped — only accepted, rejected, and partially accepted "
                "applications trigger a notification email.",
                messages.INFO,
            )
        if failed:
            self.message_user(
                request,
                f"{failed} application(s) could not be emailed "
                "(missing user email, SMTP error, or missing DEFAULT_FROM_EMAIL). See server logs.",
                messages.WARNING,
            )

    resend_status_notification_action.short_description = "Resend status notification email (selected)"

    def _run_assignment_on_queryset(self, request, queryset, soft_reassign=False):
        event_years = set()
        for app in queryset.select_related('fin_aid__event_year'):
            event_years.add(app.fin_aid.event_year)

        if not event_years:
            self.message_user(request, "No applications selected.", level=messages.WARNING)
            return

        total_created = 0
        total_deleted = 0
        all_unassignable = []
        reviews_per_application = 0

        for event_year in event_years:
            scoped = queryset.filter(fin_aid__event_year=event_year)
            result = assign_applications(
                event_year,
                applications=scoped,
                assigned_by=request.user,
                soft_reassign=soft_reassign,
            )
            total_created += result['created']
            total_deleted += result['deleted']
            all_unassignable.extend(result['unassignable'])
            reviews_per_application = result['reviews_per_application']

        if soft_reassign and total_deleted:
            self.message_user(
                request,
                f"Removed {total_deleted} unreviewed assignment(s) before reassigning.",
                level=messages.INFO,
            )
        if total_created:
            self.message_user(
                request,
                f"Created {total_created} new review assignment(s) "
                f"(targeting {reviews_per_application} review(s) per application).",
                level=messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                "No new assignments were created (all applications already have the target number of reviews).",
                level=messages.INFO,
            )
        if all_unassignable:
            self.message_user(
                request,
                f"{len(all_unassignable)} application(s) could not be assigned to any reviewer. "
                f"Application IDs: {', '.join(str(pk) for pk in all_unassignable)}",
                level=messages.WARNING,
            )

    def assign_to_reviewers_action(self, request, queryset):
        """Assign selected applications to reviewers (skips already-assigned ones)."""
        self._run_assignment_on_queryset(request, queryset, soft_reassign=False)

    assign_to_reviewers_action.short_description = "Assign selected applications to reviewers"

    def reassign_to_reviewers_action(self, request, queryset):
        """Soft-reassign selected applications: remove unreviewed assignments and redistribute.

        Completed reviews are preserved and count toward each reviewer's load
        so they are not re-piled on.
        """
        self._run_assignment_on_queryset(request, queryset, soft_reassign=True)

    reassign_to_reviewers_action.short_description = (
        "Reassign selected applications to reviewers (soft — keeps completed reviews)"
    )


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
