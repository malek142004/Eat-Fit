
from django.contrib import admin
from django.utils.html import mark_safe
from .models import Client, Appointment

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('nom_complet', 'email', 'num_tel', 'ville', 'pdp_preview')
    search_fields = ('nom_complet', 'email')

    def pdp_preview(self, obj):
        if obj.pdp:
            return mark_safe(f'<img src="{obj.pdp.url}" width="50" height="50" />')
        return "(No image)"
    pdp_preview.short_description = 'Profile Picture'

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('client', 'appointment_date', 'start_time', 'end_time', 'mode', 'visio_link', 'created_at', 'modified_at')
    list_filter = ('mode', 'appointment_date')
    search_fields = ('client__nom_complet',)
    autocomplete_fields = ('client',)
