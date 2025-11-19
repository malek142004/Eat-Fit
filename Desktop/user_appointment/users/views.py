# users/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Q
from .forms import CustomUserCreationForm, CustomAuthenticationForm, CustomUserUpdateForm, NutritionistForm , CoachForm
from .models import CustomUser as User, Nutritionist , Coach
from .forms import UserForm, CoachForm
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
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# Assurez-vous d'importer Coach (votre modèle) et CoachForm (votre formulaire)
from .models import Coach
from .forms import CoachForm

# views.py

@login_required
def coach_create(request):
    user = request.user
    
    # 1. LOGIQUE DE REDIRECTION (Vérifie si le profil Coach complet existe)
    if user.role == 'coach':
        try:
            Coach.objects.get(pk=user.pk) 
            messages.info(request, "Vous êtes déjà un Coach. Vous pouvez modifier votre profil.")
            return redirect('users:coach_update', pk=user.pk)
        except Coach.DoesNotExist:
            pass
            
    # --- 2. LOGIQUE DE TRAITEMENT POST ---
    if request.method == 'POST':
        # 🟢 Utiliser le nom d'argument correct : 'instance'
        form = CoachForm(request.POST, request.FILES, instance=user)
        
        if form.is_valid():
            form.save() 
            messages.success(request, 'Félicitations, votre profil Coach est créé !')
            return redirect('users:coach_list') 
        
    # --- 3. LOGIQUE D'AFFICHAGE INITIAL (GET) ---
    else: 
        # 🟢 Simplifier et utiliser le nom d'argument correct : 'instance'
        # On passe l'objet CustomUser. Les champs Coach seront vides, ce qui est normal pour une création.
        form = CoachForm(instance=request.user)

    # --- 4. RENDU FINAL ---
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


def add_coach(request):
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