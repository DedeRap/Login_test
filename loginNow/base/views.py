import random
import requests
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from base.forms import CustomUserCreationForm # Dari base itu sendiri!
from django.views.decorators.http import require_http_methods
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
from django.urls import reverse
from allauth.account.utils import send_email_confirmation
from django.contrib.auth.views import redirect_to_login
from .forms import *
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.models import EmailAddress
from django.shortcuts import resolve_url
from django.contrib.auth import get_user_model
from .forms import ProfileForm
from .forms import CustomLoginForm

User = get_user_model()
class CustomAccountAdapter(DefaultAccountAdapter):
    def get_signup_redirect_url(self, request):
        return resolve_url("profile-onboarding") 
    
    
class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        email = sociallogin.account.extra_data.get("email")
        
        if not email:
            return
        
        if not sociallogin.is_existing:
            existing_user = User.objects.filter(email=email).first()
            if existing_user:
                sociallogin.connect(request, existing_user)
        
        if sociallogin.is_existing: 
            user = sociallogin.user
            email_address, created = EmailAddress.objects.get_or_create(user=user, email=email)
            if not email_address.verified:
                email_address.verified = True
                email_address.save()
                
                
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        email = user.email
        email_address, created = EmailAddress.objects.get_or_create(user=user, email=email)
        if not email_address.verified:
            email_address.verified = True
            email_address.save()
            
        return user

class CustomLoginView(LoginView):
    """
    View login ini sekarang menggunakan form kustom yang sudah
    menangani validasi reCAPTCHA secara otomatis.
    """
    template_name = 'account/login.html'
    form_class = CustomLoginForm  # <-- INI BAGIAN KUNCINYA!  

class PasswordResetView(PasswordContextMixin, FormView):
    email_template_name = 'account/password_reset_email.html'
    extra_email_context = None
    form_class = PasswordResetForm
    from_email = 'dederadeaajiprasojo@gmail.com'
    html_email_template_name = None
    subject_template_name = 'account/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    template_name = 'account/password_reset_form.html'
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

@login_required
def profile_edit(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil Anda telah berhasil diperbarui!')
            return redirect('home')
    else:
        form = ProfileForm(instance=profile)
        
    return render(request, 'profile_edit.html', {'form': form})


# Signup Views and OTP
@never_cache
@require_http_methods(["GET", "POST"])
def authView(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False) # Buat objek user tanpa simpan ke DB dulu
            user.is_active = False # Set sebagai tidak aktif
            user.save() # Simpan user ke DB

            otp = str(random.randint(100000, 999999))
            email = form.cleaned_data.get('email')

            # Simpan semua data ke session sementara
            request.session['otp_user_id'] = user.id
            request.session['otp'] = otp
            request.session['otp_created_time'] = timezone.now().isoformat()
            request.session['otp_attempts'] = 0 # Inisialisasi penghitung percobaan

            # Kirim OTP ke email
            send_mail(
                'Kode OTP dari Eltekers',
                f'Kode OTP Verifikasi anda adalah: {otp}',
                'dederadeaajiprasojo@gmail.com',
                [email],
                fail_silently=False,
            )
            messages.success(request, f"Kode OTP telah dikirim ke {email}. Mohon periksa email Anda.")
            return redirect("otp_verify")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = CustomUserCreationForm()
    return render(request, "account/signup.html", {"form": form})

@never_cache
def otp_verify(request):
    otp_time_str = request.session.get("otp_created_time")
    user_id = request.session.get("otp_user_id")
    
    if not all([otp_time_str, user_id]):
        messages.error(request, "Sesi tidak valid. Mohon lakukan pendaftaran ulang.")
        return redirect('signup')
    
    otp_time = timezone.datetime.fromisoformat(otp_time_str)
    expiry_time = otp_time + timedelta(minutes=5)
    expiry_timestamp = int(expiry_time.timestamp() * 1000)

    if request.method == "POST":
        input_code = request.POST.get("otp")
        otp_code = request.session.get("otp")
        dattempts = request.session.get('otp_attempts', 0)

        # Cek apakah OTP sudah kadaluarsa
        if timezone.now() > expiry_time:
            request.session.flush()
            messages.error(request, "OTP sudah kadaluarsa. Mohon lakukan pendaftaran ulang.")
            return redirect('signup')

        if input_code == otp_code:
            try:
                user = User.objects.get(id=user_id)
                user.is_active = True
                user.save()

                request.session.flush()

                messages.success(request, "Verifikasi berhasil! Akun Anda telah diaktifkan. Silahkan login.")
                return redirect("login")
            
            except User.DoesNotExist:
                messages.error(request, "Terjadi kesalahan. User tidak ditemukan.")
                return redirect('signup')
        else:
            # Jika OTP salah, tingkatkan jumlah percobaan
            attempts += 1
            request.session['otp_attempts'] = attempts

            if attempts >= 5:
                # Terlalu banyak percobaan, hapus sesi dan redirect
                user = User.objects.get(id=user_id)
                user.delete() # Hapus user yang tidak aktif agar username/email bisa dipakai lagi
                request.session.flush()
                messages.error(request, "Terlalu banyak percobaan OTP yang salah. Pendaftaran dibatalkan.")
                return redirect('signup')
            
            remaining_attempts = 5 - attempts
            messages.error(request, f"Kode OTP salah! Anda memiliki {remaining_attempts} percobaan lagi.")
            # Tetap di halaman yang sama
            return render(request, "account/otp_verify.html", { "otp_expiry_timestamp": expiry_timestamp })

    # Untuk method GET (saat halaman pertama kali dimuat)
    return render(request, "account/otp_verify.html", { "otp_expiry_timestamp": expiry_timestamp })

def resend_otp(request):
    user_id = request.session.get("otp_user_id")
    if not user_id:
        messages.error(request, "Sesi tidak valid untuk mengirim ulang OTP.")
        return redirect("signup")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User tidak ditemukan.")
        return redirect("signup")

    # Buat OTP baru
    otp = str(random.randint(100000, 999999))
    request.session['otp'] = otp
    request.session['otp_created_time'] = timezone.now().isoformat()
    request.session['otp_attempts'] = 0 # Reset percobaan

    send_mail(
        'Kode OTP Baru Anda',
        f'Kode verifikasi baru Anda adalah: {otp}',
        'dederadeaajiprasojo@gmail.com',
        [user.email], # Ambil email dari objek user
        fail_silently=False,
    )

    messages.success(request, "OTP telah dikirim ulang ke email Anda.")
    return redirect("otp_verify")

def custom_logout(request):
    auth.logout(request)
    response = redirect('login')  
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_500(request):
    return render(request, '500.html', status=500)