from talks.models import Proposal
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field
from .models import Document  
from django_recaptcha.fields import ReCaptchaField 
from django_recaptcha.widgets import ReCaptchaV2Invisible  
from .models import * 

class ProposalForm(forms.ModelForm):
    captcha = ReCaptchaField()

    class Meta:
        model = Proposal
        fields = ('title', 'talk_type', 'talk_category', 'intended_audience', 'elevator_pitch', 'talk_abstract', 'anything_else_you_want_to_tell_us', 'special_requirements', 'recording_release')

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ProposalForm, self).__init__(*args, **kwargs)
        
        if user and not user.is_staff:
            self.fields['talk_type'].choices = [
                ('Lightning Talk', "Lightning Talk - 5 mins"),
                ('Short Talk', "Short Talk - 30 mins"),
                ('Long Talk', "Long Talk - 45 mins"),
                ('Tutorial', "Tutorial - 2 hours"),
            ]

        self.helper = FormHelper()
        self.helper.form_id = 'id-Crispy_ProposalForm'
        self.helper.form_class = 'form-horizontal'
        self.helper.add_input(Submit('submit', 'Submit'))
 

class ProposalResponseForm(forms.ModelForm):
    class Meta:
        model = Proposal
        fields = ['user_response']
        

class UpdateForm(forms.ModelForm):
    captcha = ReCaptchaField()

    class Meta:
        model = Proposal
        fields = ('title', 'talk_type', 'talk_category', 'intended_audience',  'talk_abstract',   'anything_else_you_want_to_tell_us', 'recording_release',)
 
    def __init__(self, *args, **kwargs):
        super(UpdateForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'id-Crispy_UpdateForm'
        self.helper.form_class = 'form-horizontal'
        self.helper.add_input(Submit('update', 'Update Proposal'))


class ReviewForm(forms.ModelForm):
    SCORE_CHOICES = [(i, i) for i in range(1, 6)]

    speaker_expertise = forms.ChoiceField(choices=SCORE_CHOICES, label="Speaker Expertise")
    depth_of_topic = forms.ChoiceField(choices=SCORE_CHOICES, label="Depth of Topic")
    relevancy = forms.ChoiceField(choices=SCORE_CHOICES, label="Relevancy")
    value_or_impact = forms.ChoiceField(choices=SCORE_CHOICES, label="Value or Impact")

    class Meta:
        model = Review
        fields = ['speaker_expertise', 'depth_of_topic', 'relevancy', 'value_or_impact', 'comments']


    def __init__(self, *args, **kwargs):
        super(ReviewForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('speaker_expertise', css_class='col-sm-6 col-md-3'),
                Column('depth_of_topic', css_class='col-sm-6 col-md-3'),
                Column('relevancy', css_class='col-sm-6 col-md-3'),
                Column('value_or_impact', css_class='col-sm-6 col-md-3'),
                css_class='form-row'
            ),
            Row(
                Column('comments', css_class='col-12'),
                css_class='form-row'
            ),
        )

    def save(self, commit=True):
        instance = super(ReviewForm, self).save(commit=False)
        if commit:
            instance.save()
            SubScore.objects.create(
                review=instance,
                speaker_expertise=self.cleaned_data['speaker_expertise'],
                depth_of_topic=self.cleaned_data['depth_of_topic'],
                relevancy=self.cleaned_data['relevancy'],
                value_or_impact=self.cleaned_data['value_or_impact']
            )
        return instance


class DocumentForm(forms.ModelForm):
    captcha = ReCaptchaField()

    class Meta:
        model = Document
        fields = ('name', 'document', 'document_type', 'proposal')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Brief name of the document'}),
            'document': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'proposal': forms.Select(attrs={'class': 'form-control', 'disabled': 'true'}),  # Set to disabled
        }

    def __init__(self, *args, **kwargs):
        proposal = kwargs.pop('proposal', None)  # Expecting 'proposal' to be passed as a kwarg
        super().__init__(*args, **kwargs)
        if proposal:
            self.fields['proposal'].initial = proposal
            self.fields['proposal'].disabled = True  # Make the field read-only
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            Field('name', css_class='form-control'),
            Field('document', css_class='form-control-file'),
            Field('document_type', css_class='form-control'),
            Field('proposal', css_class='form-control'),
            Submit('submit', 'Upload', css_class='btn btn-primary')
        )
 


class ExportFieldsForm(forms.Form):
    EXPORT_FIELDS_CHOICES = [
        ('title', 'Title'),
        ('talk_type', 'Talk Type'),
        ('talk_category', 'Talk Category'),
        ('elevator_pitch', 'Elevator Pitch'),
        ('talk_abstract', 'Talk Abstract'),
        ('user_email', 'Email'),
        ('user_first_name', 'First Name'),
        ('user_last_name', 'Last Name'),
        ('user_username', 'Username'),
        ('status', 'Status'),
        ('intended_audience', 'Intended Audience'),
        ('link_to_preview_video_url', 'Link to Preview Video'),
        ('anything_else_you_want_to_tell_us', 'Anything Else'),
        ('special_requirements', 'Special Requirements'),
        ('recording_release', 'Recording Release'),
        ('youtube_video_url', 'YouTube Video URL'),
        ('youtube_iframe_url', 'YouTube IFrame URL'),
        ('created_date', 'Created Date'),
        ('date_updated', 'Date Updated'),
        ('event_year', 'Event Year'),
        ('multiple_submissions', 'Multiple Submissions'),
    ]

    EXPORT_FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('xls', 'Excel (XLS)'),
        ('xlsx', 'Excel (XLSX)'),
        ('json', 'JSON'),
        ('yaml', 'YAML'),
    ]

    TALK_TYPE_CHOICES = Proposal.TALK_TYPES

    fields_to_export = forms.MultipleChoiceField(
        choices=EXPORT_FIELDS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    export_format = forms.ChoiceField(
        choices=EXPORT_FORMAT_CHOICES,
        required=True,
        widget=forms.RadioSelect
    )
    talk_types = forms.MultipleChoiceField(
        choices=TALK_TYPE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Filter by Talk Type'
    )