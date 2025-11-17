from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class CustomUserCreationForm(UserCreationForm):
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
