from talks.models import Proposal
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field
from .models import Document  
from django_recaptcha.fields import ReCaptchaField 
from django_recaptcha.widgets import ReCaptchaV2Invisible  
from .models import * 

POSTER_ALLOWED_EXTENSIONS = {'pdf', 'ppt', 'pptx', 'png', 'jpg', 'jpeg', 'gif', 'webp'}
POSTER_ALLOWED_EXTENSIONS_DISPLAY = 'PDF, PPT, PPTX, PNG, JPG, JPEG, GIF, WEBP'

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
 

class PosterProposalForm(forms.ModelForm):
    captcha = ReCaptchaField()

    class Meta:
        model = Proposal
        fields = ('title', 'talk_category', 'intended_audience', 'elevator_pitch', 'talk_abstract', 'anything_else_you_want_to_tell_us', 'special_requirements', 'poster_attachment', 'recording_release')
        widgets = {
            'elevator_pitch': forms.Textarea(attrs={'class': 'w-full', 'rows': 5}),
            'talk_abstract': forms.Textarea(attrs={'class': 'w-full', 'rows': 6}),
            'anything_else_you_want_to_tell_us': forms.Textarea(attrs={'class': 'w-full', 'rows': 4}),
            'special_requirements': forms.Textarea(attrs={'class': 'w-full', 'rows': 4}),
            'poster_attachment': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-700 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none file:mr-4 file:py-2 file:px-4 file:rounded-l-lg file:border-0 file:text-sm file:font-semibold file:bg-pycon-teal file:text-white hover:file:bg-teal-700 p-2',
                'accept': '.pdf,.ppt,.pptx,.png,.jpg,.jpeg,.gif,.webp',
            }),
        }

    def __init__(self, *args, **kwargs):
        kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['talk_category'].label = 'Category'
        self.fields['talk_abstract'].label = 'Poster Abstract'
        self.fields['elevator_pitch'].label = 'Elevator Pitch'
        self.fields['elevator_pitch'].help_text = 'Describe your poster to your targeted audience.'
        self.fields['poster_attachment'].help_text = (
            f'Upload your poster file. Accepted formats: {POSTER_ALLOWED_EXTENSIONS_DISPLAY}. '
            'Uploading a new file will replace the previous one.'
        )
        self.fields['recording_release'].help_text = (
            'By submitting your poster proposal, you agree to give permission to the conference organizers '
            'to record, edit, and release audio and/or video of your presentation. '
            'If you do not agree to this, please uncheck this box.'
        )
        self.helper = FormHelper()
        self.helper.form_id = 'id-Crispy_PosterProposalForm'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.add_input(Submit('submit', 'Submit Poster'))

    def clean_poster_attachment(self):
        attachment = self.cleaned_data.get('poster_attachment')
        if attachment and hasattr(attachment, 'name'):
            ext = attachment.name.rsplit('.', 1)[-1].lower() if '.' in attachment.name else ''
            if ext not in POSTER_ALLOWED_EXTENSIONS:
                raise forms.ValidationError(
                    f'Unsupported file type ".{ext}". '
                    f'Please upload one of: {POSTER_ALLOWED_EXTENSIONS_DISPLAY}.'
                )
        return attachment


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