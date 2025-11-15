# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .forms import CustomUserCreationForm, CustomAuthenticationForm, CustomUserUpdateForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404, redirect
from .models import CustomUser as User


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
# backoffice
# ----------------------
def backoffice_dashboard(request):
    return render(request, 'backoffice/dashboard.html')

def backoffice_blank(request):
    return render(request, 'backoffice/blank.html')

def backoffice_cards(request):
    return render(request, 'backoffice/cards.html')

def backoffice_charts(request):
    return render(request, 'backoffice/charts.html')

def backoffice_forgot_password(request):
    return render(request, 'backoffice/forgot-password.html')

def backoffice_login(request):
    return render(request, 'backoffice/login.html')

def backoffice_register(request):
    return render(request, 'backoffice/register.html')

def backoffice_tables(request):
    return render(request, 'backoffice/tables.html')



# ----------------------
# Page Auth (Sign Up + Sign In)
# ----------------------
@csrf_protect
def auth_view(request):
    """
    Gère la page de connexion et d'inscription.
    - Si 'signup' est envoyé → inscription
    - Si 'signin' est envoyé → connexion
    """
    signup_form = CustomUserCreationForm()
    login_form = CustomAuthenticationForm()

    # 🟢 INSCRIPTION
    if request.method == "POST" and "signup" in request.POST:
        signup_form = CustomUserCreationForm(request.POST, request.FILES)
        if signup_form.is_valid():
            user = signup_form.save()
            login(request, user)
            messages.success(request, "Compte créé avec succès ! Bienvenue 👋")
            
            # Redirection selon rôle
            if user.role == "admin":
                return redirect("/backoffice/tables/")
            else:
                return redirect("users:index")
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
            login_form = CustomAuthenticationForm()  # reset form connexion

    # 🔵 CONNEXION
    elif request.method == "POST" and "signin" in request.POST:
        login_form = CustomAuthenticationForm(request, data=request.POST)
        if login_form.is_valid():
            user = login_form.get_user()
            login(request, user)
            messages.success(request, f"Bienvenue {user.nom_complet} 👋")
            
            # Redirection selon rôle
            if user.role == "admin":
                return redirect("/backoffice/tables/")
            else:
                return redirect("users:index")
        else:
            messages.error(request, "Email ou mot de passe incorrect.")
            signup_form = CustomUserCreationForm()  # reset form inscription

    return render(request, "user.html", {
        "signup_form": signup_form,
        "login_form": login_form
    })


# ----------------------
# Page profil (accessible seulement aux utilisateurs connectés)
# ----------------------
@login_required
def profile_view(request):
    user = request.user
    if request.method == "POST":
        # Formulaire de mise à jour du profil
        profile_form = CustomUserUpdateForm(request.POST, request.FILES, instance=user)
        # Formulaire de changement de mot de passe
        password_form = PasswordChangeForm(user, request.POST)

        if 'update_profile' in request.POST:
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profil mis à jour avec succès ✅")
                return redirect('users:index')
            else:
                messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")

        elif 'change_password' in request.POST:
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # garde l'utilisateur connecté
                messages.success(request, "Mot de passe mis à jour avec succès ✅")
                return redirect('users:index')
            else:
                messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")

    else:
        profile_form = CustomUserUpdateForm(instance=user)
        password_form = PasswordChangeForm(user)

    return render(request, 'ahana-master/profile.html', {
        'form': profile_form,
        'password_form': password_form
    })

# ----------------------
# Déconnexion
# ----------------------
def logout_view(request):
    """
    Déconnecte l'utilisateur et redirige vers la page d'accueil.
    """
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('users:index')

@login_required
def delete_profile(request):
    user = request.user
    if request.method == "POST":
        user.delete()
        messages.success(request, "Votre profil a été supprimé avec succès.")
        return redirect('users:index')  # Redirige vers l'accueil
    return render(request, 'confirm_delete.html')  # Page de confirmation


User = get_user_model()

def users_list(request):
    users = User.objects.all()
    return render(request, 'backoffice/tables.html', {'users': users})



def modifier_utilisateur(request, id):
    user = get_object_or_404(User, id=id)
    if request.method == "POST":
        user.nom_complet = request.POST.get('nom_complet')
        user.ville = request.POST.get('ville')
        user.num_tel = request.POST.get('num_tel')
        user.email = request.POST.get('email')
        user.role = request.POST.get('role')

        if request.FILES.get("pdp"):
            user.pdp = request.FILES["pdp"]
        user.save()
        return redirect('/backoffice/tables/')
    return render(request, 'backoffice/modifier_utilisateur.html', {'user': user})

def supprimer_utilisateur(request, id):
    user = get_object_or_404(User, id=id)
    user.delete()
    return redirect('/backoffice/tables/')

def backoffice_login(request):
    if request.user.is_authenticated:
        if request.user.role == 'admin':
            return redirect("/backoffice/tables/")  # rediriger vers dashboard
        else:
            messages.error(request, "Vous n'êtes pas autorisé à accéder au backoffice.")
            return redirect('users:index')

    if request.method == "POST":
        email = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            if user.role == 'admin':
                login(request, user)
                return redirect("/backoffice/tables/")
            else:
                messages.error(request, "Vous n'avez pas les droits pour le backoffice.")
        else:
            messages.error(request, "Email ou mot de passe incorrect.")

    return render(request, 'backoffice/login.html')

def backoffice_logout(request):
    logout(request)  # déconnecte l'utilisateur
    return redirect("/backoffice/login/")  # redirige vers la page de login

@login_required
def ajouter_utilisateur(request):
    # seulement les admins peuvent ajouter
    if request.user.role != 'admin':
        messages.error(request, "Vous n'avez pas la permission.")
        return redirect('users:users_list')

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"L'utilisateur {user.nom_complet} a été ajouté avec succès !")
            return redirect('users:users_list')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = CustomUserCreationForm()
        # Pré-remplir le rôle si demandé via GET ?role=admin
        if request.GET.get('role') == 'admin':
            form.fields['role'].initial = 'admin'

    return render(request, "backoffice/ajouter_utilisateur.html", {"form": form})