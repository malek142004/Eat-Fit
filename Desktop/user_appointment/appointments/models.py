
from django.db import models

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
    MODE_CHOICES = [
        ('face_to_face', 'Face to Face'),
        ('visio', 'Visio'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    visio_link = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Appointment for {self.client} on {self.appointment_date}"
