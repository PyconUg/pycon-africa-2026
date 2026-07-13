# admin.py
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from import_export import resources, fields, formats
from import_export.admin import ExportActionMixin, ImportExportModelAdmin
from .models import *
from registration.models import Profile
from .forms import ExportFieldsForm 
from .services import assign_proposals
from django.shortcuts import render
from django.urls import path
from django.utils.html import format_html
from django.db.models import Count
from django.shortcuts import render, get_object_or_404, reverse
from django.http import HttpResponseRedirect, HttpResponse, FileResponse, Http404
from django.urls import path, reverse 
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.admin.utils import unquote 
from django.db.models import Avg, F, Q, Count 
  



class ProposalResource(resources.ModelResource):
    user_email = fields.Field(attribute='user__email', column_name='Email')
    user_first_name = fields.Field(attribute='user__user_profile__name', column_name='First Name')
    user_last_name = fields.Field(attribute='user__user_profile__surname', column_name='Last Name')
    user_username = fields.Field(attribute='user__username', column_name='Username')
    event_year = fields.Field(attribute='event_year__year', column_name='Event Year')
    multiple_submissions = fields.Field(column_name='Multiple Submissions')

    class Meta:
        model = Proposal
        fields = (
            'title', 'talk_type', 'talk_category', 'elevator_pitch', 'talk_abstract', 'user_email', 'user_first_name', 
            'user_last_name', 'user_username', 'status', 'intended_audience', 'link_to_preview_video_url', 
            'anything_else_you_want_to_tell_us', 'special_requirements', 'recording_release', 'youtube_video_url', 
            'youtube_iframe_url', 'created_date', 'date_updated', 'event_year', 'multiple_submissions'
        )

    def dehydrate_multiple_submissions(self, proposal):
        user_talk_count = Proposal.objects.filter(
            user=proposal.user,
            event_year=proposal.event_year
        ).count()
        return user_talk_count > 1

class TalkAdmin(ImportExportModelAdmin):
    change_form_template = "admin/talks/proposal/change_form.html"
    resource_class = ProposalResource
    list_display = (
        "title",
        "user",
        "list_speakers",
        "talk_type",
        "intended_audience",
        "status",
        "status_email_sent_display",
        "user_response",
        "has_poster_attachment",
        "created_date",
        "date_updated",
    )
    list_editable = ["user_response"]
    list_filter = ("talk_type", "created_date", "status", "user_response")
    search_fields = ("title", "user__username", "user__email")
    readonly_fields = ("last_program_status_email_sent_at",)
    actions = [
        "accept_and_notify_speaker_action",
        "waitlist_and_notify_speaker_action",
        "reject_and_notify_speaker_action",
        "resend_programme_notification_action",
        "export_selected_action",
        "assign_to_reviewers_action",
    ]

    @admin.display(
        description="Status email",
        ordering="last_program_status_email_sent_at",
        boolean=False,
    )
    def status_email_sent_display(self, obj):
        ts = obj.last_program_status_email_sent_at
        if not ts:
            return format_html('<span style="color:#999">—</span>')
        return format_html(
            '<span title="{}">Sent</span>',
            ts.strftime("%Y-%m-%d %H:%M %Z"),
        )

    def save_model(self, request, obj, form, change):
        prev_status = None
        if change and obj.pk:
            prev_status = (
                Proposal.objects.filter(pk=obj.pk)
                .values_list("status", flat=True)
                .first()
            )
        super().save_model(request, obj, form, change)
        if change and prev_status is not None and prev_status != obj.status:
            self.message_user(
                request,
                "Status saved. If SMTP is working, the speaker notification is sent after "
                "this save completes (see the Status email column).",
                messages.SUCCESS,
            )

    def accept_and_notify_speaker_action(self, request, queryset):
        """Set status to Accepted and trigger the programme notification email."""
        accepted = 0
        already = 0
        for proposal_pk in queryset.values_list("pk", flat=True):
            proposal = Proposal.objects.get(pk=proposal_pk)
            if proposal.status == "A":
                already += 1
                continue
            proposal.status = "A"
            proposal.save()
            accepted += 1
        if accepted:
            self.message_user(
                request,
                f"Accepted {accepted} proposal(s). Notifications send when SMTP succeeds "
                "(see the Status email column).",
                messages.SUCCESS,
            )
        if already:
            self.message_user(
                request,
                f"{already} proposal(s) were already accepted (skipped). "
                "Use “Resend programme notification email” to email them without changing status.",
                messages.INFO,
            )
        if not accepted and not already:
            self.message_user(request, "No proposals to update.", messages.WARNING)

    accept_and_notify_speaker_action.short_description = (
        "Accept & email speaker (selected proposals)"
    )

    def waitlist_and_notify_speaker_action(self, request, queryset):
        """Set status to Waiting List and trigger the programme notification email."""
        waitlisted = 0
        already = 0
        for proposal_pk in queryset.values_list("pk", flat=True):
            proposal = Proposal.objects.get(pk=proposal_pk)
            if proposal.status == "W":
                already += 1
                continue
            proposal.status = "W"
            proposal.save()
            waitlisted += 1
        if waitlisted:
            self.message_user(
                request,
                f"Waitlisted {waitlisted} proposal(s). Notifications send when SMTP succeeds "
                "(see the Status email column).",
                messages.SUCCESS,
            )
        if already:
            self.message_user(
                request,
                f"{already} proposal(s) were already on the waiting list (skipped). "
                "Use “Resend programme notification email” to email them without changing status.",
                messages.INFO,
            )
        if not waitlisted and not already:
            self.message_user(request, "No proposals to update.", messages.WARNING)

    waitlist_and_notify_speaker_action.short_description = (
        "Waitlist & email speaker (selected proposals)"
    )

    def reject_and_notify_speaker_action(self, request, queryset):
        """Set status to Rejected and trigger the programme notification email."""
        rejected = 0
        already = 0
        for proposal_pk in queryset.values_list("pk", flat=True):
            proposal = Proposal.objects.get(pk=proposal_pk)
            if proposal.status == "R":
                already += 1
                continue
            proposal.status = "R"
            proposal.save()
            rejected += 1
        if rejected:
            self.message_user(
                request,
                f"Rejected {rejected} proposal(s). Notifications send when SMTP succeeds "
                "(see the Status email column).",
                messages.SUCCESS,
            )
        if already:
            self.message_user(
                request,
                f"{already} proposal(s) were already rejected (skipped). "
                "Use “Resend programme notification email” to email them without changing status.",
                messages.INFO,
            )
        if not rejected and not already:
            self.message_user(request, "No proposals to update.", messages.WARNING)

    reject_and_notify_speaker_action.short_description = (
        "Reject & email speaker (selected proposals)"
    )

    def resend_programme_notification_action(self, request, queryset):
        """Send the programme email matching each proposal's current status (including resends)."""
        from talks.signals import send_programme_status_notification

        sent = 0
        failed = 0
        for proposal_pk in queryset.values_list("pk", flat=True):
            if send_programme_status_notification(proposal_pk):
                sent += 1
            else:
                failed += 1
        if sent:
            self.message_user(
                request,
                f"Sent programme notification for {sent} proposal(s). "
                "See the Status email column for the last sent time.",
                messages.SUCCESS,
            )
        if failed:
            self.message_user(
                request,
                f"{failed} proposal(s) could not be emailed "
                "(missing user email, SMTP error, or missing DEFAULT_FROM_EMAIL). See server logs.",
                messages.WARNING,
            )

    resend_programme_notification_action.short_description = (
        "Resend programme notification email (selected)"
    )

    def accept_programme_view(self, request, object_id):
        """POST from proposal change page — set Accepted and queue notification email."""
        if not self.has_change_permission(request):
            raise PermissionDenied
        opts = self.model._meta
        object_id = unquote(object_id)
        proposal = get_object_or_404(self.model, pk=object_id)
        change_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_change",
            args=[proposal.pk],
        )
        if request.method != "POST":
            self.message_user(
                request,
                "Use the Accept & email speaker button to confirm.",
                messages.WARNING,
            )
            return HttpResponseRedirect(change_url)
        if proposal.status == "A":
            self.message_user(request, "This proposal is already accepted.", messages.INFO)
        else:
            proposal.status = "A"
            proposal.save()
            self.message_user(
                request,
                "Marked as Accepted. Notification sends when SMTP succeeds "
                "(see the Status email column).",
                messages.SUCCESS,
            )
        return HttpResponseRedirect(change_url)

    def waitlist_programme_view(self, request, object_id):
        """POST from proposal change page — set Waiting List and queue notification email."""
        if not self.has_change_permission(request):
            raise PermissionDenied
        opts = self.model._meta
        object_id = unquote(object_id)
        proposal = get_object_or_404(self.model, pk=object_id)
        change_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_change",
            args=[proposal.pk],
        )
        if request.method != "POST":
            self.message_user(
                request,
                "Use the Waitlist & email speaker button to confirm.",
                messages.WARNING,
            )
            return HttpResponseRedirect(change_url)
        if proposal.status == "W":
            self.message_user(
                request, "This proposal is already on the waiting list.", messages.INFO
            )
        else:
            proposal.status = "W"
            proposal.save()
            self.message_user(
                request,
                "Marked as Waiting List. Notification sends when SMTP succeeds "
                "(see the Status email column).",
                messages.SUCCESS,
            )
        return HttpResponseRedirect(change_url)

    def reject_programme_view(self, request, object_id):
        """POST from proposal change page — set Rejected and queue notification email."""
        if not self.has_change_permission(request):
            raise PermissionDenied
        opts = self.model._meta
        object_id = unquote(object_id)
        proposal = get_object_or_404(self.model, pk=object_id)
        change_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_change",
            args=[proposal.pk],
        )
        if request.method != "POST":
            self.message_user(
                request,
                "Use the Reject & email speaker button to confirm.",
                messages.WARNING,
            )
            return HttpResponseRedirect(change_url)
        if proposal.status == "R":
            self.message_user(request, "This proposal is already rejected.", messages.INFO)
        else:
            proposal.status = "R"
            proposal.save()
            self.message_user(
                request,
                "Marked as Rejected. Notification sends when SMTP succeeds "
                "(see the Status email column).",
                messages.SUCCESS,
            )
        return HttpResponseRedirect(change_url)

    def resend_programme_view(self, request, object_id):
        """POST from proposal change page — resend programme email for current status."""
        if not self.has_change_permission(request):
            raise PermissionDenied
        from talks.signals import send_programme_status_notification

        opts = self.model._meta
        object_id = unquote(object_id)
        proposal = get_object_or_404(self.model, pk=object_id)
        change_url = reverse(
            f"admin:{opts.app_label}_{opts.model_name}_change",
            args=[proposal.pk],
        )
        if request.method != "POST":
            self.message_user(
                request,
                "Use the Resend programme notification button to confirm.",
                messages.WARNING,
            )
            return HttpResponseRedirect(change_url)
        if send_programme_status_notification(proposal.pk):
            self.message_user(
                request,
                "Programme notification resent (see the Status email column).",
                messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                "Could not send email (missing user email, SMTP error, or "
                "missing DEFAULT_FROM_EMAIL). See server logs.",
                messages.WARNING,
            )
        return HttpResponseRedirect(change_url)

    def assign_to_reviewers_action(self, request, queryset):
        """Run the assignment algorithm scoped to the selected proposals.

        Reviewers are taken from the active reviewers in the system.
        Each event year present in the queryset is processed independently.
        """
        event_years = {p.event_year for p in queryset.select_related('event_year')}
        if not event_years:
            self.message_user(request, "No proposals selected.", level=messages.WARNING)
            return

        total_created = 0
        all_unassignable = []
        for event_year in event_years:
            scoped = queryset.filter(event_year=event_year)
            result = assign_proposals(
                event_year,
                proposals=scoped,
                assigned_by=request.user,
            )
            total_created += result['created']
            all_unassignable.extend(result['unassignable'])

        if total_created:
            self.message_user(
                request,
                f"Created {total_created} new review assignment(s).",
                level=messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                "No new assignments were created (everything is already assigned).",
                level=messages.INFO,
            )

        if all_unassignable:
            self.message_user(
                request,
                f"{len(all_unassignable)} proposal(s) could not be assigned to any reviewer "
                f"(every eligible reviewer is the author or a co-speaker). "
                f"Proposal IDs: {', '.join(str(pid) for pid in all_unassignable)}",
                level=messages.WARNING,
            )

    assign_to_reviewers_action.short_description = "Assign selected proposals to reviewers"

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/accept-programme/",
                self.admin_site.admin_view(self.accept_programme_view),
                name="%s_%s_accept_programme" % info,
            ),
            path(
                "<path:object_id>/waitlist-programme/",
                self.admin_site.admin_view(self.waitlist_programme_view),
                name="%s_%s_waitlist_programme" % info,
            ),
            path(
                "<path:object_id>/reject-programme/",
                self.admin_site.admin_view(self.reject_programme_view),
                name="%s_%s_reject_programme" % info,
            ),
            path(
                "<path:object_id>/resend-programme/",
                self.admin_site.admin_view(self.resend_programme_view),
                name="%s_%s_resend_programme" % info,
            ),
            path(
                "export_selected/",
                self.admin_site.admin_view(self.export_selected),
                name="export_selected",
            ),
        ]
        return custom_urls + urls

    def get_export_resource_class(self):
        return self.resource_class

    def export_selected(self, request):
        if request.method == 'POST':
            form = ExportFieldsForm(request.POST)
            if form.is_valid():
                fields_to_export = form.cleaned_data['fields_to_export']
                export_format = form.cleaned_data['export_format']
                selected_talk_types = form.cleaned_data['talk_types']

                # Map the selected format to the import_export format class
                format_map = {
                    'csv': formats.base_formats.CSV,
                    'xls': formats.base_formats.XLS,
                    'xlsx': formats.base_formats.XLSX,
                    'json': formats.base_formats.JSON,
                    'yaml': formats.base_formats.YAML,
                }

                selected_format_class = format_map[export_format]
                queryset = self.get_queryset(request)
                
                if selected_talk_types:
                    queryset = queryset.filter(talk_type__in=selected_talk_types)
                
                resource = self.get_export_resource_class()()

                # Export only the selected fields
                dataset = resource.export(queryset, fields=fields_to_export)

                export_data = selected_format_class().export_data(dataset)
                response = HttpResponse(export_data, content_type=selected_format_class().get_content_type())
                response['Content-Disposition'] = f'attachment; filename="proposals.{selected_format_class().get_extension()}"'
                return response
        else:
            form = ExportFieldsForm()

        context = {
            'form': form,
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
        }
        return render(request, 'admin/export_selected.html', context)

    def export_selected_action(self, request, queryset):
        selected_ids = request.POST.getlist(ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect(reverse('admin:export_selected') + '?' + '&'.join([f'id={id}' for id in selected_ids]))

    export_selected_action.short_description = "Export selected proposals"

    def has_poster_attachment(self, obj):
        return bool(obj.poster_attachment)
    has_poster_attachment.boolean = True
    has_poster_attachment.short_description = 'Poster file?'

    def list_speakers(self, obj):
        return ", ".join([speaker.username for speaker in obj.speakers.all()])
    list_speakers.short_description = 'Speakers'

admin.site.register(Proposal, TalkAdmin)


class ConfirmedSpeakerAdmin(admin.ModelAdmin):
    """Read-only listing of confirmed speakers (accepted proposal + speaker accepted)."""

    list_display = (
        "title",
        "talk_type",
        "talk_category",
        "speaker_name",
        "speaker_username",
        "speaker_email",
        "speaker_country",
        "speaker_profession",
        "speaker_organisation",
        "photo_preview",
        "photo_download",
    )
    list_filter = ("talk_type", "talk_category", "event_year")
    search_fields = (
        "title",
        "user__username",
        "user__email",
        "user__user_profile__name",
        "user__user_profile__surname",
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(status="A", user_response="A")
            .select_related("user", "user__user_profile")
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        # Allow opening the list; there is no per-row change form to edit here.
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def _profile(self, obj):
        return getattr(obj.user, "user_profile", None)

    def _photo_url(self, obj):
        profile = self._profile(obj)
        if not profile:
            return None
        if profile.profile_image:
            return profile.profile_image.url
        if profile.link_to_speaker_image:
            return profile.link_to_speaker_image
        return None

    @admin.display(description="Speaker")
    def speaker_name(self, obj):
        profile = self._profile(obj)
        if profile:
            full_name = profile.get_full_name().strip()
            if full_name:
                return full_name
        return obj.user.username

    @admin.display(description="Username", ordering="user__username")
    def speaker_username(self, obj):
        return obj.user.username

    @admin.display(description="Email", ordering="user__email")
    def speaker_email(self, obj):
        return obj.user.email or "—"

    @admin.display(description="Country")
    def speaker_country(self, obj):
        profile = self._profile(obj)
        if profile and profile.country:
            return profile.country.name
        return "—"

    @admin.display(description="Profession")
    def speaker_profession(self, obj):
        profile = self._profile(obj)
        if profile and profile.profession:
            return profile.profession
        return "—"

    @admin.display(description="Organisation")
    def speaker_organisation(self, obj):
        profile = self._profile(obj)
        if profile and profile.organization:
            return profile.organization
        return "—"

    @admin.display(description="Photo")
    def photo_preview(self, obj):
        url = self._photo_url(obj)
        if not url:
            return "—"
        return format_html(
            '<img src="{}" style="height:60px;width:60px;object-fit:cover;'
            'border-radius:4px;" alt="speaker photo" />',
            url,
        )

    @admin.display(description="Download")
    def photo_download(self, obj):
        if not self._photo_url(obj):
            return "—"
        info = self.model._meta.app_label, self.model._meta.model_name
        download_url = reverse("admin:%s_%s_download_photo" % info, args=[obj.pk])
        return format_html('<a class="button" href="{}">Download photo</a>', download_url)

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/download-photo/",
                self.admin_site.admin_view(self.download_photo_view),
                name="%s_%s_download_photo" % info,
            ),
        ]
        return custom_urls + urls

    def download_photo_view(self, request, object_id):
        if not self.has_view_permission(request):
            raise PermissionDenied
        object_id = unquote(object_id)
        obj = get_object_or_404(self.get_queryset(request), pk=object_id)
        profile = self._profile(obj)
        if profile and profile.profile_image:
            try:
                filename = profile.profile_image.name.rsplit("/", 1)[-1]
                return FileResponse(
                    profile.profile_image.open("rb"),
                    as_attachment=True,
                    filename=filename,
                )
            except FileNotFoundError:
                raise Http404("Speaker photo file is missing.")
        if profile and profile.link_to_speaker_image:
            # External image URL — redirect the browser to it.
            return HttpResponseRedirect(profile.link_to_speaker_image)
        raise Http404("This speaker has no photo.")


admin.site.register(ConfirmedSpeaker, ConfirmedSpeakerAdmin)







class CFPSubmissionPeriodAdmin(admin.ModelAdmin):
    list_display = ('event_year', 'submission_type', 'start_date', 'end_date', 'is_active_period')
    list_filter = ('event_year', 'submission_type')
    search_fields = ('event_year__year',)

    def is_active_period(self, obj):
        return obj.is_active()
    is_active_period.boolean = True
    is_active_period.short_description = 'Is active?'

admin.site.register(CFPSubmissionPeriod, CFPSubmissionPeriodAdmin)

class SpeakAdmin(admin.ModelAdmin):
    list_display = ('title', 'date_created')  
    ordering = ['-date_created']

admin.site.register(Speak, SpeakAdmin)

class SpeakerInvitationAdmin(admin.ModelAdmin):
    list_display = ('talk', 'invitee', 'status', 'invitation_sent')  
    ordering = ['-invitation_sent']

admin.site.register(SpeakerInvitation, SpeakerInvitationAdmin)

class ProposingTalkAdmin(admin.ModelAdmin):
    list_display = ('title', 'date_created')  
    ordering = ['-date_created']

admin.site.register(Proposing_talk, ProposingTalkAdmin)

class ReviewerAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_email', 'review_load', 'is_active', 'assignment_count']
    list_editable = ['review_load', 'is_active']
    list_filter = ['review_load', 'is_active']
    search_fields = ['user__username', 'user__email']
    actions = ['run_assignment_for_latest_year_action']

    def get_email(self, obj):
        return obj.user.email
    get_email.admin_order_field = 'user__email'
    get_email.short_description = 'Email Address'

    def assignment_count(self, obj):
        return obj.assignments.count()
    assignment_count.short_description = 'Current assignments'

    def run_assignment_for_latest_year_action(self, request, queryset):
        """Run assignment for the most recent event year using the selected reviewers."""
        from home.models import EventYear
        latest_year = EventYear.objects.order_by('-year').first()
        if not latest_year:
            self.message_user(request, "No event year configured.", level=messages.ERROR)
            return

        result = assign_proposals(
            latest_year,
            reviewers=queryset,
            assigned_by=request.user,
        )

        if result['created']:
            self.message_user(
                request,
                f"Created {result['created']} new review assignment(s) for {latest_year.year}.",
                level=messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                "No new assignments created (everything is already assigned).",
                level=messages.INFO,
            )

        if result['unassignable']:
            self.message_user(
                request,
                f"{len(result['unassignable'])} proposal(s) could not be assigned. "
                f"IDs: {', '.join(str(pid) for pid in result['unassignable'])}",
                level=messages.WARNING,
            )

    run_assignment_for_latest_year_action.short_description = (
        "Run assignment for the latest event year (using selected reviewers)"
    )

admin.site.register(Reviewer, ReviewerAdmin)


class ReviewAssignmentAdmin(admin.ModelAdmin):
    list_display = ['reviewer', 'proposal', 'event_year', 'assigned_at', 'assigned_by', 'has_review']
    list_filter = ['proposal__event_year', 'reviewer__review_load', 'assigned_at']
    search_fields = [
        'reviewer__user__username',
        'reviewer__user__email',
        'proposal__title',
    ]
    autocomplete_fields = ['reviewer', 'proposal']
    readonly_fields = ['assigned_at']

    def event_year(self, obj):
        return obj.proposal.event_year
    event_year.admin_order_field = 'proposal__event_year__year'
    event_year.short_description = 'Event year'

    def has_review(self, obj):
        return Review.objects.filter(reviewer=obj.reviewer, talk=obj.proposal).exists()
    has_review.boolean = True
    has_review.short_description = 'Reviewed?'

admin.site.register(ReviewAssignment, ReviewAssignmentAdmin)

class SubScoreInline(admin.TabularInline):
    model = SubScore
    fields = ['speaker_expertise', 'depth_of_topic', 'relevancy', 'value_or_impact']
    readonly_fields = ['speaker_expertise', 'depth_of_topic', 'relevancy', 'value_or_impact']
    can_delete = False
    extra = 0




class ReviewAdmin(admin.ModelAdmin):
    list_display = ['talk', 'get_reviewer_name', 'average_score', 'get_hashid', 'short_comment', 'has_multiple_submissions', 'number_of_submissions', 'rank_in_submissions']
    
    def get_reviewer_name(self, obj):
        return obj.reviewer.user.get_full_name() or obj.reviewer.user.username
    get_reviewer_name.admin_order_field = 'reviewer__user__username'  # Allows column order sorting by username
    get_reviewer_name.short_description = 'Reviewer Name'  # Renames column head

    def get_hashid(self, obj):
        return str(obj.id)  # Assuming 'id' is a Hashid field
    get_hashid.admin_order_field = 'id'  # Allows column order sorting
    get_hashid.short_description = 'ID'  # Renames column head

    def short_comment(self, obj):
        return obj.comments[:50] + '...' if len(obj.comments) > 50 else obj.comments
    short_comment.short_description = 'Comments'

    def average_score(self, obj):
        return obj.average_score()  # Assuming 'average_score' is a method on the Review model
    average_score.admin_order_field = 'average_score'  # Allows column order sorting
    average_score.short_description = 'Average Score'

    def has_multiple_submissions(self, obj):
        user = obj.talk.user
        event_year = obj.talk.event_year
        count = Proposal.objects.filter(user=user, event_year=event_year).count()
        return count > 1
    has_multiple_submissions.short_description = 'Multiple Submissions'
    has_multiple_submissions.boolean = True

    def number_of_submissions(self, obj):
        user = obj.talk.user
        event_year = obj.talk.event_year
        return Proposal.objects.filter(user=user, event_year=event_year).count()
    number_of_submissions.short_description = 'Number of Submissions'

    def rank_in_submissions(self, obj):
        user = obj.talk.user
        event_year = obj.talk.event_year
        proposals = Proposal.objects.filter(user=user, event_year=event_year)
        sorted_proposals = sorted(proposals, key=lambda p: p.average_review_score(), reverse=True)
        rank = next((i for i, p in enumerate(sorted_proposals, 1) if p == obj.talk), None)
        return rank
    rank_in_submissions.short_description = 'Rank in Submissions'

    inlines = [SubScoreInline]

admin.site.register(Review, ReviewAdmin)




class RecordingAdmin(admin.ModelAdmin):
    list_display = ('title', 'date_created')  
    ordering = ['-date_created']

admin.site.register(Recording, RecordingAdmin)



class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'document_type', 'proposal', 'uploaded_at')
    list_filter = ('document_type', 'uploaded_at', 'proposal__event_year')
    search_fields = ('name', 'proposal__title', 'proposal__user__username')
    date_hierarchy = 'uploaded_at'
    ordering = ('-uploaded_at',)

    def proposal_title(self, obj):
        return obj.proposal.title
    proposal_title.short_description = 'Proposal Title'

    def proposal_user(self, obj):
        return obj.proposal.user.username
    proposal_user.short_description = 'Uploaded By'

admin.site.register(Document, DocumentAdmin)