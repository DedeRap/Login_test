# forms.py
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox
from django import forms

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

class CaptchaLoginForm(forms.Form):
    captcha = ReCaptchaField(
        public_key='6LcnDhgrAAAAAEI4iNGeSxPBYs3CJnKCeWzuFZQI',
        private_key='6LcnDhgrAAAAAEa6FQIygGPiMhAoevBnWbmcxBB8',)