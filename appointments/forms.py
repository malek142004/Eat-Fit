from django import forms
from .models import Appointment, Client, TrainingProgram, Feedback
from django.contrib.auth import get_user_model

User = get_user_model()

class AppointmentCreateForm(forms.ModelForm):
    client = forms.ModelChoiceField(
        queryset=User.objects.filter(role='client'),
        label="Client",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control-custom'})
    )
    professional = forms.ModelChoiceField(
        queryset=User.objects.filter(role__in=['coach', 'nutritionist']),
        label="Professional",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control-custom'})
    )

    class Meta:
        model = Appointment
        fields = ['client', 'professional', 'appointment_date', 'start_time', 'end_time', 'mode', 'visio_link']
        widgets = {
            'appointment_date': forms.DateInput(
                attrs={'type': 'date', 'placeholder': 'Appointment Date'}
            ),
            'start_time': forms.TimeInput(
                attrs={'type': 'time', 'placeholder': 'Start Time'}
            ),
            'end_time': forms.TimeInput(
                attrs={'type': 'time', 'placeholder': 'End Time'}
            ),
            'visio_link': forms.TextInput(attrs={'placeholder': 'Lien Visio (si applicable)'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        professional = kwargs.pop('professional', None)
        super(AppointmentCreateForm, self).__init__(*args, **kwargs)
        
        if user and user.role == 'client':
            self.fields['client'].widget = forms.HiddenInput()
            self.fields['client'].required = False
            self.fields['client'].initial = user
        
        if professional:
            self.fields['professional'].widget = forms.HiddenInput()
            self.fields['professional'].required = False
            self.fields['professional'].initial = professional
        
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control-custom'
            if isinstance(field.widget, forms.Textarea):
                 field.widget.attrs['rows'] = 4

class AppointmentUpdateForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['appointment_date', 'start_time', 'end_time', 'mode', 'visio_link', 'status']
        widgets = {
            'appointment_date': forms.DateInput(
                attrs={'type': 'date', 'placeholder': 'Appointment Date'}
            ),
            'start_time': forms.TimeInput(
                attrs={'type': 'time', 'placeholder': 'Start Time'}
            ),
            'end_time': forms.TimeInput(
                attrs={'type': 'time', 'placeholder': 'End Time'}
            ),
            'visio_link': forms.TextInput(attrs={'placeholder': 'Lien Visio (si applicable)'}),
        }

    def __init__(self, *args, **kwargs):
        super(AppointmentUpdateForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control-custom'
            if isinstance(field.widget, forms.Textarea):
                 field.widget.attrs['rows'] = 4
                 
class ClientUpdateForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['nom_complet', 'email', 'num_tel', 'ville']
        widgets = {
            'nom_complet': forms.TextInput(attrs={'placeholder': 'Nom Complet'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
            'num_tel': forms.TextInput(attrs={'placeholder': 'Numéro de Téléphone'}),
            'ville': forms.TextInput(attrs={'placeholder': 'Ville'}),
        }

    def __init__(self, *args, **kwargs):
        super(ClientUpdateForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control-custom'

class TrainingProgramForm(forms.ModelForm):
    class Meta:
        model = TrainingProgram
        fields = ['name', 'price', 'level', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super(TrainingProgramForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control-custom'

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Votre commentaire (optionnel)'}),
        }
        labels = {
            'rating': 'Note (1 à 5)',
            'comment': 'Commentaire',
<<<<<<< HEAD
        }


class ManualPredictionFeaturesForm(forms.Form):
    GENDER_CHOICES = [(1, 'Homme'), (0, 'Femme')]
    age = forms.IntegerField(label="Âge du client", min_value=0)
    gender = forms.ChoiceField(label="Genre du client", choices=GENDER_CHOICES)

    def __init__(self, *args, **kwargs):
        super(ManualPredictionFeaturesForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
=======
        }
>>>>>>> 1a8f9733996aab58de030e31a9be7f3d02d657cb
