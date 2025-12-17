from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser

    # Champs à afficher dans la liste
    list_display = (
        'email', 
        'nom_complet', 
        'role', 
        'num_tel', 
        'ville', 
        'photo_tag',  # Photo affichée en miniature
        'is_staff', 
        'is_superuser', 
        'is_active'
    )

    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')

    fieldsets = (
        (None, {'fields': ('email', 'nom_complet', 'password', 'role', 'num_tel', 'ville', 'pdp')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'is_active', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nom_complet', 'password1', 'password2', 'role', 'num_tel', 'ville', 'pdp', 'is_staff', 'is_superuser', 'is_active')}
        ),
    )

    search_fields = ('email', 'nom_complet', 'ville', 'role')
    ordering = ('email',)

    # ✅ Affichage réel de la photo dans la liste
    def photo_tag(self, obj):
        if obj.pdp:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit:cover; border-radius:50%;" />',
                obj.pdp.url
            )
        return "-"
    photo_tag.short_description = 'Photo'

# Enregistrement
admin.site.register(CustomUser, CustomUserAdmin)
