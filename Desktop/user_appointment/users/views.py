# users/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest

from .forms import CustomUserCreationForm, CustomAuthenticationForm, CustomUserUpdateForm, NutritionistForm
from .models import CustomUser as User, Nutritionist

# ----------------------
# Pages principales
# ----------------------

# ----------------------
# backoffice
# ----------------------


def backoffice_tables(request):
    return render(request, 'backoffice/tables_user.html')



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
                return redirect("main:backoffice_dashboard")
            else:
                return redirect("main:index")
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
                return redirect("main:backoffice_dashboard")
            else:
                return redirect("main:index")
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
                return redirect('main:index')
            else:
                messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")

        elif 'change_password' in request.POST:
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # garde l'utilisateur connecté
                messages.success(request, "Mot de passe mis à jour avec succès ✅")
                return redirect('main:index')
            else:
                messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")

    else:
        profile_form = CustomUserUpdateForm(instance=user)
        password_form = PasswordChangeForm(user)

    return render(request, 'main/profile.html', {
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
    return redirect('main:index')

@login_required
def delete_profile(request):
    user = request.user
    if request.method == "POST":
        user.delete()
        messages.success(request, "Votre profil a été supprimé avec succès.")
        return redirect('main:index')  # Redirige vers l'accueil
    return render(request, 'confirm_delete.html')  # Page de confirmation


User = get_user_model()

def users_list(request):
    users = User.objects.all()
    return render(request, 'backoffice/tables_user.html', {'users': users})



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
        return redirect('users:users_list')
    return render(request, 'backoffice/modifier_utilisateur.html', {'user': user})

def supprimer_utilisateur(request, id):
    user = get_object_or_404(User, id=id)
    user.delete()
    return redirect('users:users_list')

def backoffice_login(request):
    if request.user.is_authenticated:
        if request.user.role == 'admin':
            return redirect("users:users_list")  # rediriger vers dashboard
        else:
            messages.error(request, "Vous n'êtes pas autorisé à accéder au backoffice.")
            return redirect('main:index')

    if request.method == "POST":
        email = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            if user.role == 'admin':
                login(request, user)
                return redirect("users:users_list")
            else:
                messages.error(request, "Vous n'avez pas les droits pour le backoffice.")
        else:
            messages.error(request, "Email ou mot de passe incorrect.")

    return render(request, 'backoffice/login.html')

def backoffice_logout(request):
    logout(request)  # déconnecte l'utilisateur
    return redirect("users:login")  # redirige vers la page de login

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



# ----------------------
# CRUD Nutritionnistes
# ----------------------

def nutritionist_list(request):
    nutritionists = Nutritionist.objects.all()
    return render(request, 'main/nutritionist_list.html', {'nutritionists': nutritionists})

def nutritionist_detail(request, pk):
    nutritionist = get_object_or_404(Nutritionist, pk=pk)
    return render(request, 'main/nutritionist_detail.html', {'nutritionist': nutritionist})

@login_required
def nutritionist_create(request):
    if request.method == 'POST':
        form = NutritionistForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Nutritionist créé avec succès !")
            return redirect('users:nutritionist_list')
    else:
        form = NutritionistForm(user=request.user)  # passer user connecté

    return render(request, 'main/nutritionist_form.html', {'form': form})

@login_required
def nutritionist_update(request, pk):
    nutritionist = get_object_or_404(Nutritionist, pk=pk)
    if request.method == 'POST':
        form = NutritionistForm(request.POST, request.FILES, instance=nutritionist, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Nutritionist modifié avec succès')
            return redirect('users:nutritionist_list')
    else:
        form = NutritionistForm(instance=nutritionist, user=request.user)
    return render(request, 'main/nutritionist_form.html', {'form': form})

@require_POST
def nutritionist_delete(request, pk):
    nutritionist = get_object_or_404(Nutritionist, pk=pk)
    try:
        nutritionist.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': 'Nutritionist deleted successfully.'})
        messages.success(request, 'Nutritionist deleted successfully.')
        return redirect('users:nutritionist_list')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        messages.error(request, f'Error deleting nutritionist: {e}')
        return redirect('users:nutritionist_list') # Or render the confirm delete page with an error message




def backoffice_tables(request):
    # Pass all nutritionists to the backoffice tables view
    nutritionists = Nutritionist.objects.all()
    return render(request, 'backoffice/tables_nutritionists.html', {'nutritionists': nutritionists})

def backoffice_nutritionist_delete(request, pk):
    """
    Supprime un nutritionniste uniquement via POST.
    Redirige vers la table backoffice après suppression.
    """
    if request.method == 'POST':
        nutritionist = get_object_or_404(Nutritionist, pk=pk)
        nutritionist.delete()
        messages.success(request, f'Le nutritionniste {nutritionist.full_name} a été supprimé.')
        return redirect('users:backoffice_nutritionist_list')


def backoffice_nutritionist_update(request, pk):
    """Edit a nutritionist from the backoffice and stay in the backoffice after saving."""
    nutritionist = get_object_or_404(Nutritionist, pk=pk)
    if request.method == 'POST':
        form = NutritionistForm(request.POST, request.FILES, instance=nutritionist)
        if form.is_valid():
            form.save()
            messages.success(request, 'nutritionniste modifié avec succès')
            return redirect('users:backoffice_tables')
    else:
        form = NutritionistForm(instance=nutritionist)
    return render(request, 'backoffice/nutritionist_form.html', {'form': form, 'nutritionist': nutritionist})


def backoffice_nutritionist_create(request):
    """Create a nutritionist from the backoffice and stay in the backoffice after saving."""
    if request.method == 'POST':
        form = NutritionistForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'nutritionniste ajouté avec succès')
            return redirect('users:backoffice_tables')
    else:
        form = NutritionistForm()
    return render(request, 'backoffice/nutritionist_form.html', {'form': form})


def backoffice_nutritionist_detail(request, pk):
    nutritionist = get_object_or_404(Nutritionist, pk=pk)
    return render(request, 'backoffice/BOnutritionist_detail.html', {'nutritionist': nutritionist})
