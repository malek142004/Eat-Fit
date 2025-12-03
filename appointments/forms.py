from django import forms
from .models import Appointment
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
