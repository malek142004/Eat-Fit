# users/views.py
# ----------------- Django imports -----------------
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.db.models import Q, Avg, Count
from django.utils import timezone

# ----------------- Local app imports -----------------
from .forms import (
    CustomUserCreationForm,
    CustomAuthenticationForm,
    CustomUserUpdateForm,
    NutritionistForm,
    CoachForm,
    UserForm,
    BusinessOwnerForm
)
from .models import CustomUser as User, Nutritionist, Coach, BusinessOwner

from product.models import Product
from product.forms import ProductForm

# ----------------- Python standard library imports -----------------
from datetime import datetime, timedelta, timezone
from io import BytesIO
import os

# ----------------- ReportLab imports -----------------
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import cm, inch
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RlImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors



# Create your views here.
# Pages principale
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
            login(request, user ,backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Compte créé avec succès ! Bienvenue 👋")
            
            # Redirection selon rôle
            if user.role == "admin":
                # Admin → page principale du backoffice (liste des utilisateurs)
                return redirect("users:users_list")
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
                # Admin → page principale du backoffice (liste des utilisateurs)
                return redirect("users:users_list")
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
# users/views.py




def delete_profile(request):
    if request.method == 'POST':
        user = request.user
        
        # 1. Effectuer la désactivation logique
        user.is_deleted = True
        user.deletion_date = datetime.now(timezone.utc) # Enregistre l'horodatage
        user.is_active = False # Désactive l'utilisateur pour qu'il ne puisse plus se connecter
        user.save()
        
        # 2. Déconnecter l'utilisateur
        logout(request)
        
        # 3. Rediriger vers la page d'accueil ou un message de confirmation
        return redirect('main:index') # Assurez-vous d'avoir une URL 'home' définie
        
    # Si la méthode n'est pas POST (pour afficher le formulaire de confirmation)
    return render(request, 'confirm_delete.html')

User = get_user_model()




def users_list(request):
    search = request.GET.get('search')
    role = request.GET.get('role')

    users = User.objects.all()
    active_users = User.objects.filter(is_deleted=False).order_by('id')
    
    # ------------------------------------------------------------------
    # Récupérer les utilisateurs supprimés dans les 7 derniers jours (Exemple)
    # ------------------------------------------------------------------
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    deleted_users_notifications = User.objects.filter(
        is_deleted=True,
        deletion_date__gte=seven_days_ago # Récupère ceux supprimés récemment
    ).order_by('-deletion_date')

    if role:
        users = users.filter(role=role)

    if search:
        users = users.filter(
            Q(nom_complet__icontains=search) |
            Q(email__icontains=search)
        )

    return render(request, 'backoffice/tables_user.html', {
        'users': users,
        'deleted_notifications': deleted_users_notifications,
        'search': search,
        'role': role,
    })




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

    # Autoriser seulement l'admin ou le propriétaire du profil
    if not (
        request.user.role == 'admin'
        or request.user.pk == nutritionist.pk
    ):
        messages.error(request, "Vous n'êtes pas autorisé à modifier ce nutritionniste.")
        return redirect('users:nutritionist_list')

    if request.method == 'POST':
        form = NutritionistForm(request.POST, request.FILES, instance=nutritionist, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Nutritionist modifié avec succès')
            return redirect('users:nutritionist_list')
    else:
        form = NutritionistForm(instance=nutritionist, user=request.user)
    return render(request, 'main/nutritionist_form.html', {'form': form})

@login_required
@require_POST
def nutritionist_delete(request, pk):
    nutritionist = get_object_or_404(Nutritionist, pk=pk)
    try:
        # Autoriser seulement l'admin ou le propriétaire du profil
        if not (
            request.user.role == 'admin'
            or request.user.pk == nutritionist.pk
        ):
            messages.error(request, "Vous n'êtes pas autorisé à supprimer ce nutritionniste.")
            return redirect('users:nutritionist_list')

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
# ----------------------
# CRUD Coaches

def coach_list(request):
    """
    Liste des coachs affichables sur le site (Front-end),
    avec options de filtrage par sport et de tri.
    """
    # 1. Requête de base avec les filtres obligatoires
    coaches = Coach.objects.filter(
        show_on_website=True,
        is_active=True
    ).select_related('customuser_ptr') 

    # 2. LOGIQUE DE FILTRAGE SUPPLÉMENTAIRE PAR TYPE DE SPORT
    sport_type = request.GET.get('sport') 
    
    if sport_type:
        coaches = coaches.filter(sport_type__iexact=sport_type)

    # 3. LOGIQUE DE TRI (ORDRE)
    sort_by = request.GET.get('sort', 'id') 

    # ⚠️ Correction: Gérer le cas où 'sort_by' n'est pas un champ valide pour éviter une erreur 500
    try:
        coaches = coaches.order_by(sort_by)
    except Exception:
         # Revenir à un tri par défaut si le champ de tri n'existe pas
        coaches = coaches.order_by('id') 

    # 4. Rendu de la page
    context = {
        'coaches': coaches,
        'current_sport': sport_type,
        'current_sort': sort_by,
        # ⚠️ Correction: Utiliser Coach.SPORT_CHOICES si défini dans models.py
        'all_sport_types': getattr(Coach, 'SPORT_CHOICES', []) 
    }
    
    return render(request, 'main/trainer.html', context)

# users/views.py - Fonction coach_create (Corrigée et simplifiée)


# views.py

@login_required
def coach_create(request):
    """
    Permet à un utilisateur connecté de devenir Coach sans recréer un CustomUser.
    - On utilise le CustomUser existant (request.user)
    - On crée ou met à jour l'objet Coach lié (multi-table) avec la même PK
    """
    user = request.user

    # Si l'utilisateur est déjà coach ET qu'un profil Coach existe, on le redirige vers la page d'édition
    if user.role == 'coach':
        try:
            Coach.objects.get(pk=user.pk)
            messages.info(request, "Vous êtes déjà un Coach. Vous pouvez modifier votre profil.")
            return redirect('users:coach_update', pk=user.pk)
        except Coach.DoesNotExist:
            # le rôle est 'coach' mais pas encore d'entrée dans la table Coach -> on continue la création
            pass

    if request.method == 'POST':
        # On utilise CoachForm seulement pour la validation des champs
        form = CoachForm(request.POST, request.FILES)

        if form.is_valid():
            # 1) Promouvoir l'utilisateur au rôle 'coach' sans recréer un CustomUser
            if user.role != 'coach':
                user.role = 'coach'
                # mettre à jour aussi les infos de base si besoin
                user.nom_complet = form.cleaned_data.get('nom_complet', user.nom_complet)
                user.num_tel = form.cleaned_data.get('num_tel', user.num_tel)
                user.ville = form.cleaned_data.get('ville', user.ville)
                if form.cleaned_data.get('pdp'):
                    user.pdp = form.cleaned_data['pdp']
                user.save()

            # 2) Créer ou mettre à jour l'entrée Coach liée à ce CustomUser
            coach_fields = {
                'sport_type': form.cleaned_data.get('sport_type'),
                'experience_years': form.cleaned_data.get('experience_years'),
                'location': form.cleaned_data.get('location'),
                'session_price': form.cleaned_data.get('session_price'),
                'subscription_price': form.cleaned_data.get('subscription_price'),
                'bio': form.cleaned_data.get('bio'),
                'certifications': form.cleaned_data.get('certifications'),
                'is_available': form.cleaned_data.get('is_available'),
                'show_on_website': form.cleaned_data.get('show_on_website'),
            }

            # Multi-table inheritance : on crée/maj uniquement la table enfant,
            # reliée au CustomUser existant via customuser_ptr (même PK).
            coach, created = Coach.objects.get_or_create(
                pk=user.pk,
                defaults=coach_fields,
            )
            if not created:
                for field, value in coach_fields.items():
                    setattr(coach, field, value)
                coach.save()

            messages.success(request, 'Félicitations, votre profil Coach est créé !')
            return redirect('users:coach_list')
    else:
        # Pré-remplir le formulaire avec les infos de base de l'utilisateur
        initial = {
            'email': user.email,
            'nom_complet': user.nom_complet,
            'num_tel': user.num_tel,
            'ville': user.ville,
        }
        # Si un Coach existe déjà sans rôle correctement défini, on peut aussi charger ses champs
        try:
            coach = Coach.objects.get(pk=user.pk)
            initial.update({
                'sport_type': coach.sport_type,
                'experience_years': coach.experience_years,
                'location': coach.location,
                'session_price': coach.session_price,
                'subscription_price': coach.subscription_price,
                'bio': coach.bio,
                'certifications': coach.certifications,
                'is_available': coach.is_available,
                'show_on_website': coach.show_on_website,
            })
        except Coach.DoesNotExist:
            pass

        form = CoachForm(initial=initial)

    return render(request, 'main/coach_form.html', {
        'form': form,
        'title': 'Créer votre Profil Coach'
    })
    
    
@login_required
def coach_update(request, pk):
    """Mise à jour du profil Coach (Front-end)."""
    coach = get_object_or_404(Coach, pk=pk)
    
    if request.user.pk != coach.pk and request.user.role != 'admin':
        messages.error(request, "Vous n'êtes pas autorisé à modifier ce profil.")
        return redirect('main:index')
        
    if request.method == 'POST':
        # Utiliser l'instance Coach pour la mise à jour
        form = CoachForm(request.POST, request.FILES, instance=coach)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil Coach modifié avec succès ✅')
            return redirect('users:coach_list')
    else:
        form = CoachForm(instance=coach)

    return render(request, 'main/coach_form.html', {
        'form': form,
        'title': 'Éditer le Coach',
        'coach': coach
    })

@login_required
@require_POST
def coach_delete(request, pk):
    """Suppression du profil Coach (Front-end)."""
    coach = get_object_or_404(Coach, pk=pk)
    
    if request.user.pk != coach.pk and request.user.role != 'admin':
        return HttpResponseBadRequest("Action non autorisée.")
        
    nom_complet = coach.nom_complet
    coach.delete() # Supprime l'objet Coach ET CustomUser (héritage multi-table)

    messages.success(request, f'Le profil Coach {nom_complet} a été supprimé.')
    return redirect('users:coach_list')
    
def coach_detail(request, pk):
    """Détail d'un coach (Front-end)."""
    coach = get_object_or_404(Coach, pk=pk)
    return render(request, 'main/coach_detail.html', {'coach': coach})

# ----------------------
# Backoffice CRUD Coaches
# ----------------------



def manage_coaches(request):
    # Handle search functionality
    coaches = Coach.objects.select_related('customuser_ptr').all()
    return render(request, 'backoffice/coaches/manage_coaches.html', {'coaches': coaches})





# Récupération du modèle utilisateur personnalisé (doit être CustomUser)
User = get_user_model()


@login_required(login_url='users:auth')
def add_coach(request):
    # Sécurité: Vérifier si l'utilisateur est Admin avant de procéder
    if request.user.role != 'coach': 
        messages.error(request, "Accès refusé.")
        return redirect('users:auth') # Rediriger vers un lieu sûr
        
    if request.method == 'POST':
        try:
            # --- 1. Récupération des Données ---
            full_name = request.POST.get('full_name')
            email = request.POST.get('email')
            phone_number = request.POST.get('phone_number', '')
            city = request.POST.get('city', '')
            profile_photo = request.FILES.get('profile_photo') 
            
            sport_type = request.POST.get('sport_type')
            experience_years = request.POST.get('experience_years')
            location = request.POST.get('location')
            session_price = request.POST.get('session_price')
            subscription_price = request.POST.get('subscription_price')
            bio = request.POST.get('bio', '')
            certifications = request.POST.get('certifications', '')
            is_available = request.POST.get('is_available') == 'on'
            show_on_website = request.POST.get('show_on_website') == 'on'
            
            # --- 2. Validation de base ---
            if not all([full_name, email, sport_type, experience_years, location, session_price, subscription_price]):
                messages.error(request, 'Veuillez remplir tous les champs obligatoires.')
                return redirect('backoffice:manage_coaches')
            
            # Validation d'unicité de l'email (très important)
            if User.objects.filter(email=email).exists():
                messages.error(request, f"Un utilisateur avec l'email {email} existe déjà.")
                return redirect('backoffice:manage_coaches')
            
            # Validation de la conversion de type (pour éviter les erreurs d'exécution)
            try:
                exp_years_int = int(experience_years)
                session_price_float = float(session_price)
                subscription_price_float = float(subscription_price)
            except ValueError:
                messages.error(request, "Les champs de prix et d'expérience doivent être des nombres valides.")
                return redirect('backoffice:manage_coaches')


            # --- 3. Création et Hachage ---
            

            # 💡 CRÉATION DE L'OBJET COACH (qui est aussi un CustomUser)
            # L'objet est créé en une seule étape.
            coach = Coach.objects.create(
                # Champs CustomUser
                email=email,
                nom_complet=full_name,
                num_tel=phone_number,
                ville=city,
                pdp=profile_photo,
                role='Coach',  # Définir le rôle explicitement
                
                # Champs Coach
                sport_type=sport_type,
                experience_years=exp_years_int, 
                session_price=session_price_float,
                subscription_price=subscription_price_float,
                location=location,
                bio=bio,
                certifications=certifications,
                is_available=is_available,
                show_on_website=show_on_website
            )

            # Il est ESSENTIEL d'appeler set_password puis save() après la création
            coach.set_password(raw_password)
            coach.save()
            
            # Optionnel: Envoyer l'email au coach avec le raw_password
            # send_mail(..., raw_password)
            
            messages.success(request, f'Coach {full_name} ajouté. Mot de passe généré : {raw_password} (Veuillez lui communiquer en privé).')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'ajout du coach: {str(e)}')
            
        return redirect('backoffice:manage_coaches')
    
    # GET request: Assurez-vous de rediriger vers le bon endroit
    # ou de rendre un formulaire si vous avez une page d'ajout dédiée
    return redirect('backoffice:manage_coaches')


def coach_edit(request, pk):
    coach = get_object_or_404(Coach, pk=pk)
    
    # 🎯 FIX 1: Change coach.user to coach.customuser_ptr
    user_instance = coach.customuser_ptr 
    
    if request.method == 'POST':
        # 🎯 Apply FIX 1 here
        user_form = UserForm(request.POST, request.FILES, instance=user_instance)
        coach_form = CoachForm(request.POST, instance=coach)
        
        if user_form.is_valid() and coach_form.is_valid():
            user_form.save()
            
            coach_obj = coach_form.save(commit=False)
            # You can keep this line if you want to force visibility on edit
            # coach_obj.show_on_website = True 
            coach_obj.save()
            
            # 🎯 Apply FIX 1 here for the success message
            messages.success(request, f'Coach "{user_instance.nom_complet}" updated successfully!')
            return redirect('users:manage_coaches')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # 🎯 Apply FIX 1 here
        user_form = UserForm(instance=user_instance)
        coach_form = CoachForm(instance=coach)

    return render(request, 'backoffice/coaches/coach_edit_page.html', {
        'user_form': user_form,
        'coach_form': coach_form,
        'coach': coach,
        'title': 'Edit Coach',
    })
        
def coaches_coach_delete(request, pk):
    coach = get_object_or_404(Coach, pk=pk)
    
    # Use the correct attribute for the base user instance
    user_instance = coach.customuser_ptr 
    
    nom_complet = user_instance.nom_complet # Use nom_complet 
    user_instance.delete() # Deletes the CustomUser, which cascades to delete the Coach
    
    messages.success(request, f'Coach profile "{nom_complet}" has been deleted.')
    return redirect('users:manage_coaches')






def create_or_edit_business(request):

    # Vérifie que l'utilisateur est connecté ET a un rôle business owner
    if getattr(request.user, 'role', None) != 'business_owner':
        return redirect('main:index')

    # Vérifie si le business existe déjà
    try:
        business = request.user.businessowner
        form = BusinessOwnerForm(instance=business)
    except BusinessOwner.DoesNotExist:
        business = None
        form = BusinessOwnerForm()

    if request.method == "POST":
        form = BusinessOwnerForm(request.POST, request.FILES, instance=business)
        if form.is_valid():
            new_business = form.save(commit=False)
            new_business.user = request.user
            new_business.save()
            return redirect('product:product_list')

    return render(request, 'main/businessowner/businessowner.html', {'form': form})

#backoffice buisness owner 


def backoffice_manage_businessowners(request):
    owners = BusinessOwner.objects.all()
    return render(request, 'backoffice/manage_businessowners.html', {'owners': owners})




def backoffice_add_businessowner(request):
    if request.method == 'POST':
        form = BusinessOwnerForm(request.POST, request.FILES)
        if form.is_valid():
            business_email = form.cleaned_data['professional_email']

            # Vérifie si l'email existe déjà dans CustomUser
            if CustomUser.objects.filter(email=business_email).exists():
                messages.error(request, "Cet email est déjà utilisé par un utilisateur existant.")
            else:
                business = form.save(commit=False)
                # Ici, si nécessaire, tu peux lier à un utilisateur existant
                # business.user = request.user
                business.save()
                messages.success(request, "Business Owner créé avec succès !")
                return redirect('users:manage_businessowners')
    else:
        form = BusinessOwnerForm()
    
    return render(request, 'backoffice/form_businessowner.html', {
        'form': form,
        'title': 'Add Business Owner'
    })

def backoffice_edit_businessowner(request, owner_id):
    owner = get_object_or_404(BusinessOwner, id=owner_id)

    if request.method == 'POST':
        form = BusinessOwnerForm(request.POST, request.FILES, instance=owner)
        if form.is_valid():
            form.save()
            return redirect('users:manage_businessowners')
    else:
        form = BusinessOwnerForm(instance=owner)

    return render(request, 'backoffice/form_businessowner.html', {'form': form, 'title': 'Edit Business Owner'})


def backoffice_delete_businessowner(request, owner_id):
    owner = get_object_or_404(BusinessOwner, id=owner_id)
    owner.delete()
    return redirect('users:manage_businessowners')

def backoffice_manage_products(request):
    products = Product.objects.all().annotate(avg_rating=Avg("ratings__rating"))
    return render(request, 'backoffice/manage_products.html', {'products': products})


def backoffice_add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('users:backoffice_manage_products')
    else:
        form = ProductForm()

    return render(request, 'backoffice/form_product.html', {
        'form': form,
        'title': 'Add Product'
    })


def backoffice_edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('users:backoffice_manage_products')
    else:
        form = ProductForm(instance=product)

    return render(request, 'backoffice/form_product.html', {
        'form': form,
        'title': 'Edit Product'
    })


def backoffice_delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return redirect('users:backoffice_manage_products')


def backoffice_product_details(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    ratings = product.ratings.all()
    return render(request, 'backoffice/product_details.html', {
        'product': product,
        'ratings': ratings
    })


# Importez votre modèle utilisateur et d'autres dépendances, ex:
# from django.contrib.auth import get_user_model
# User = get_user_model() 
# Si vous utilisez un User par défaut, importez-le :
# from django.contrib.auth.models import User 





def users_pdf(request):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch
    )
    styles = getSampleStyleSheet()
    Story = []

    # --- 2. Titre et Date ---
    title_text = "Liste Détaillée des Utilisateurs"
    date_text = datetime.now().strftime("Généré le %d/%m/%Y à %H:%M")

    # Titre centré
    h1_style = styles['h1']
    h1_style.alignment = 1 # Center
    Story.append(Paragraph(f'<b><font size="16">{title_text}</font></b>', h1_style))
    Story.append(Spacer(1, 0.1 * inch))

    # Date à droite
    date_style = styles['Normal']
    date_style.alignment = 2 # Right
    Story.append(Paragraph(f'<font size="10">{date_text}</font>', date_style))
    Story.append(Spacer(1, 0.3 * inch))

    # --- 3. Construction des données du tableau ---
    
    # 3.1. En-têtes du tableau (6 colonnes)
    data = [["Photo", "Nom Complet", "Ville", "Tél.", "Email", "Rôle"]]
    
    # Récupération des utilisateurs
    users = User.objects.all()
    
    # 3.2. Remplissage des lignes
    image_size = 0.5 * inch # Taille de la photo de profil

    for user in users:
        # Initialisation de la cellule d'image
        img_cell = Paragraph("", styles['Normal']) 

        # Définition des 6 variables de la ligne. Adaptez les noms des champs si besoin.
        nom = user.nom_complet if hasattr(user, 'nom_complet') and user.nom_complet else "Non défini"
        ville = getattr(user, 'ville', "Non défini")
        tel = getattr(user, 'num_tel', "Non défini") # J'ai gardé 'numero_telephone' comme nom de champ
        email = user.email if user.email else "Non défini"
        role = getattr(user, "role", "Non défini")
        
        # ------------------------------------------------------------------
        # Logique de chargement de l'image (Champ 'pdp')
        # ------------------------------------------------------------------
        if hasattr(user, 'pdp') and user.pdp:
            try:
                image_path = user.pdp.path 
                
                if image_path and os.path.exists(image_path):
                    # Redimensionne et insère l'image dans la cellule
                    img_cell = RlImage(image_path, image_size, image_size, mask='preserve') 
                else:
                    img_cell = Paragraph("🚫", styles['Normal']) 
                    
            except Exception as e:
                # Gère les erreurs de chargement d'image (ex: chemin invalide)
                print(f"Erreur de chargement d'image pour l'utilisateur {user.email}: {e}")
                img_cell = Paragraph("🚫", styles['Normal']) 

        # Mise à jour de data.append() pour inclure les 6 éléments
        data.append([img_cell, nom, ville, tel, email, role])
        
    # --- 4. Création du tableau ---
    # Définition des 6 largeurs de colonnes (assurez-vous que la somme est < 7.5 pouces)
    colWidths = [
        0.7 * inch,  # Photo (Pdp)
        1.7 * inch,  # Nom Complet
        1.0 * inch,  # Ville
        1.2 * inch,  # Tél.
        2.2 * inch,  # Email
        0.7 * inch   # Rôle
    ] 

    table = Table(data, colWidths=colWidths)

    # 4.1. Définition du style du tableau
    table_style = TableStyle([
        # En-têtes (Ligne 0)
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e6c9a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')), 
        
        # Contenu des cellules
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'), # Alignement général du contenu à gauche
        ('ALIGN', (0, 1), (0, -1), 'CENTER'), # Sauf la colonne Photo (index 0)
        ('ALIGN', (3, 1), (3, -1), 'CENTER'), # Sauf la colonne Téléphone (index 3)
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Alternance de couleurs (Striping)
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f8ff')), # Lignes paires
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor('#f0f8ff')]), # Alternance
    ])

    table.setStyle(table_style)
    Story.append(table)
    Story.append(Spacer(1, 0.5 * inch))

    # --- 5. Total des utilisateurs ---
    total_text = f"Total des utilisateurs : {users.count()}" 
    Story.append(Paragraph(f'<b><font size="12">{total_text}</font></b>', styles['Normal']))

    # --- 6. Génération et retour ---
    doc.build(Story)

    # Retour de la réponse HTTP
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="liste_utilisateurs_v2.pdf"'
    response.write(buffer.getvalue())
    buffer.close()
    return response



User = get_user_model()

def users_stats(request):
    # Compter le nombre d'utilisateurs par rôle
    stats = User.objects.values('role').annotate(count=Count('id'))

    # Préparer les données pour le graphique
    labels = [item['role'] for item in stats]
    counts = [item['count'] for item in stats]

    return render(request, 'backoffice/users_stats.html', {
        'labels': labels,
        'counts': counts,
    })
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import messages
from .forms import ForgotPasswordForm

User = get_user_model()

def forgot(request):
    return render(request, 'forgot_password.html')

from django.core.mail import EmailMultiAlternatives

def forgot_password(request):
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, "Email introuvable.")
                return redirect('users:forgot')

            token = PasswordResetTokenGenerator().make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            reset_link = request.build_absolute_uri(
                f"/users/reset/{uid}/{token}/"
            )

            # ----- EMAIL HTML -----
            subject = "🔐 Réinitialisation de votre mot de passe"
            text_message = f"Réinitialisez votre mot de passe : {reset_link}"

            html_message = f"""
            <div style='font-family:Arial;padding:20px;background:#f7f7f7'>
                <div style='background:white;padding:25px;border-radius:10px;
                            max-width:500px;margin:auto;
                            box-shadow:0 4px 15px rgba(0,0,0,0.1);'>

                    <h2 style='color:#4c84ff;text-align:center;'>
                        Réinitialisation du mot de passe
                    </h2>

                    <p style='font-size:15px;color:#333;'>
                        Bonjour <b>{user.nom_complet}</b>,<br><br>
                        Vous avez demandé à réinitialiser votre mot de passe.
                        Cliquez sur le bouton ci-dessous :
                    </p>

                    <div style='text-align:center;margin:25px 0;'>
                        <a href='{reset_link}'
                           style='background:#4c84ff;color:white;padding:12px 20px;
                                  text-decoration:none;font-weight:bold;border-radius:8px;
                                  display:inline-block;'>
                           🔑 Réinitialiser mon mot de passe
                        </a>
                    </div>

                    <p style='font-size:14px;color:#888;'>
                        Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.
                    </p>

                </div>
            </div>
            """

            email_obj = EmailMultiAlternatives(subject, text_message, None, [email])
            email_obj.attach_alternative(html_message, "text/html")
            email_obj.send()

            messages.success(request, "📩 Email envoyé ! Vérifiez votre boîte.")
            return redirect('users:forgot')
    else:
        form = ForgotPasswordForm()

    return render(request, "forgot_password.html", {"form": form})


from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode

def reset_password(request, uidb64, token):
    User = get_user_model()

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user is not None and PasswordResetTokenGenerator().check_token(user, token):
        if request.method == "POST":
            new_password = request.POST.get("password")
            confirm = request.POST.get("confirm")
            
            if new_password != confirm:
                messages.error(request, "Les mots de passe ne correspondent pas.")
                return redirect(request.path)

            user.set_password(new_password)
            user.save()
            messages.success(request, "Mot de passe réinitialisé avec succès.")
            return redirect('users:auth')

        return render(request, "reset_password.html")

    else:
        return render(request, "invalid_link.html")
