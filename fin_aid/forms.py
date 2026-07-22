"""
Forms and validation code for user registration.

Note that all of these forms assume Django's bundle default ``User``
model; since it's not possible for a form to anticipate in advance the
needs of custom user models, you will need to write your own forms if
you're using a custom model.

"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, UserChangeForm

from django.contrib.auth.models import User
from registration.users import UserModel
from registration.users import UsernameField
from registration.utils import _
from django.utils.translation import gettext_lazy as _

# Third Parties
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django_countries.widgets import CountrySelectWidget
from django_recaptcha.fields import ReCaptchaField


User = UserModel()


from datetime import date

from crispy_forms.layout import Layout, Fieldset, Field, HTML

from .models import (
    Fin_aid,
    OpportunityGrantApplication,
    FinAidApplicationReview,
    RegionalGrantApplication,
    RegionalGrantApplicationReview,
    REGIONAL_GRANT_INTEREST_CHOICES,
)


class Fin_aidForm(forms.ModelForm):
    captcha = ReCaptchaField()

    class Meta:
        model = Fin_aid
        fields = ('title',)

    def __init__(self, *args, **kwargs):
        super(Fin_aidForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'id-Crispy_Fin_aidForm'
        self.helper.form_class = 'form-horizontal'
        self.helper.add_input(Submit('update', 'Fin_aid '))


class OpportunityGrantApplicationForm(forms.ModelForm):
    class Meta:
        model = OpportunityGrantApplication
        fields = (
            'legal_name',
            'country',
            'support_type',
            'budget_narrative',
            'why_need_support',
            'community_contribution',
            'additional_notes',
        )
        widgets = {
            'country': CountrySelectWidget(attrs={'class': 'w-full max-w-lg rounded-lg border border-gray-300 px-3 py-2'}),
            'budget_narrative': forms.Textarea(attrs={'rows': 4}),
            'why_need_support': forms.Textarea(attrs={'rows': 4}),
            'community_contribution': forms.Textarea(attrs={'rows': 4}),
            'additional_notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class OpportunityGrantResponseForm(forms.ModelForm):
    class Meta:
        model = OpportunityGrantApplication
        fields = ('user_response',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user_response'].widget = forms.RadioSelect()
        self.fields['user_response'].choices = [
            ('A', _('I accept — I will attend PyCon Africa with this grant.')),
            ('R', _('I decline — I cannot accept this grant.')),
        ]
        self.fields['user_response'].label = _('Your response')
        self.fields['user_response'].required = True
        self.fields['user_response'].initial = None
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True


class FinAidApplicationReviewForm(forms.ModelForm):
    class Meta:
        model = FinAidApplicationReview
        fields = (
            'is_speaker',
            'is_organizer',
            'is_local_contributor',
            'region',
            'is_woman',
            'is_professional_cant_afford',
            'has_disability',
            'is_motivated_student',
            'is_student',
            'alignment_score',
            'grant_type',
            'amount_exceeded',
            'recommendation',
            'comments',
        )
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 5, 'class': 'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-pycon-teal focus:border-transparent'}),
            'recommendation': forms.Select(attrs={'class': 'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-pycon-teal focus:border-transparent'}),
            'region': forms.Select(attrs={'class': 'w-full max-w-xs rounded-lg border border-gray-300 px-3 py-2'}),
            'alignment_score': forms.Select(attrs={'class': 'w-full max-w-xs rounded-lg border border-gray-300 px-3 py-2'}),
            'grant_type': forms.RadioSelect(),
            'amount_exceeded': forms.NumberInput(attrs={
                'class': 'w-full max-w-xs rounded-lg border border-gray-300 px-3 py-2 text-sm',
                'placeholder': 'e.g. 150.00',
                'min': '0',
                'step': '0.01',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.fields['region'].choices = [('', '--- Select region ---')] + list(
            FinAidApplicationReview.REGION_CHOICES
        )
        self.fields['region'].required = True
        self.fields['grant_type'].required = True

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('is_motivated_student') and cleaned.get('is_student'):
            raise forms.ValidationError(
                'Select either Motivated student or Student — not both.'
            )
        return cleaned


TEXT_INPUT_CLASS = 'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-pycon-teal focus:border-transparent'
TEXTAREA_CLASS = TEXT_INPUT_CLASS
SELECT_CLASS = TEXT_INPUT_CLASS
CHECKBOX_CLASS = 'h-4 w-4 rounded border-gray-300 text-pycon-teal focus:ring-pycon-teal'


class RegionalGrantApplicationForm(forms.ModelForm):
    interests = forms.MultipleChoiceField(
        choices=REGIONAL_GRANT_INTEREST_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': CHECKBOX_CLASS}),
        label='Areas of interest',
        help_text='Select all areas that interest you',
    )
    captcha = ReCaptchaField()

    class Meta:
        model = RegionalGrantApplication
        fields = (
            'country',
            'full_name',
            'email',
            'phone',
            'city',
            'gender',
            'dob',
            'is_18',
            'status',
            'field',
            'python_level',
            'python_duration',
            'why_attend',
            'hope_to_gain',
            'interests',
            'community',
            'contributions',
            'knowledge_sharing',
            'attend_all',
            'represent_professionally',
            'share_publicly',
            'represent_how',
            'has_national_id',
            'has_passport',
            'can_travel',
            'can_cover_expenses_with_ticket',
            'can_attend_with_travel_support',
            'financial_support',
            'additional_notes',
        )
        widgets = {
            'country': forms.Select(attrs={'class': SELECT_CLASS}),
            'full_name': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': 'Your full name', 'autocomplete': 'name'}),
            'email': forms.EmailInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': 'your.email@example.com', 'autocomplete': 'email'}),
            'phone': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': '+256 700 000 000', 'autocomplete': 'tel'}),
            'city': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': 'Your city', 'autocomplete': 'address-level2'}),
            'gender': forms.Select(attrs={'class': SELECT_CLASS}),
            'dob': forms.DateInput(attrs={'class': TEXT_INPUT_CLASS, 'type': 'date'}),
            'is_18': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'status': forms.Select(attrs={'class': SELECT_CLASS}),
            'field': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': 'e.g., Computer Science, Software Development'}),
            'python_level': forms.Select(attrs={'class': SELECT_CLASS}),
            'python_duration': forms.Select(attrs={'class': SELECT_CLASS}),
            'why_attend': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 4, 'placeholder': 'Tell us why you want to attend...'}),
            'hope_to_gain': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 4, 'placeholder': 'What skills, knowledge, or connections are you looking for?'}),
            'community': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 3, 'placeholder': 'Optional: describe your involvement in tech communities'}),
            'contributions': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 3, 'placeholder': 'Optional: open source, mentoring, organizing events, etc.'}),
            'knowledge_sharing': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 3, 'placeholder': 'Optional: blogging, teaching, talks, etc.'}),
            'attend_all': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'represent_professionally': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'share_publicly': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'represent_how': forms.TextInput(attrs={'class': TEXT_INPUT_CLASS, 'placeholder': 'Optional: social media, blog, presentations, etc.'}),
            'has_national_id': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'has_passport': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'can_travel': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'can_cover_expenses_with_ticket': forms.Select(attrs={'class': SELECT_CLASS}),
            'can_attend_with_travel_support': forms.Select(attrs={'class': SELECT_CLASS}),
            'financial_support': forms.Select(attrs={'class': SELECT_CLASS}),
            'additional_notes': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'rows': 3, 'placeholder': 'Optional: anything else you want us to know'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def checkbox(field_name):
            return Field(field_name, template='2026/fin_aid/_inline_checkbox_field.html')

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            HTML('<h2 class="text-xl font-semibold text-gray-900 mt-2 mb-4">Personal Information</h2>'),
            Fieldset('', 'country', 'full_name', 'email', 'phone', 'city', 'gender', 'dob', checkbox('is_18')),
            HTML('<h2 class="text-xl font-semibold text-gray-900 mt-8 mb-4">Background &amp; Skills</h2>'),
            Fieldset('', 'status', 'field', 'python_level', 'python_duration', 'interests'),
            HTML('<h2 class="text-xl font-semibold text-gray-900 mt-8 mb-4">Motivation</h2>'),
            Fieldset('', 'why_attend', 'hope_to_gain'),
            HTML('<h2 class="text-xl font-semibold text-gray-900 mt-8 mb-4">Community &amp; Impact <span class="text-sm font-normal text-gray-500">(optional)</span></h2>'),
            Fieldset('', 'community', 'contributions', 'knowledge_sharing'),
            HTML('<h2 class="text-xl font-semibold text-gray-900 mt-8 mb-4">Commitment</h2>'),
            Fieldset(
                '',
                checkbox('attend_all'),
                checkbox('represent_professionally'),
                checkbox('share_publicly'),
                'represent_how',
            ),
            HTML('<h2 class="text-xl font-semibold text-gray-900 mt-8 mb-4">Travel &amp; Documents</h2>'),
            Fieldset(
                '',
                checkbox('has_national_id'),
                checkbox('has_passport'),
                checkbox('can_travel'),
                'can_cover_expenses_with_ticket',
                'can_attend_with_travel_support',
                'financial_support',
                'additional_notes',
                'captcha',
            ),
        )

    def clean(self):
        cleaned_data = super().clean()

        dob = cleaned_data.get('dob')
        is_18 = cleaned_data.get('is_18')

        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                raise forms.ValidationError('You must be 18 years or older to apply.')

        if not is_18:
            raise forms.ValidationError('You must confirm that you are 18 years or older.')

        if not cleaned_data.get('attend_all'):
            raise forms.ValidationError('You must confirm your ability to attend all days.')
        if not cleaned_data.get('represent_professionally'):
            raise forms.ValidationError('You must agree to represent the regional grant program professionally.')
        if not cleaned_data.get('share_publicly'):
            raise forms.ValidationError('You must agree to share your experience publicly.')

        if not cleaned_data.get('has_national_id') and not cleaned_data.get('has_passport'):
            raise forms.ValidationError('You must have either a national ID or passport.')

        return cleaned_data

    def clean_interests(self):
        interests = self.cleaned_data.get('interests')
        if not interests:
            raise forms.ValidationError('Please select at least one area of interest.')
        return ', '.join(interests)


class RegionalGrantApplicationReviewForm(forms.ModelForm):
    class Meta:
        model = RegionalGrantApplicationReview
        fields = (
            'is_community_member',
            'is_active_contributor',
            'is_knowledge_sharer',
            'python_level',
            'python_duration',
            'financial_need',
            'is_woman',
            'has_disability',
            'is_student',
            'alignment_score',
            'recommendation',
            'comments',
        )
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 5, 'class': TEXT_INPUT_CLASS}),
            'recommendation': forms.Select(attrs={'class': SELECT_CLASS}),
            'python_level': forms.Select(attrs={'class': 'w-full max-w-xs rounded-lg border border-gray-300 px-3 py-2'}),
            'python_duration': forms.Select(attrs={'class': 'w-full max-w-xs rounded-lg border border-gray-300 px-3 py-2'}),
            'financial_need': forms.Select(attrs={'class': 'w-full max-w-xs rounded-lg border border-gray-300 px-3 py-2'}),
            'alignment_score': forms.Select(attrs={'class': 'w-full max-w-xs rounded-lg border border-gray-300 px-3 py-2'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.fields['python_level'].required = True
        self.fields['python_duration'].required = True
        self.fields['financial_need'].required = True
