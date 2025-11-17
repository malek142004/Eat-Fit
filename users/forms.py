from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser

# Formulaire d'inscription
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("email", "nom_complet", "role", "num_tel", "ville", "pdp")


# Formulaire de mise à jour du profil
class CustomUserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['nom_complet', 'email', 'num_tel', 'ville', 'role', 'pdp']


# Formulaire de connexion personnalisé pour utiliser l'email comme identifiant
class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email")  # Renomme "username" en "Email"
