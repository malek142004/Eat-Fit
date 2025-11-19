from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import (
    RegexValidator, MinLengthValidator, EmailValidator , MinValueValidator
)
from django.core.exceptions import ValidationError



def validate_nom(value):
    if not all(c.isalpha() or c.isspace() for c in value):
        raise ValidationError("Le nom complet ne doit contenir que des lettres et des espaces.")



def validate_ville(value):
    if not all(c.isalpha() or c.isspace() for c in value):
        raise ValidationError("Le nom de la ville ne doit contenir que des lettres et des espaces.")


class CustomUserManager(BaseUserManager):
    def create_user(self, email, nom_complet, password=None, **extra_fields):
        """Créer un utilisateur normal"""
        if not email:
            raise ValueError("L'utilisateur doit avoir une adresse email.")
        email = self.normalize_email(email)
        user = self.model(email=email, nom_complet=nom_complet, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nom_complet, password=None, **extra_fields):
        """Créer un superutilisateur"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Le superutilisateur doit avoir is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Le superutilisateur doit avoir is_superuser=True.")

        return self.create_user(email, nom_complet, password, **extra_fields)



class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator(message="Veuillez entrer une adresse e-mail valide.")]
    )

    nom_complet = models.CharField(
        max_length=150,
        validators=[
            validate_nom,
            MinLengthValidator(3, message="Le nom complet doit comporter au moins 3 caractères.")
        ]
    )

    ROLE_CHOICES = (
        ('client', 'Client'),
        ('business_owner', 'Business Owner'),
        ('nutritionist', 'Nutritionniste'),
        ('coach', 'Coach'),
        ('admin', 'Admin'),
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='client'
    )

    num_tel = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^[0-9]{8,15}$',
                message="Le numéro de téléphone doit contenir uniquement des chiffres (8 à 15 caractères)."
            )
        ]
    )

    ville = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        validators=[validate_ville]
    )

    pdp = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom_complet']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.nom_complet} ({self.email}) {self.pdp}"

class Nutritionist(CustomUser):   # ✨ HÉRITAGE (multi-table)
    speciality = models.CharField(max_length=100, blank=True)
    experience_years = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    office_address = models.CharField(max_length=255, blank=True)
    # Use DecimalField for monetary values
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    availability = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Nutritionist: {self.nom_complet} "

# Héritage multi-table pour Coach

class Coach(CustomUser): # Héritage multi-table (pour respecter la demande)
    SPORT_TYPES = [
        ('fitness', 'Fitness'),
        ('yoga', 'Yoga'),
        ('cardio', 'Cardio'),
        ('musculation', 'Musculation'),
        ('crossfit', 'CrossFit'),
    ]
    
    # Les champs qui étaient dans la première version de Coach
    sport_type = models.CharField(max_length=50, choices=SPORT_TYPES)
    experience_years = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)]) # Utilise PositiveIntegerField et validator
    session_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00) # Utilise DecimalField pour la monnaie
    subscription_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00) # Utilise DecimalField pour la monnaie
    location = models.CharField(max_length=255)
    bio = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    
    # Champs NEW FIELDS
    certifications = models.TextField(
        blank=True, 
        help_text="Coach certifications and credentials"
    )
    show_on_website = models.BooleanField(
        default=True, 
        help_text="Display this coach on the public trainers page"
    )

    def __str__(self):
        return f"Coach: {self.nom_complet} - {self.sport_type}"

    def generate_training_plan(self):
        return f"Training plan generated for {self.nom_complet}"

    def manage_appointments(self):
        return f"Appointments managed for {self.nom_complet}"