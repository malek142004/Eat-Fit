from django.contrib import admin
from .models import BusinessOwner

# Register your models here.

@admin.register(BusinessOwner)
class BusinessOwnerAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'get_owner_name', 'professional_email', 'professional_phone')
    search_fields = ('business_name', 'professional_email', 'user__email', 'user__nom_complet')
    list_filter = ('professional_email',)

    def get_owner_name(self, obj):
        return obj.user.nom_complet
    get_owner_name.short_description = "Owner Name"

