from django.db import models
from django.conf import settings
from django.utils import timezone

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
