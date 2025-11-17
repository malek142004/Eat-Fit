from django.db import models
from users.models import CustomUser
# Create your models here.

class BusinessOwner(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    business_name = models.CharField(max_length=100)
    business_description = models.TextField(blank=True, null=True)
    address = models.CharField(max_length=255)
    professional_email = models.EmailField(unique=True)
    professional_phone = models.CharField(max_length=20)
    social_media_account = models.CharField(max_length=255, blank=True, null=True)
    business_logo = models.ImageField(upload_to='business_logos/', blank=True, null=True)

    def __str__(self):
        return self.business_name

