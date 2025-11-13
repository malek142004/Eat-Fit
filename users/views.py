# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from .forms import CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect

# ----------------------
# Pages principales
# ----------------------
def index(request):
    return render(request, 'ahana-master/index.html')

def home(request):
    return render(request, 'ahana-master/home.html')

def about(request):
    return render(request, 'ahana-master/about.html')

def services(request):
    return render(request, 'ahana-master/services.html')

def contact(request):
    return render(request, 'ahana-master/contact.html')

def classes(request):
    return render(request, 'ahana-master/classes-details.html')

def blog(request):
    return render(request, 'ahana-master/blog.html')


# ----------------------
# Page Auth (Sign Up + Sign In)
# ----------------------
@csrf_protect
def auth_view(request):
    signup_form = CustomUserCreationForm()
    login_form = AuthenticationForm()

    if request.method == "POST":
        if "signup" in request.POST:
            signup_form = CustomUserCreationForm(request.POST, request.FILES)
            if signup_form.is_valid():
                user = signup_form.save()
                login(request, user)  # Connecte automatiquement après inscription
                return redirect('users:index')  # Redirige vers la page d'accueil
        elif "signin" in request.POST:
            login_form = AuthenticationForm(request, data=request.POST)
            if login_form.is_valid():
                user = login_form.get_user()
                login(request, user)
                return redirect('users:index')  # Redirige vers la page d'accueil

    return render(request, "user.html", {
        "signup_form": signup_form,
        "login_form": login_form
    })


# ----------------------
# Page profil (accessible seulement aux utilisateurs connectés)
# ----------------------
from .forms import CustomUserUpdateForm


@login_required
def profile_view(request):
    user = request.user
    if request.method == "POST":
        form = CustomUserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('users:index')  # redirige vers l'accueil après enregistrement
    else:
        form = CustomUserUpdateForm(instance=user)

    return render(request, 'ahana-master/profile.html', {'form': form})
# ----------------------
# Déconnexion
# ----------------------
def logout_view(request):
    logout(request)
    return redirect('users:index')  # Redirige vers la page d'accueil
