import random
import requests
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from base.forms import CustomUserCreationForm # Dari base itu sendiri!
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth.models import auth
from django.contrib.auth import logout
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from django.contrib.auth.forms import ( AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm)
from django.contrib.auth.views import PasswordContextMixin
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.tokens import default_token_generator
from django.utils.decorators import method_decorator
#from django.utils.http import is_safe_url, urlsafe_base64_decode
from django.views.decorators.csrf import csrf_protect
from django.views.generic.edit import FormView
from django.contrib.auth.views import LoginView
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'  # Pastikan sama dengan file HTML kamu

    def form_valid(self, form):
        recaptcha_response = self.request.POST.get('g-recaptcha-response')
        data = {
            'secret': settings.RECAPTCHA_PRIVATE_KEY,  # simpan di settings.py
            'response': recaptcha_response
        }
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = r.json()

        if result.get('success'):
            return super().form_valid(form)
        else:
            messages.error(self.request, 'Verifikasi reCAPTCHA gagal. Silakan centang terlebih dahulu.*')
            return self.form_invalid(form)  

class PasswordResetView(PasswordContextMixin, FormView):
    email_template_name = 'registration/password_reset_email.html'
    extra_email_context = None
    form_class = PasswordResetForm
    from_email = 'dederadeaajiprasojo@gmail.com'
    html_email_template_name = None
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    template_name = 'registration/password_reset_form.html'
    title = 'Password reset'
    token_generator = default_token_generator 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['domain'] = '127.0.0.1:8000'
        context['protocol'] = 'http'
        return context
    
    extra_email_context = {
        'domain': '127.0.0.1:8000',
        'site_name': 'base',
        'protocol': 'http',
    }

    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'token_generator': self.token_generator,
            'from_email': self.from_email,
            'email_template_name': self.email_template_name,
            'subject_template_name': self.subject_template_name,
            'request': self.request,
            'html_email_template_name': self.html_email_template_name,
            'extra_email_context': self.extra_email_context,
        }
        form.save(**opts)
        return super().form_valid(form)

    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


@login_required
@never_cache
def home(request):
    return render(request, "home.html", {})


# Signup Views and OTP
def authView(request):
    if request.method == "POST":
        #form = UserCreationForm(request.POST)
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Ambil data dari form
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            email = request.POST.get('email')  # Pastikan email ikut diambil

            otp = str(random.randint(100000, 999999))

            # Simpan semua data ke session sementara
            request.session['otp'] = otp
            request.session['registration_data'] = {
                'username': username,
                'password': password,
                'email': email,
            }
            request.session['otp_created_time'] = timezone.now().isoformat()

            # Kirim OTP ke email
            send_mail(
                'Your OTP Code',
                f'Your verification code is: {otp}',
                'dederadeaajiprasojo@gmail.com',
                [email],
                fail_silently=False,
            )

            return redirect("base:otp_verify")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})

from django.utils import timezone
from datetime import timedelta

def otp_verify(request):
    otp_time_str = request.session.get("otp_created_time")
    expiry_timestamp = None  # default, supaya tidak error di GET

    if otp_time_str:
        otp_time = timezone.datetime.fromisoformat(otp_time_str)
        expiry_time = otp_time + timedelta(minutes=5)
        expiry_timestamp = int(expiry_time.timestamp() * 1000)  # untuk JavaScript (ms)

    if request.method == "POST":
        input_code = request.POST.get("otp")
        otp_code = request.session.get("otp")
        data = request.session.get("registration_data", {})

        if not all([input_code, otp_code, otp_time_str, data]):
            return render(request, "registration/otp_verify.html", {
                "error": "Session expired or invalid data. Please sign up again.",
                "otp_expiry_timestamp": expiry_timestamp
            })

        # Cek apakah OTP sudah kadaluarsa
        if timezone.now() - otp_time > timedelta(minutes=5):
            request.session.flush()
            return render(request, "registration/otp_verify.html", {
                "error": "OTP expired. Please sign up again.",
                "otp_expiry_timestamp": 0
            })

        if input_code == otp_code:
            # Buat user sekarang karena OTP cocok
            user = User.objects.create_user(
                username=data.get("username"),
                email=data.get("email"),
                password=data.get("password")
            )
            user.is_active = True
            user.save()

            # Bersihkan session
            request.session.pop("otp", None)
            request.session.pop("registration_data", None)
            request.session.pop("otp_created_time", None)

            return redirect("base:login")
        else:
            return render(request, "registration/otp_verify.html", {
                "error": "Wrong OTP!, Please check your email and try again!",
                "otp_expiry_timestamp": expiry_timestamp
            })

    # Untuk GET (pertama kali buka halaman)
    return render(request, "registration/otp_verify.html", {
        "otp_expiry_timestamp": expiry_timestamp
    })

def resend_otp(request):
    data = request.session.get("registration_data", {})
    if not data:
        return redirect("base:signup")  # Redirect kalau data user nggak ada

    # Buat OTP baru
    otp = str(random.randint(100000, 999999))
    request.session['otp'] = otp
    request.session['otp_created_time'] = timezone.now().isoformat()

    # Kirim ulang ke email
    send_mail(
        'Your New OTP Code',
        f'Your new verification code is: {otp}',
        'dederadeaajiprasojo@gmail.com',
        [data.get("email")],
        fail_silently=False,
    )

    messages.success(request, "OTP has been resent to your email.")
    return redirect("base:otp_verify")

def custom_logout(request):
    logout(request)
    response = redirect('base:login')  
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def logout(request):
    auth.logout(request)
    return redirect('/')
