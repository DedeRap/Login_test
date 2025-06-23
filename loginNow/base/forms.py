# forms.py
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox
from decouple import config
from django import forms
from django.forms import ModelForm
from .models import Profile
import bleach
from allauth.account.forms import LoginForm

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control','placeholder': 'Masukkan Email anda'}))
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)

    class Meta:
        model = User
        fields = ("username", "email") # , "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['username', 'password1', 'password2']:
            self.fields[field_name].widget.attrs.update({
                'class': 'form-control'
            })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email ini telah digunakan! Mohon menggunakan Email yang lainnya.")
        return email

class CustomLoginForm(LoginForm):
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)

    def __init__(self, *args, **kwargs):
        super(CustomLoginForm, self).__init__(*args, **kwargs)
        self.fields['login'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Username atau Email'}
        )
        self.fields['password'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Kata Sandi'}
        )
    
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'displayname', 'info']

    def clean_image(self):
        image = self.cleaned_data.get('image', False)
        if image:
            if image.size > 3 * 1024 * 1024:
                raise forms.ValidationError("Ukuran gambar tidak boleh lebih dari 3MB!")
        return image
    
    def clean_info(self):
        info_text = self.cleaned_data.get('info', '')
        return bleach.clean(info_text, strip=True)
    
    def clean_displayname(self):
        displayname_text = self.cleaned_data.get('displayname', '')
        return bleach.clean(displayname_text, strip=True)