# blogapp/forms.py
from django import forms
from .models import Blog, Comment

class BlogForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ['title', 'theme', 'preview', 'content']  # tous les champs modifiables
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Un titre qui donne envie de cliquer...',
                'class': 'form-control'
            }),
            'theme': forms.Select(attrs={'class': 'form-control'}),
            'preview': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Un petit teaser qui apparaît sur la grille (max 200 caractères)',
                'class': 'form-control'
            }),
            'content': forms.Textarea(attrs={
                'rows': 15,
                'placeholder': 'Raconte tout ici... recettes, astuces fitness, mindset, etc.',
                'class': 'form-control'
            }),
        }
        labels = {
            'title': 'Titre de l’article',
            'theme': 'Thème',
            'preview': 'Extrait / Teaser (affiché sur la page d’accueil)',
            'content': 'Contenu complet',
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content', 'is_active']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'content': 'Commentaire',
            'is_active': 'Actif',
        }