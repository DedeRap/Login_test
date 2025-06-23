# base/urls.py

from django.urls import path
from . import views

# Kita hanya mendefinisikan URL yang spesifik untuk aplikasi 'base'
urlpatterns = [
    # URL untuk halaman utama
    path("", views.home, name="home"),

    # URL untuk fitur profil
    path('profile/edit/', views.profile_edit, name='profile_edit'),

    # URL untuk alur registrasi OTP kustom Anda
    path("signup/", views.authView, name="authView"),
    path('otp-verify/', views.otp_verify, name='otp_verify'),
    path("resend-otp/", views.resend_otp, name="resend_otp"),

    # CATATAN: URL untuk login, logout, dan reset password sekarang ditangani
    # oleh 'allauth.urls' yang sudah kita sertakan di file root urls.py.
    # Anda tidak perlu mendefinisikannya lagi di sini.
    # Cukup kustomisasi template allauth jika ingin tampilan berbeda.
]