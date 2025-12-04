# users/views.py
# ----------------- Django imports -----------------
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.utils import timezone
from django.conf import settings
from django.http import FileResponse, JsonResponse, HttpResponse, HttpResponseBadRequest
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

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
import io
import json
import requests
from PIL import Image

# ----------------- ReportLab imports -----------------
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import cm, inch
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RlImage, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.colors import HexColor

#----
import random
import string
import logging

logger = logging.getLogger(__name__)

# Create your views here.
# Pages principale
# ----------------------

# ----------------------
# backoffice
# ----------------------


def backoffice_tables(request):
    # Pass all nutritionists to the backoffice tables view
    nutritionists = Nutritionist.objects.all()
    return render(request, 'backoffice/tables_nutritionists.html', {'nutritionists': nutritionists})



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


def backoffice_nutritionist_delete(request, pk):
    """
    Supprime un nutritionniste uniquement via POST.
    Redirige vers la table backoffice après suppression.
    """
    if request.method == 'POST':
        nutritionist = get_object_or_404(Nutritionist, pk=pk)
        nutritionist.delete()
        messages.success(request, f'Le nutritionniste {nutritionist.nom_complet} a été supprimé.')
        return redirect('users:backoffice_nutritionist_list')


def backoffice_nutritionist_update(request, pk):
    """Edit a nutritionist from the backoffice and stay in the backoffice after saving."""
    nutritionist = get_object_or_404(Nutritionist, pk=pk)
    if request.method == 'POST':
        form = NutritionistForm(request.POST, request.FILES, instance=nutritionist)
        if form.is_valid():
            form.save()
            messages.success(request, 'nutritionniste modifié avec succès')
            return redirect('users:backoffice_nutritionist_list')
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

    # 3. FILTRAGE PAR LOCALISATION
    location = request.GET.get('location')
    if location:
        coaches = coaches.filter(location__iexact=location)

    # 4. LOGIQUE DE TRI (ORDRE)
    sort_by = request.GET.get('sort', 'id') 
    valid_sort_fields = ['session_price', 'subscription_price', 'experience_years', 'id']
    if sort_by not in valid_sort_fields:
        sort_by = 'id'  # Default sorting

    coaches = coaches.order_by(sort_by)

    # 5. Liste des localisations uniques
    locations = Coach.objects.values_list('location', flat=True).distinct()

    # 6. Rendu de la page
    # Calculate average rating and latest feedbacks for each coach
    from appointments.models import Feedback
    from django.db.models import Avg
    coach_feedback_data = {}
    for coach in coaches:
        feedbacks = Feedback.objects.filter(coach=coach).order_by('-created_at')
        avg_rating = feedbacks.aggregate(avg=Avg('rating'))['avg']
        latest_feedbacks = feedbacks[:3]
        coach_feedback_data[coach.pk] = {
            'avg_rating': avg_rating,
            'latest_feedbacks': latest_feedbacks,
            'feedback_count': feedbacks.count()
        }
    context = {
        'coaches': coaches,
        'current_sport': sport_type,
        'current_sort': sort_by,
        'location': location,
        'locations': locations,
        'all_sport_types': Coach.SPORT_TYPES,
        'coach_feedback_data': coach_feedback_data,
    }
    return render(request, 'main/trainer.html', context)

# users/views.py - Fonction coach_create (Corrigée et simplifiée)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# Assurez-vous d'importer Coach (votre modèle) et CoachForm (votre formulaire)
from .models import Coach
from .forms import CoachForm

# views.py

@login_required
def coach_create(request):
        # --- FRONT-END SELF-SERVICE COACH CREATION ---
        # This view is for logged-in users to create their own coach profile.
        # It should NEVER create, delete, or overwrite user accounts.
        # It only extends the current user with coach-specific data.
    user = request.user

    # 1. LOGIQUE DE REDIRECTION (Vérifie si le profil Coach complet existe)
    if user.role == 'coach':
        if Coach.objects.filter(pk=user.pk).exists():
            messages.info(request, "Vous êtes déjà un Coach. Vous pouvez modifier votre profil.")
            return redirect('users:coach_update', pk=user.pk)

    # --- 2. LOGIQUE DE TRAITEMENT POST ---
    if request.method == 'POST':
        form = CoachForm(request.POST, request.FILES)
        try:
            if form.is_valid():
                coach_obj = form.save(commit=False)
                # Do NOT overwrite user info fields
                coach_obj.pk = user.pk  # Ensure coach uses the same PK as user
                coach_obj.nom_complet = user.nom_complet
                coach_obj.num_tel = user.num_tel
                coach_obj.ville = user.ville
                coach_obj.email = user.email
                coach_obj.save()
                # Explicitly set user role to 'coach' and save
                user.role = 'coach'
                user.save()
                logger.info(f"Coach profile created for user {user.email} (ID: {user.pk})")
                messages.success(request, 'Félicitations, votre profil Coach est créé !')
                return redirect('users:coach_list')
            else:
                logger.warning(f"Coach form invalid for user {user.email}: {form.errors}")
                messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
        except Exception as e:
            logger.error(f"Exception during coach creation for user {user.email}: {e}")
            messages.error(request, "Une erreur est survenue lors de la création du profil Coach. Contactez l'administrateur.")
    else:
        form = CoachForm()

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
            coach = form.save(commit=False)

            # Ensure latitude, longitude, and show_map are saved
            coach.latitude = form.cleaned_data.get('latitude')
            coach.longitude = form.cleaned_data.get('longitude')
            coach.show_map = form.cleaned_data.get('show_map', coach.show_map)

            coach.save()
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
    from appointments.models import Feedback
    from appointments.forms import FeedbackForm
    from django.db.models import Avg
    feedbacks = Feedback.objects.filter(coach=coach).order_by('-created_at')
    avg_rating = feedbacks.aggregate(avg=Avg('rating'))['avg']
    latest_feedbacks = feedbacks[:3]
    all_feedbacks = feedbacks
    more_feedbacks = feedbacks.count() > 3
    can_leave_feedback = False
    feedback_form = None
    user = request.user
    # Allow any authenticated client to leave unlimited feedback
    if user.is_authenticated and user.role == 'client':
        can_leave_feedback = True
        feedback_form = FeedbackForm()
        if request.method == 'POST' and 'leave_feedback' in request.POST:
            feedback_form = FeedbackForm(request.POST)
            if feedback_form.is_valid():
                feedback_obj = feedback_form.save(commit=False)
                feedback_obj.client = user
                feedback_obj.coach = coach
                feedback_obj.save()
                return redirect('users:coach_detail', pk=coach.pk)
    context = {
        'coach': coach,
        'avg_rating': avg_rating,
        'latest_feedbacks': latest_feedbacks,
        'all_feedbacks': all_feedbacks,
        'more_feedbacks': more_feedbacks,
        'can_leave_feedback': can_leave_feedback,
        'feedback_form': feedback_form,
    }
    return render(request, 'main/coach_detail.html', context)

# ----------------------
# Backoffice CRUD Coaches
# ----------------------




def manage_coaches(request):
    """
    Manage coaches in the backoffice with filtering and sorting functionality.
    """
    # Base queryset
    coaches = Coach.objects.all()

    # Filtering by sport type
    sport_type = request.GET.get('sport_type')
    if sport_type:
        coaches = coaches.filter(sport_type__iexact=sport_type)

    # Filtering by location
    location = request.GET.get('location')
    if location:
        coaches = coaches.filter(location__iexact=location)

    # Filtering by status
    status = request.GET.get('status')
    if status == 'available':
        coaches = coaches.filter(is_available=True)
    elif status == 'not_available':
        coaches = coaches.filter(is_available=False)

    # Searching by name or email
    search_query = request.GET.get('search')
    if search_query:
        coaches = coaches.filter(
            Q(nom_complet__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # Sorting
    sort_by = request.GET.get('sort', 'id')
    order = request.GET.get('order', 'asc')
    valid_sort_fields = ['session_price', 'subscription_price', 'experience_years', 'id']
    if sort_by not in valid_sort_fields:
        sort_by = 'id'  # Default sorting

    if order == 'desc':
        sort_by = f'-{sort_by}'

    # Log the sorting parameters
    logger.debug(f"Sorting by: {sort_by}")

    try:
        coaches = coaches.order_by(sort_by)
    except Exception as e:
        logger.error(f"Error while sorting: {e}")
        coaches = Coach.objects.all()  # Fallback to default queryset

    # Log the resulting queryset
    logger.debug(f"Resulting Queryset: {coaches.query}")

    # Get unique locations for the location filter
    locations = Coach.objects.values_list('location', flat=True).distinct()

    # Get sport types for the sport type filter
    sport_types = Coach.SPORT_TYPES

    # Context data
    context = {
        'coaches': coaches,
        'sport_type_filter': sport_type,
        'location_filter': location,
        'status_filter': status,
        'search_query': search_query,
        'current_sort': sort_by,
        'current_order': order,
        'sport_types': sport_types,
        'locations': locations,
    }

    return render(request, 'backoffice/coaches/manage_coaches.html', context)


def add_coach(request):
        # --- BACKOFFICE ADMIN COACH CREATION ---
        # This view is for admins to create a new user and coach profile at once.
        # It generates a password, creates a new user, then links a coach profile.
        # It should NEVER be used for self-service coach creation by logged-in users.
    if request.method == 'POST':
        try:
            # --- Data Retrieval ---
            full_name = request.POST.get('full_name')
            email = request.POST.get('email')
            phone_number = request.POST.get('phone_number', '')
            city = request.POST.get('city', '')
            # Use request.FILES.get() for file uploads (profile_photo)
            profile_photo = request.FILES.get('profile_photo') 
            
            sport_type = request.POST.get('sport_type')
            experience_years = request.POST.get('experience_years')
            location = request.POST.get('location')
            session_price = request.POST.get('session_price')
            subscription_price = request.POST.get('subscription_price')
            bio = request.POST.get('bio', '')
            certifications = request.POST.get('certifications', '')
            # Checkbox values are 'on' or None
            is_available = request.POST.get('is_available') == 'on'
            show_on_website = request.POST.get('show_on_website') == 'on'
            
            # --- Validation ---
            if not all([full_name, email, sport_type, experience_years, location, session_price, subscription_price]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('backoffice:manage_coaches')
            
            if User.objects.filter(email=email).exists():
                messages.error(request, 'A user with this email already exists.')
                return redirect('backoffice:manage_coaches')
            
            # --- Processing and Creation ---
            
            # Generate a random password (Requires import random and string)
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            
            # Create user
            user = User.objects.create_user(
                email=email,
                password=password,
                full_name=full_name,
                phone_number=phone_number,
                city=city,
                role='coach'
            )
            
            if profile_photo:
                user.profile_photo = profile_photo
            
            user.save()
            
            # Create coach profile
            coach = Coach.objects.create(
                user=user,
                sport_type=sport_type,
                # Convert string inputs to correct types
                experience_years=int(experience_years), 
                session_price=float(session_price),
                subscription_price=float(subscription_price),
                location=location,
                bio=bio,
                certifications=certifications,
                is_available=is_available,
                show_on_website=show_on_website
            )
            
            messages.success(request, f'Coach {full_name} was added successfully! A random password has been generated for their account.')
            
        except Exception as e:
            # Catch exceptions like invalid type conversion (float/int)
            messages.error(request, f'Error adding coach: {str(e)}')
        
        return redirect('backoffice:manage_coaches')
    
    # If not POST (or a GET request to this URL), redirect back to coaches page
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




from .forms import BusinessOwnerForm
from .models import BusinessOwner
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


@login_required
def businessowner_page(request):

    # Si l'utilisateur n'est PAS Business Owner → afficher la page publique
    if request.user.role != 'business_owner':
        owners = BusinessOwner.objects.all()
        return render(request, 'main/businessowner/businessowner_public.html', {'owners': owners})

    # Si l'utilisateur est Business Owner → récupérer ou créer son profil
    business, created = BusinessOwner.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = BusinessOwnerForm(request.POST, request.FILES, instance=business)
        if form.is_valid():
            form.save()
            messages.success(request, "Vos informations ont été enregistrées avec succès.")
            return redirect('users:businessowner_page')
  # éviter le resubmit en actualisant
    else:
        form = BusinessOwnerForm(instance=business)

    return render(request, 'main/businessowner/businessowner.html', {'form': form})

#backoffice buisness owner 

def backoffice_manage_businessowners(request):
    owners = BusinessOwner.objects.all()
    return render(request, 'backoffice/manage_businessowners.html', {'owners': owners})

def backoffice_add_businessowner(request):
    if request.method == 'POST':
        form = BusinessOwnerForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.cleaned_data['professional_email']

            # Vérifie si un user existe déjà avec cet email
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, "Cet email est déjà utilisé.")
            else:
                # 1️⃣ Créer un utilisateur
                user = CustomUser.objects.create(
                    email=email,
                    username=email,
                    role='business_owner',
                )

                # 2️⃣ Créer le BusinessOwner lié à ce user
                business = form.save(commit=False)
                business.user = user
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

#------------metiers nutritionniste------------------
# --- Fonctions Front Office (nutritionist_list) ---
def nutritionist_list(request):
    """
    Affiche la liste des nutritionnistes avec gestion de la recherche (q) et du tri (sort, order).
    """
    search_query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', 'name') 
    order = request.GET.get('order', 'asc')

    # 1. Filtrage (Recherche)
    if search_query:
        nutritionists_qs = Nutritionist.objects.filter(
            Q(nom_complet__icontains=search_query) |
            Q(ville__icontains=search_query) |
            Q(speciality__icontains=search_query)
        )
    else:
        nutritionists_qs = Nutritionist.objects.all()

    # 2. Application du Tri
    sort_field_map = {
        'id': 'pk',
        'name': 'nom_complet',
        'city': 'ville',
        'speciality': 'speciality',
        'experience': 'experience_years',
        'fee': 'consultation_fee'
    }
    
    sort_field = sort_field_map.get(sort_by, 'full_name')

    if order == 'desc':
        sort_field = '-' + sort_field

    nutritionists = nutritionists_qs.order_by(sort_field)
    
    # 3. Préparer les options de tri pour le template
    sort_options_list = [
        ('name', 'Nom'),
        ('city', 'Ville'),
        ('speciality', 'Spécialité'),
        ('experience', 'Expérience'),
        ('fee', 'Tarif')
    ]

    return render(request, 'main/nutritionist_list.html', {
        'nutritionists': nutritionists,
        'search_query': search_query,
        'sort_by': sort_by,
        'order': order,
        'sort_options_list': sort_options_list,
    })

# --------------------------------------------------------------------------------------------------

class NutritionistCard(Flowable):
    """
    Crée une carte de nutritionniste personnalisée avec une photo de profil cerclée.
    """
    def __init__(self, nutritionist, width=None, height=2 * inch):
        Flowable.__init__(self)
        self.nutritionist = nutritionist
        self.width = width if width is not None else 7.5 * inch
        self.height = height
        self.styles = getSampleStyleSheet()

    def draw(self):
        c = self.canv # Référence au canvas de ReportLab
        
        # PARAMÈTRES POUR LE CERCLE ET L'IMAGE
        image_diameter = 1.6 * inch # Diamètre de l'image circulaire
        image_radius = image_diameter / 2
        
        # Positionnement de l'image (centre du cercle)
        x_circle_center = 1 * inch
        y_circle_center = self.height / 2 
        
        # Chemin de la photo
        photo_path = None
        if self.nutritionist.pdp:
            try:
                # Assurez-vous que l'objet file a bien un nom avant d'essayer de le joindre
                if self.nutritionist.pdp.name:
                    photo_path = os.path.join(settings.MEDIA_ROOT, self.nutritionist.pdp.name)
            except ValueError:
                photo_path = None
        
        # Dessiner la photo de profil cerclée
        c.saveState() # Sauvegarder l'état actuel du canevas
        
        # Étape 1: Créer un chemin de découpe circulaire (CORRECTION DÉFINITIVE)
        c.translate(x_circle_center, y_circle_center) # Déplacer l'origine au centre du cercle
        
        # Créer le chemin explicitement pour satisfaire l'API ReportLab
        circle_path = c.beginPath() 
        circle_path.circle(0, 0, image_radius) # Dessiner la forme du cercle sur l'objet Path
        
        c.clipPath(circle_path) # <-- Passer explicitement le chemin (circle_path) comme argument 'aPath'
        
        # Étape 2: Dessiner l'image
        image_exists = photo_path and os.path.exists(photo_path)
        
        if image_exists:
            try:
                c.drawImage(
                    photo_path,
                    -image_radius, # Position X (depuis le centre)
                    -image_radius, # Position Y (depuis le centre)
                    width=image_diameter,
                    height=image_diameter,
                    mask='auto'
                )
            except Exception as e:
                # Si l'image existe mais ReportLab n'arrive pas à la charger (ex: format non supporté)
                c.setFillColor(colors.lightgrey)
                c.circle(0, 0, image_radius, fill=1, stroke=0)
        else:
            # Placeholder pour l'image manquante (cercle gris)
            c.setFillColor(colors.lightgrey)
            c.circle(0, 0, image_radius, fill=1, stroke=0)

        c.restoreState() # Restaurer l'état du canevas (retirer la translation et le chemin de découpe)
        
        # Étape 3: Dessiner une bordure autour du cercle (optionnel)
        c.setStrokeColor(HexColor('#BBBBBB'))
        c.setLineWidth(1)
        c.circle(x_circle_center, y_circle_center, image_radius + 1, fill=0, stroke=1)


        # 2. Dessiner les informations du texte
        text_x = x_circle_center + image_radius + 0.5 * inch
        
        # Nom (Titre)
        style_name = ParagraphStyle(
            name='NameStyle',
            fontName='Helvetica-Bold',
            fontSize=16,
            textColor=HexColor('#2C3E50'),
            leading=18
        )
        name_text = Paragraph(self.nutritionist.nom_complet, style_name)
        
        # Spécialité et Ville (Sous-titres)
        style_details = ParagraphStyle(
            name='DetailsStyle',
            fontName='Helvetica',
            fontSize=10,
            textColor=HexColor('#7F8C8D'),
            leading=12
        )
        
        details_text_html = (
            f'Spécialité: <b>{self.nutritionist.speciality}</b> | '
            f'Ville: <b>{self.nutritionist.ville}</b> | '
            f'Expérience: <b>{self.nutritionist.experience_years} ans</b>'
        )
        details_paragraph = Paragraph(details_text_html, style_details)


        # Positionnement vertical du texte
        name_text.wrapOn(c, self.width - text_x - 0.2*inch, 0.5*inch)
        details_paragraph.wrapOn(c, self.width - text_x - 0.2*inch, 0.5*inch)
        
        total_text_height = name_text.height + details_paragraph.height + 0.1 * inch
        
        name_text_y = y_circle_center + (total_text_height / 2) - name_text.height 
        details_paragraph_y = name_text_y - 0.1 * inch - details_paragraph.height

        name_text.drawOn(c, text_x, name_text_y)
        details_paragraph.drawOn(c, text_x, details_paragraph_y)
        
        # 3. Dessiner la bordure de séparation
        c.setStrokeColor(HexColor('#F2F4F8'))
        c.setLineWidth(1)
        c.line(0, 0, self.width, 0)
        
# --------------------------------------------------------------------------------------------------

# Fonction à utiliser pour la vue Django
def nutritionist_list_pdf(request):
    # Cette section est nécessaire pour la création du PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                            leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                            topMargin=1.5 * cm, bottomMargin=1.5 * cm)

    styles = getSampleStyleSheet()
    Story = []

    # 1. Titre du document
    title_style = ParagraphStyle(
        name='TitleStyle',
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=HexColor('#2980B9'), # Bleu moderne
        alignment=1, # Centré
        spaceAfter=0.5 * cm
    )
    Story.append(Paragraph("Liste des Experts en Nutrition", title_style))
    Story.append(Spacer(1, 0.2 * cm))

    # Dessiner une ligne de séparation sous le titre
    class Line(Flowable):
        def __init__(self, width=doc.width, height=0):
            Flowable.__init__(self)
            self.width = width
            self.height = height

        def draw(self):
            c = self.canv
            c.setStrokeColor(HexColor('#BDC3C7')) # Gris clair
            c.setLineWidth(1)
            c.line(0, self.height, self.width, self.height)

    Story.append(Line(width=doc.width))
    Story.append(Spacer(1, 1 * cm))
    
    # 2. Liste des nutritionnistes
    nutritionists = Nutritionist.objects.all()

    for nutritionist in nutritionists:
        card = NutritionistCard(nutritionist)
        Story.append(card)
        Story.append(Spacer(1, 0.2 * cm)) # Ajout d'un petit espacement ici pour séparer les cartes
        
    doc.build(Story)
    
    # Récupérer la valeur du buffer et le renvoyer en tant que réponse HTTP
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='nutritionists_list.pdf')

def backoffice_nutritionist_list(request): 
    """
    Affiche la liste des nutritionnistes avec gestion de la recherche/tri
    ET inclut les statistiques par ville.
    """
    search_query = request.GET.get('q', '')
    # Utiliser 'nom_complet' par défaut pour le tri, car 'name' n'est pas un champ de modèle
    sort_by = request.GET.get('sort', 'nom_complet')
    order = request.GET.get('order', 'asc')

    # 1. Traitement de la Liste des Nutritionnistes (existant)
    nutritionists_qs = Nutritionist.objects.all()

    if search_query:
        # Applique le filtre de recherche UNIQUEMENT s'il y a une requête
        nutritionists_qs = nutritionists_qs.filter(
            Q(nom_complet__icontains=search_query) |
            Q(ville__icontains=search_query) |
            Q(num_tel__icontains=search_query) |
            Q(speciality__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # Application du Tri
    sort_field_map = {
        'id': 'id',
        'nom_complet': 'nom_complet', # Champ par défaut
        'email': 'email',
        'num_tel': 'num_tel',
        'ville': 'ville',
        'speciality': 'speciality',
        'experience_years': 'experience_years', # Le nom exact du champ du modèle
        'consultation_fee': 'consultation_fee' # Le nom exact du champ du modèle
    }
    
    # Assurez-vous que sort_by correspond à une clé dans sort_field_map
    sort_key = sort_by if sort_by in sort_field_map else 'nom_complet'
    sort_field = sort_field_map.get(sort_key)
    
    if order == 'desc':
        sort_field = '-' + sort_field
        
    # Le QuerySet final avec le filtre et le tri appliqués
    nutritionists = nutritionists_qs.order_by(sort_field)
    
    # Calcul du total
    total_nutritionists = Nutritionist.objects.count()

    # Statistiques par ville
    stats = Nutritionist.objects.values('ville').annotate(count=Count('ville')).order_by('-count')
    total_nutritionists_for_stats = Nutritionist.objects.count()
    stats_processed = []

    if total_nutritionists_for_stats > 0:
        for stat in stats:
            ville = stat['ville'] if stat['ville'] else '(Non spécifiée)'
            percentage = (stat['count'] / total_nutritionists_for_stats) * 100
            stat['ville'] = ville
            stat['percentage'] = round(percentage, 1)
            stats_processed.append(stat)

    context = {
        'nutritionists': nutritionists,
        'search_query': search_query,
        'sort_by': sort_key,
        'order': order,
        'total_nutritionists': total_nutritionists,
        'city_stats_data': json.dumps(stats_processed),
    }

    return render(request, 'backoffice/tables_nutritionists.html', context)

# Recherche AJAX pour les nutritionnistes
def ajax_search_nutritionists(request):
    query = request.GET.get("q", "")
    results = []

    if query:
        qs = Nutritionist.objects.filter(
            Q(nom_complet__icontains=query) |
            Q(ville__icontains=query) |
            Q(speciality__icontains=query)
        )

        for n in qs:
            results.append({
                "name": n.nom_complet,
                "city": n.ville,
                "speciality": n.speciality,
                "photo": n.pdp.url if n.pdp else "",
            })

    return JsonResponse({"results": results})

def geocode_address(request):
    """
    Geocode an address using Nominatim API to avoid CORS issues in frontend.
    Enhanced to handle detailed Tunisian addresses better.
    """
    address = request.GET.get('address', '')
    if not address:
        return JsonResponse({'error': 'Address parameter is required'}, status=400)

    try:
        # First try the full address
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={requests.utils.quote(address)}&limit=1&countrycodes=TN"
        headers = {
            'User-Agent': 'EatAndFit/1.0 (contact@eatandfit.com)'  # Required by Nominatim
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        # If no results, try with more specific Tunisian context
        if not data and 'Tunisia' in address:
            # Try removing specific details and keeping main area/location
            simplified_address = address.replace(', Tunisia', '').strip()
            # For Tunisian addresses, try adding "Tunis" if it's a known area
            tunis_areas = ['ariana', 'el ghazela', 'el manar', 'lac', 'rades', 'carthage', 'sidi bou said']
            area_found = None
            for area in tunis_areas:
                if area.lower() in simplified_address.lower():
                    area_found = area
                    break

            if area_found:
                fallback_address = f"{area_found}, Tunis, Tunisia"
                url = f"https://nominatim.openstreetmap.org/search?format=json&q={requests.utils.quote(fallback_address)}&limit=1&countrycodes=TN"
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()

        return JsonResponse(data, safe=False)

    except requests.RequestException as e:
        return JsonResponse({'error': f'Geocoding service error: {str(e)}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'Unexpected error: {str(e)}'}, status=500)

def nutritionist_city_stats(request):
    """
    Calcule le nombre de nutritionnistes par ville, incluant ceux sans ville spécifiée.
    Retourne un QuerySet: [{'city': 'Tunis', 'count': 15}, {'city': 'Sfax', 'count': 8}, ...]
    """

    # 1. Requête d'agrégation (incluant les villes vides ou None)
    stats = Nutritionist.objects.values('ville').annotate(count=Count('ville')).order_by('-count')

    # 2. Calcul du total et des pourcentages
    total_nutritionists = Nutritionist.objects.count()
    stats_processed = []

    if total_nutritionists > 0:
        for stat in stats:
            ville = stat['ville'] if stat['ville'] else '(Non spécifiée)'
            percentage = (stat['count'] / total_nutritionists) * 100
            stat['ville'] = ville
            stat['percentage'] = round(percentage, 1)
            stats_processed.append(stat)

    # 3. Préparation du contexte pour le template (Back-office)
    context = {
        'city_stats': stats_processed,
        'total_nutritionists': total_nutritionists
    }

    # 4. Rendu du template
    return render(request, 'backoffice/nutritionist_stats.html', context)

# --- AI Nutritional Analysis Feature ---

def analyze_food_image(request):
    """
    Vue pour analyser une image de nourriture et estimer ses valeurs nutritionnelles
    """
    if request.method == 'POST' and request.FILES.get('food_image'):
        food_image = request.FILES['food_image']

        # Sauvegarder temporairement l'image
        temp_path = default_storage.save(f'temp/{food_image.name}', ContentFile(food_image.read()))
        temp_file_path = os.path.join(settings.MEDIA_ROOT, temp_path)

        try:
            # Utiliser OpenAI pour analyser l'image directement
            nutritional_info = estimate_nutrition_with_openai(temp_file_path)

            # Nettoyer le fichier temporaire
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

            # Si c'est une requête AJAX, retourner JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'nutritional_info': nutritional_info
                })

            # Sinon, afficher la page de résultats normale
            context = {
                'nutritional_info': nutritional_info,
                'image_url': None  # L'image a été supprimée
            }
            return render(request, 'food_analysis_result.html', context)

        except Exception as e:
            # Nettoyer en cas d'erreur
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

            # Si c'est une requête AJAX, retourner JSON avec erreur
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })

            messages.error(request, f'Erreur lors de l\'analyse: {str(e)}')
            return redirect('nutritionist_list')

    return render(request, 'main/food_analysis_upload.html')

def analyze_image_with_vision(image_path):
    """
    Utilise Google Vision API pour analyser l'image
    """
    try:
        from google.cloud import vision

        # Initialiser le client Vision
        client = vision.ImageAnnotatorClient()

        # Charger l'image
        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)

        # Effectuer la détection d'objets
        objects = client.object_localization(image=image).localized_object_annotations

        # Effectuer la reconnaissance de texte
        text_response = client.text_detection(image=image)
        texts = text_response.text_annotations

        # Effectuer la détection d'étiquettes
        label_response = client.label_detection(image=image)
        labels = label_response.label_annotations

        return {
            'objects': [{'name': obj.name, 'confidence': obj.score} for obj in objects],
            'texts': [text.description for text in texts],
            'labels': [{'description': label.description, 'confidence': label.score} for label in labels]
        }

    except Exception as e:
        raise Exception(f"Erreur Google Vision API: {str(e)}. Assurez-vous que les credentials Google Cloud sont configurés.")

def estimate_nutrition_with_openai(image_path):
    """
    Utilise OpenAI Vision API pour analyser l'image et estimer les valeurs nutritionnelles
    """
    try:
        import openai
        import base64

        # Convertir l'image en JPEG si nécessaire et encoder en base64
        try:
            with Image.open(image_path) as img:
                # Vérifier le format de l'image
                if img.format not in ['JPEG', 'JPG', 'PNG', 'BMP', 'TIFF', 'WEBP']:
                    raise Exception(f"Format d'image non supporté: {img.format}. Utilisez JPEG, PNG, BMP, TIFF ou WebP.")

                # Convertir en RGB si nécessaire (pour les images avec transparence)
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")
                # Sauvegarder en JPEG dans un buffer
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG")
                buffer.seek(0)
                base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        except (Image.UnidentifiedImageError, OSError) as img_error:
            # PIL raises UnidentifiedImageError for unknown formats, OSError for corrupted files
            if "cannot identify image file" in str(img_error).lower() or "AVIF" in str(img_error).lower() or image_path.lower().endswith('.avif'):
                raise Exception("Format d'image non supporté. Veuillez utiliser une image au format JPEG, PNG, BMP, TIFF ou WebP.")
            else:
                raise Exception(f"Erreur lors du traitement de l'image: {str(img_error)}")
        except Exception as img_error:
            if "cannot identify image file" in str(img_error).lower() or "AVIF" in str(img_error).lower() or image_path.lower().endswith('.avif'):
                raise Exception("Format d'image non supporté. Veuillez utiliser une image au format JPEG, PNG, BMP, TIFF ou WebP.")
            else:
                raise Exception(f"Erreur lors du traitement de l'image: {str(img_error)}")

        # Créer le prompt pour OpenAI Vision
        prompt = """
        Analyse cette image de nourriture et estime les valeurs nutritionnelles approximatives pour 100g de ce repas/plat.

        Identifie les aliments présents dans l'image et fournis une estimation nutritionnelle précise.

        Fournis une réponse structurée en JSON avec les champs suivants:
        - calories: nombre de calories pour 100g
        - proteines: grammes de protéines pour 100g
        - lipides: grammes de lipides pour 100g
        - glucides: grammes de glucides pour 100g
        - fibres: grammes de fibres pour 100g (si applicable)
        - score_sante: score de santé sur 10 (1=très malsain, 10=très sain)
        - recommandations: liste de recommandations nutritionnelles courtes

        Réponds uniquement avec du JSON valide.
        """

        # Vérifier que la clé API OpenAI est configurée
        if not settings.OPENAI_API_KEY:
            raise Exception("La clé API OpenAI n'est pas configurée. Assurez-vous que la variable d'environnement OPENAI_API_KEY est définie.")

        # Utiliser OpenAI Vision API
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0.3
        )

        # Parser la réponse JSON
        result_text = response.choices[0].message.content.strip()

        # Supprimer les blocs de code markdown si présents
        if result_text.startswith('```json'):
            result_text = result_text[7:]  # Supprimer ```json
        if result_text.startswith('```'):
            result_text = result_text[3:]  # Supprimer ```
        if result_text.endswith('```'):
            result_text = result_text[:-3]  # Supprimer ``` à la fin

        result_text = result_text.strip()  # Nettoyer les espaces

        try:
            nutritional_data = json.loads(result_text)
        except json.JSONDecodeError as e:
            raise Exception(f"Erreur de parsing JSON de la réponse OpenAI: {str(e)}. Réponse reçue: {result_text[:500]}...")

        return nutritional_data

    except Exception as e:
        raise Exception(f"Erreur OpenAI Vision API: {str(e)}. Assurez-vous que la clé API OpenAI est configurée dans les variables d'environnement.")

def generate_nutrition_pdf(request):
    """
    Génère un PDF avec les résultats de l'analyse nutritionnelle
    """
    if request.method == 'POST':
        try:
            # Récupérer les données nutritionnelles depuis le POST
            nutritional_data = json.loads(request.POST.get('nutritional_data', '{}'))

            # Créer le buffer pour le PDF
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4,
                                    leftMargin=2 * cm, rightMargin=2 * cm,
                                    topMargin=2 * cm, bottomMargin=2 * cm)

            styles = getSampleStyleSheet()
            Story = []

            # Titre du document
            title_style = ParagraphStyle(
                name='TitleStyle',
                fontName='Helvetica-Bold',
                fontSize=24,
                textColor=HexColor('#FF6B35'),
                alignment=1,
                spaceAfter=0.5 * cm
            )
            Story.append(Paragraph("Rapport d'Analyse Nutritionnelle", title_style))
            Story.append(Spacer(1, 0.3 * cm))

            # Ligne de séparation
            class Line(Flowable):
                def __init__(self, width=doc.width, height=0):
                    Flowable.__init__(self)
                    self.width = width
                    self.height = height

                def draw(self):
                    c = self.canv
                    c.setStrokeColor(HexColor('#FF6B35'))
                    c.setLineWidth(2)
                    c.line(0, self.height, self.width, self.height)

            Story.append(Line(width=doc.width))
            Story.append(Spacer(1, 1 * cm))

            # Score de santé
            score = nutritional_data.get('score_sante', 0)
            health_score_style = ParagraphStyle(
                name='HealthScoreStyle',
                fontName='Helvetica-Bold',
                fontSize=18,
                textColor=HexColor('#4CAF50') if score >= 7 else HexColor('#FF9800') if score >= 5 else HexColor('#F44336'),
                alignment=1,
                spaceAfter=0.5 * cm
            )
            Story.append(Paragraph(f"Score de Santé: {score}/10", health_score_style))
            Story.append(Spacer(1, 0.5 * cm))

            # Section valeurs nutritionnelles
            section_style = ParagraphStyle(
                name='SectionStyle',
                fontName='Helvetica-Bold',
                fontSize=16,
                textColor=HexColor('#2C3E50'),
                spaceAfter=0.3 * cm
            )
            Story.append(Paragraph("Valeurs Nutritionnelles (pour 100g)", section_style))
            Story.append(Spacer(1, 0.2 * cm))

            # Tableau des nutriments
            from reportlab.platypus import Table, TableStyle

            nutrients_data = [
                ['Nutriment', 'Quantité'],
                ['Calories', f"{nutritional_data.get('calories', 0)} kcal"],
                ['Protéines', f"{nutritional_data.get('proteines', 0)} g"],
                ['Lipides', f"{nutritional_data.get('lipides', 0)} g"],
                ['Glucides', f"{nutritional_data.get('glucides', 0)} g"],
            ]

            if nutritional_data.get('fibres'):
                nutrients_data.append(['Fibres', f"{nutritional_data.get('fibres')} g"])

            nutrients_table = Table(nutrients_data, colWidths=[8*cm, 4*cm])
            nutrients_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#FF6B35')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#F8F9FA')),
                ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#2C3E50')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 11),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#DEE2E6')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            Story.append(nutrients_table)
            Story.append(Spacer(1, 1 * cm))

            # Recommandations
            recommendations = nutritional_data.get('recommandations', [])
            if recommendations:
                Story.append(Paragraph("💡 Recommandations", section_style))
                Story.append(Spacer(1, 0.2 * cm))

                rec_style = ParagraphStyle(
                    name='RecStyle',
                    fontName='Helvetica',
                    fontSize=11,
                    textColor=HexColor('#388E3C'),
                    leftIndent=20,
                    spaceAfter=0.1 * cm
                )

                for rec in recommendations:
                    Story.append(Paragraph(f"• {rec}", rec_style))

            # Générer le PDF
            doc.build(Story)

            # Retourner le PDF
            buffer.seek(0)
            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="analyse_nutritionnelle.pdf"'
            return response

        except Exception as e:
            return JsonResponse({'error': f'Erreur lors de la génération du PDF: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
