from . import views
from django.urls import path, include
from .views import authView, home, logout, otp_verify, resend_otp,  CustomLoginView
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from .views import PasswordResetView  # import view sendiri

app_name = 'base'

urlpatterns = [
    path("", home, name="home"),
    #path('', include('loginNow.urls', namespace='base')),
    #Make New Account
    path("signup/", authView, name="authView"),
    #OTP
    path('otp-verify/', otp_verify, name='otp_verify'),
    path("resend-otp/", views.resend_otp, name="resend_otp"),
    #Account system
    path("accounts/logout/", logout, name="logout"),
    path("accounts/login/", CustomLoginView.as_view(), name="login"),
    path("accounts/", include("django.contrib.auth.urls")), 
    path('accounts/', include('allauth.urls')), #Jaga-jaga
    #reset password urls
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html', email_template_name='registration/password_reset_email.html', subject_template_name='registration/password_reset_subject.txt', success_url='/password_reset/done/'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html', success_url = reverse_lazy('base:password_reset_complete')), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
]