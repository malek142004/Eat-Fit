from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, Nutritionist, Coach, BusinessOwner
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class CustomUserCreationForm(UserCreationForm):
    # ... (Le reste de la classe est inchangé)
    class Meta:
        model = CustomUser
        fields = ("email", "nom_complet", "role", "num_tel", "ville", "pdp")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # supprimer l'option admin
        self.fields['role'].choices = [
            (key, value) for key, value in self.fields['role'].choices if key != 'admin'
        ]

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        try:
            validate_password(password, self.instance)
        except ValidationError as e:
            self.add_error('password1', e)
        return password
    
    def clean_pdp(self):
        image = self.cleaned_data.get("pdp")
        if not image:
            return image

        import tempfile, os
        temp_path = os.path.join(tempfile.gettempdir(), image.name)

        with open(temp_path, "wb+") as temp_file:
            for chunk in image.chunks():
                temp_file.write(chunk)

        from .utils.face_validation import is_valid_profile_image

        if not is_valid_profile_image(temp_path):
            raise ValidationError(
                "La photo doit contenir une seule personne (pas d'animaux, pas de groupe, pas d'objets)."
            )

        return image


class CustomUserUpdateForm(forms.ModelForm):
    # ... (Le reste de la classe est inchangé)
    class Meta:
        model = CustomUser
        fields = ['nom_complet', 'email', 'num_tel', 'ville', 'role', 'pdp']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'nom_complet': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'num_tel': forms.TextInput(attrs={'class': 'form-control'}),
            'ville': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # supprimer l'option admin
        self.fields['role'].choices = [
            (key, value) for key, value in self.fields['role'].choices if key != 'admin'
        ]
class UserForm(forms.ModelForm):
    """
    Formulaire minimal pour mettre à jour les champs de base de CustomUser.
    Utilisé en conjonction avec CoachForm dans le backoffice.
    """
    class Meta:
        model = CustomUser
        # Incluez tous les champs CustomUser nécessaires pour le formulaire d'édition
        fields = ['nom_complet', 'email', 'num_tel', 'ville', 'pdp', 'role']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si on est en mode édition, on peut vouloir désactiver l'édition du rôle/email pour l'utilisateur lambda
        # (La vue backoffice aura sa propre logique)
        # Exemple : self.fields['email'].disabled = True
class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={'autofocus': True}))


class NutritionistForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput, 
        label="Mot de passe", 
        required=False
    )

    class Meta:
        model = Nutritionist
        fields = [
            'nom_complet',
            'email',
            'ville',
            'num_tel',
            'pdp',
            'password',
            'speciality',
            'experience_years',
            'office_address',
            'consultation_fee',
            'availability',
        ]

    def __init__(self, *args, **kwargs):
        # On garde une référence à l'utilisateur connecté pour pouvoir réutiliser sa photo de profil
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['nom_complet'].initial = self.user.nom_complet
            self.fields['email'].initial = self.user.email
            self.fields['ville'].initial = self.user.ville
            self.fields['num_tel'].initial = self.user.num_tel
            # Initial visuel, mais surtout on va réutiliser self.user.pdp dans save() si aucun fichier n'est uploadé
            self.fields['password'].initial = ''  # vide par défaut

    def save(self, commit=True):
        instance = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            instance.set_password(password)

        # Si aucune photo n'est envoyée dans le formulaire, on réutilise la photo de profil de l'utilisateur connecté
        if not instance.pdp and getattr(self, 'user', None) is not None:
            if getattr(self.user, 'pdp', None):
                instance.pdp = self.user.pdp

        # ⚡️ Forcer le rôle à 'nutritionist'
        instance.role = 'nutritionist'

        if commit:
            instance.save()
        return instance

#coach model

# users/forms.py
# users/forms.py
class CoachForm(forms.ModelForm):
    # 🟢 Champ email désactivé pour l'affichage (recommandé si l'instance est CustomUser)
    email = forms.EmailField(disabled=True, required=False) 

    # ❌ Pas de champ password ici si vous gérez l'utilisateur existant
    # Le champ password a été retiré, c'est bien.

    class Meta: # ⬅️ CETTE CLASSE ÉTAIT MANQUANTE OU INCOMPLÈTE DANS VOTRE CODE
        model = Coach # ⬅️ CRITIQUE : Définit le modèle de base du formulaire
        fields = (
            # Champs de CustomUser
            'email', 'nom_complet', 'num_tel', 'ville', 'pdp', 
            
            # Champs de Coach
            'sport_type', 'experience_years', 'location', 'session_price', 
            'subscription_price', 'bio', 'certifications', 'is_available', 'show_on_website'
        )

    def __init__(self, *args, **kwargs):
        # 🟢 Laissez cette partie simple pour gérer l'instance CustomUser/Coach
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Désactiver les champs clés si l'instance existe
            self.fields['email'].disabled = True
            
    # La méthode save() (que vous avez fournie) semble correcte pour la logique d'héritage.
    def save(self, commit=True):
        # ... (votre code de la méthode save() est conservé ici) ...
        # 1. Obtenir l'instance CustomUser mise à jour par le formulaire
        user_instance = super().save(commit=False)
        
        # 2. Forcer le rôle
        user_instance.role = 'coach'
        
        # 3. Sauvegarder l'objet CustomUser
        if commit:
            user_instance.save()
            
        # 4. LOGIQUE CRITIQUE DE CRÉATION DE L'ENFANT
        coach_data = {
             'sport_type': self.cleaned_data.get('sport_type'),
             'experience_years': self.cleaned_data.get('experience_years'),
             'session_price': self.cleaned_data.get('session_price'),
             'subscription_price': self.cleaned_data.get('subscription_price'),
             'location': self.cleaned_data.get('location'),
             'bio': self.cleaned_data.get('bio'),
             'is_available': self.cleaned_data.get('is_available'),
             'certifications': self.cleaned_data.get('certifications'),
             'show_on_website': self.cleaned_data.get('show_on_website'),
         }

        try:
            # Mise à jour si existe
            coach_obj = Coach.objects.get(pk=user_instance.pk)
            for field, value in coach_data.items():
                setattr(coach_obj, field, value)
                
        except Coach.DoesNotExist:
            # Création si n'existe pas
            coach_obj = Coach()
            coach_obj.pk = user_instance.pk
            
            for field, value in coach_data.items():
                 setattr(coach_obj, field, value)
            
            if commit:
                # Création de l'objet enfant
                coach_obj.save_base(raw=True) # Créer l'enfant avec la même PK
                
        # Sauvegarde finale (pour les mises à jour et les données du formulaire)
        if commit:
            coach_obj.save() 
            
        return coach_obj
    

from django import forms
from .models import BusinessOwner

class BusinessOwnerForm(forms.ModelForm):
    class Meta:
        model = BusinessOwner
        fields = [
            'business_name',
            'business_description',
            'address',
            'professional_email',
            'professional_phone',
            'social_media_account',
            'business_logo'
        ]

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField()