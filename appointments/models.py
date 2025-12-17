from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class Client(models.Model):
    nom_complet = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    num_tel = models.CharField(max_length=20, default='')
    ville = models.CharField(max_length=100, default='')
    pdp = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom_complet
    
    
class Appointment(models.Model):
    STATUS_CHOICES = [
        ('untreated', 'Untreated'),
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    MODE_CHOICES = [
        ('face_to_face', 'Face to Face'),
        ('visio', 'Visio'),
    ]

    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointments', limit_choices_to={'role': 'client'})
    professional = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='professional_appointments', limit_choices_to={'role__in': ['coach', 'nutritionist']})
    appointment_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='face_to_face')
    visio_link = models.URLField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='untreated')
    created_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Appointment for {self.client} on {self.appointment_date} at {self.start_time}"

class TrainingProgram(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='training_programs')
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Feedback(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback_given')
    coach = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback_received')
    rating = models.PositiveSmallIntegerField()  # 1 to 5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['coach']),
        ]

    def __str__(self):
        return f"Feedback from {self.client} to {self.coach}"


class Wallet(models.Model):
    user = models.OneToOneField('users.CustomUser', on_delete=models.CASCADE, related_name='wallet')
    points = models.IntegerField(default=0)

    def __str__(self):
        return f"Wallet({self.user.email}): {self.points} pts"


class Coupon(models.Model):
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='coupons')
    code = models.CharField(max_length=32, unique=True)
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    redeemed = models.BooleanField(default=False)
    redeemed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Coupon({self.code}) - {self.amount} dt - Redeemed: {self.redeemed}"