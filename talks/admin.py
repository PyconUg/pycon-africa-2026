# admin.py
from django.contrib import admin
from import_export import resources, fields, formats
from import_export.admin import ExportActionMixin, ImportExportModelAdmin
from .models import *
from registration.models import Profile
from .forms import ExportFieldsForm 
from django.shortcuts import render
from django.urls import path
from django.utils.html import format_html
from django.db.models import Count
from django.shortcuts import render, get_object_or_404, reverse
from django.http import HttpResponseRedirect, HttpResponse       
from django.urls import path, reverse 
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME 
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
    resource_class = ProposalResource
    list_display = ("title", "user", 'list_speakers', "talk_type", "intended_audience", "status", "user_response", 'has_poster_attachment', 'created_date', 'date_updated')
    list_editable = ["status", "user_response"]
    list_filter = ("talk_type", 'created_date', "status", "user_response")
    actions = ['export_selected_action']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export_selected/', self.admin_site.admin_view(self.export_selected), name='export_selected'),
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
    list_display = ['user', 'get_email']
    search_fields = ['user__username', 'user__email']

    def get_email(self, obj):
        return obj.user.email
    get_email.admin_order_field = 'user__email'  # Allows column order sorting
    get_email.short_description = 'Email Address'  # Renames column head

admin.site.register(Reviewer, ReviewerAdmin)

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