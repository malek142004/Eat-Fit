from django import forms
from .models import Appointment, Client

class AppointmentCreateForm(forms.ModelForm):
    # Fields for new client information
    nom_complet = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'placeholder': 'Nom Complet'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    num_tel = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'placeholder': 'Numéro de Téléphone'}))
    ville = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'placeholder': 'Ville'}))

    class Meta:
        model = Appointment
        fields = ['appointment_date', 'start_time', 'end_time', 'mode', 'visio_link']
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
        super(AppointmentCreateForm, self).__init__(*args, **kwargs)
        # Apply custom CSS class to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control-custom'
            if isinstance(field.widget, forms.Textarea):
                 field.widget.attrs['rows'] = 4

class AppointmentUpdateForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['appointment_date', 'start_time', 'end_time', 'mode', 'visio_link']
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
        # Apply custom CSS class to all fields
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