from django import forms
from .models import BusinessOwner
from users.models import CustomUser

class BusinessOwnerForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role='business_owner'),
        required=True,
        label="Owner User"
    )

    class Meta:
        model = BusinessOwner
        fields = '__all__'
