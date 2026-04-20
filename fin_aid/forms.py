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


from .models import Fin_aid, OpportunityGrantApplication, FinAidApplicationReview


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


class FinAidApplicationReviewForm(forms.ModelForm):
    class Meta:
        model = FinAidApplicationReview
        fields = ('recommendation', 'comments')
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
