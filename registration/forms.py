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
from .users import UserModel
from .users import UsernameField
from .utils import _
from django.utils.translation import gettext_lazy as _

# Third Parties
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit 
  
from django_countries.widgets import CountrySelectWidget  
from django_recaptcha.fields import ReCaptchaField 
from django_recaptcha.widgets import ReCaptchaV2Invisible

User = UserModel()


from .email_uniqueness import EMAIL_IN_USE_MESSAGE, email_address_in_use
from .models import Profile


class RegistrationForm(UserCreationForm):
    """
    Form for registering a new user account.

    Validates that the requested username is not already in use, and
    requires the password to be entered twice to catch typos.

    Subclasses should feel free to add any additional validation they
    need, but should avoid defining a ``save()`` method -- the actual
    saving of collected user data is delegated to the active
    registration backend.

    """
    required_css_class = 'required'
    email = forms.EmailField(label=_("E-mail"))
    captcha = ReCaptchaField()

    class Meta:
        model = User
        fields = (UsernameField(), "email")


class RegistrationFormUsernameLowercase(RegistrationForm):
    """
    A subclass of :class:`RegistrationForm` which enforces unique case insensitive
    usernames, make all usernames to lower case.

    """
    def clean_username(self):
        username = self.cleaned_data.get('username', '').lower()
        if User.objects.filter(**{UsernameField(): username}).exists():
            raise forms.ValidationError(_('A user with that username already exists.'))

        return username


class RegistrationFormTermsOfService(RegistrationForm):
    """
    Subclass of ``RegistrationForm`` which adds a required checkbox
    for agreeing to a site's Terms of Service.

    """
    tos = forms.BooleanField(widget=forms.CheckboxInput,
                             label=_('I have read and agree to the Terms of Service'),
                             error_messages={'required': _("You must agree to the terms to register")})


class RegistrationFormUniqueEmail(RegistrationForm):
    """
    Subclass of ``RegistrationForm`` which enforces uniqueness of
    email addresses.

    """
    def clean_email(self):
        email = self.cleaned_data["email"]
        if email_address_in_use(email):
            raise forms.ValidationError(EMAIL_IN_USE_MESSAGE)
        return email


class RegistrationFormNoFreeEmail(RegistrationForm):
    """
    Subclass of ``RegistrationForm`` which disallows registration with
    email addresses from popular free webmail services; moderately
    useful for preventing automated spam registrations.

    To change the list of banned domains, subclass this form and
    override the attribute ``bad_domains``.

    """
    bad_domains = [ 'email.com', 
                    ]

    def clean_email(self):
        """
        Check the supplied email address against a list of known free
        webmail domains.

        """
        email_domain = self.cleaned_data['email'].split('@')[1]
        if email_domain in self.bad_domains:
            raise forms.ValidationError(_("Registration using free email addresses is prohibited. Please supply a different email address."))
        return self.cleaned_data['email']


class ResendActivationForm(forms.Form):
    required_css_class = 'required'
    email = forms.EmailField(label=_("E-mail"))


class UpdateForm(forms.ModelForm):
    captcha = ReCaptchaField()

    class Meta:
        model = Profile
        fields = ('name', 'surname', 'profile_image', 'profession', 'organization', 'biography', 'twitter_handle', 'github_username', 'linkedin', 'contact_number', 'website', 'city', 'country',)
        widgets = {
            'country': CountrySelectWidget(),
            # Plain file input (no "Currently/Clear" clutter) — rendered inside
            # the custom upload box in profiles/update.html.
            'profile_image': forms.FileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super(UpdateForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'id-Crispy_UpdateForm'
        self.helper.form_class = 'form-horizontal'
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'name', 'surname', 'profession', 'organization', 'biography',
            'twitter_handle', 'github_username', 'linkedin',
            'contact_number', 'website', 'city', 'country', 'captcha',
        )

class UserForm(forms.ModelForm):
    captcha = ReCaptchaField()

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email',)

    def clean_email(self):
        email = self.cleaned_data["email"]
        exclude_user = self.instance if self.instance.pk else None
        if email_address_in_use(email, exclude_user=exclude_user):
            raise forms.ValidationError(EMAIL_IN_USE_MESSAGE)
        return email

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'id-Crispy_UserForm'
        self.helper.form_class = 'form-horizontal'
        self.helper.add_input(Submit('update', 'Update Profile'))


class PasswordForm(PasswordChangeForm):
    captcha = ReCaptchaField()

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(PasswordForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'id-Crispy_UserForm'
        self.helper.form_class = 'form-horizontal'
        self.helper.Layout(
            'old_password',
            'password1',
            'password2'
        )
        self.helper.add_input(Submit('update', 'Update Profile'))

