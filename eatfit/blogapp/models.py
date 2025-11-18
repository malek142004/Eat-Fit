from django.db import models
from django.conf import settings
from django.utils import timezone


class Blog(models.Model):
    THEMES = [
        ('nutrition', 'Nutrition'),
        ('fitness', 'Fitness'),
        ('wellness', 'Santé & Bien-être'),
        ('consultation', 'Consultation'),
        ('ia', 'IA & Technologie'),
        ('products', 'Produits & Lifestyle'),
    ]

    title = models.CharField(max_length=200, null=True, blank=True)
    theme = models.CharField(max_length=20, choices=THEMES)
    preview = models.TextField(max_length=200, null=True, blank=True)
    content = models.TextField(max_length=500)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blogs'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='liked_blogs',
        blank=True
    )

    class Meta:
        ordering = ['-created_at']  

    def __str__(self):
        return self.title

    def total_likes(self):
        return self.likes.count()


class Comment(models.Model):
    blog = models.ForeignKey(
        Blog,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at'] 

    def __str__(self):
        return f"Comment by {self.author.username} on {self.blog.title}"
