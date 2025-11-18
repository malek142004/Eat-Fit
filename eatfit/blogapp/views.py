# blogapp/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Blog, Comment
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone

from django.http import HttpResponseForbidden
from .forms import BlogForm

def blog_list(request):
    # option : afficher les plus aimés / paginer etc.
    blogs = Blog.objects.annotate(num_likes=Count('likes')).all()
    return render(request, 'blogapp/blog_list.html', {'blogs': blogs})

def blog_detail(request, pk):
    blog = get_object_or_404(Blog, pk=pk)
    comments = blog.comments.filter(is_active=True)  # grâce à related_name
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "Vous devez être connecté pour commenter.")
            return redirect('login')
        content = request.POST.get('content', '').strip()
        if content:
            Comment.objects.create(
                blog=blog,
                author=request.user,
                content=content,
                created_at=timezone.now()
            )
            messages.success(request, "Commentaire ajouté.")
            return redirect('blogapp:blog_detail', pk=blog.pk)
        else:
            messages.error(request, "Le commentaire est vide.")
    liked = False
    if request.user.is_authenticated:
        liked = request.user in blog.likes.all()
    return render(request, 'blogapp/blog_detail.html', {
        'blog': blog,
        'comments': comments,
        'liked': liked,
    })

@login_required
def toggle_like(request, pk):
    blog = get_object_or_404(Blog, pk=pk)
    user = request.user
    if user in blog.likes.all():
        blog.likes.remove(user)
        messages.info(request, "Vous n'aimez plus cet article.")
    else:
        blog.likes.add(user)
        messages.success(request, "Vous aimez cet article.")
    return redirect('blogapp:blog_detail', pk=pk)


# CREATE
@login_required
def blog_create(request):
    """
    - GET : afficher le formulaire vide
    - POST: valider et créer l'article (assigner l'auteur = request.user)
    """
    if request.method == 'POST':
        form = BlogForm(request.POST)
        if form.is_valid():
            blog = form.save(commit=False)  # on obtient l'objet sans l'enregistrer
            blog.author = request.user      # attribuer l'auteur actuel
            blog.save()                     # maintenant on enregistre en base
            messages.success(request, "Article créé avec succès.")
            return redirect('blogapp:blog_detail', pk=blog.pk)
    else:
        form = BlogForm()
    return render(request, 'blogapp/blog_form.html', {'form': form, 'title': 'Créer un article'})

# UPDATE
@login_required
def blog_update(request, pk):
    """
    - Vérifie que l'utilisateur est l'auteur
    - GET : pré-remplit le formulaire avec instance=blog
    - POST: sauvegarde les modifications si valide
    """
    blog = get_object_or_404(Blog, pk=pk)
    if blog.author != request.user:
        return HttpResponseForbidden("Vous n'êtes pas autorisé à modifier cet article.")
    if request.method == 'POST':
        form = BlogForm(request.POST, instance=blog)
        if form.is_valid():
            form.save()
            messages.success(request, "Article mis à jour.")
            return redirect('blogapp:blog_detail', pk=blog.pk)
    else:
        form = BlogForm(instance=blog)
    return render(request, 'blogapp/blog_form.html', {'form': form, 'title': 'Modifier l’article'})

# DELETE
@login_required
def blog_delete(request, pk):
    """
    - GET : afficher une page de confirmation
    - POST: supprimer définitivement l'article
    - Seul l'auteur peut supprimer
    """
    blog = get_object_or_404(Blog, pk=pk)
    if blog.author != request.user:
        return HttpResponseForbidden("Vous n'êtes pas autorisé à supprimer cet article.")
    if request.method == 'POST':
        blog.delete()
        messages.success(request, "Article supprimé.")
        return redirect('blogapp:blog_list')
    return render(request, 'blogapp/blog_confirm_delete.html', {'blog': blog})