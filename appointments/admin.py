from django.contrib import admin
from .models import Appointment

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('client', 'appointment_date', 'start_time', 'end_time', 'mode', 'status', 'created_at')
    list_filter = ('mode', 'status', 'appointment_date')
    search_fields = ('client__nom_complet',)
    autocomplete_fields = ('client',)
