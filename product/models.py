# products/models.py
from django.db import models
from businessowner.models import BusinessOwner
from django.conf import settings   
class Product(models.Model):
    CATEGORY_CHOICES = [
        ('Food', 'Food'),
        ('Drink', 'Drink'),
        ('Supplement', 'Supplement'),
        ('Equipment', 'Equipment'),
        ('Snacks', 'Snacks'),
        ('Protein', 'Protein'),
        ('Vitamins', 'Vitamins'),
        ('Organic', 'Organic'),
        ('Vegan', 'Vegan'),
        ('Others', 'Others'),
    ]

    business_owner = models.ForeignKey(BusinessOwner, on_delete=models.CASCADE, related_name='products')
    product_name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    price = models.FloatField()
    discount = models.FloatField(default=0)
    image_url = models.URLField(blank=True, null=True)
    creation_date = models.DateField(auto_now_add=True)
    ingredients = models.TextField(blank=True, null=True)
    calories = models.PositiveIntegerField(blank=True, null=True)
    def __str__(self):
        return self.product_name
    @property
    def average_rating(self):
        ratings = self.ratings.all()
        if ratings.exists():
            return round(sum(r.rating for r in ratings) / ratings.count(), 1)
        return 0
    
class Rating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()  # 1 à 5 étoiles
    comment = models.TextField(blank=True, null=True)  # facultatif

    class Meta:
        unique_together = ('product', 'user')  # un client ne peut noter qu'une fois

    def __str__(self):
        return f"{self.user.email} - {self.product.product_name} : {self.rating}"
    
