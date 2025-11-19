from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, Nutritionist # Assurez-vous d'importer Nutritionist
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
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['nom_complet'].initial = user.nom_complet
            self.fields['email'].initial = user.email
            self.fields['ville'].initial = user.ville
            self.fields['num_tel'].initial = user.num_tel
            self.fields['pdp'].initial = user.pdp
            self.fields['password'].initial = ''  # vide par défaut

    def save(self, commit=True):
        instance = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            instance.set_password(password)

        # ⚡️ Forcer le rôle à 'nutritionist'
        instance.role = 'nutritionist'

        if commit:
            instance.save()
        return instance
