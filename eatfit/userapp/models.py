from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    user_id = models.AutoField(primary_key=True)  # identifiant unique
    email = models.EmailField()
    role = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)

    # username et password sont déjà présents dans AbstractUser
    # firstname et lastname existent aussi, donc tu peux utiliser ceux hérités si tu veux

    def __str__(self):
        return self.username

