from django.urls import path, include
from .views import authView, home, logout
from django.contrib.auth import views as auth_views

#Curiga vvv
urlpatterns = [
    path("", home, name="home"),
    path("signup/", authView, name="authView"),
    #path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path("accounts/logout/", logout, name="logout"),
    path("accounts/", include("django.contrib.auth.urls")),
]