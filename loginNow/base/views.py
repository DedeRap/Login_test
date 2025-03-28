from django.shortcuts import render,redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth.models import auth
from django.contrib.auth import logout


@login_required
@never_cache
def home(request):
    return render(request, "home.html", {})


# Create your views here.
def authView(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST or None)
        if form.is_valid():
            form.save()
            return redirect("base:login")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form" :form})

def custom_logout(request):
    logout(request)
    response = redirect('base:login')  # Ganti dengan nama URL login Anda
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def logout(request):
    auth.logout(request)
    return redirect('/')
