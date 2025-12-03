# blogapp/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Blog, Comment
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone
from django.db.models import Q, Count
from django.http import HttpResponseForbidden
from .forms import BlogForm
from blogapp.forms import BlogForm,CommentForm
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
import requests
from huggingface_hub import InferenceClient

from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import render
from .models import Blog

def blog_list(request):
    blogs = Blog.objects.annotate(
        num_likes=Count('likes'),
        num_comments=Count('comments')
    )

    # 🔍 RECHERCHE
    search_query = request.GET.get("q", "").strip()
    if search_query:
        blogs = blogs.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(preview__icontains=search_query)
        )

    # 🎨 FILTRE PAR THÈME
    theme = request.GET.get("theme")
    if theme and theme != "all":
        blogs = blogs.filter(theme=theme)

    # ❤️ TRI
    sort = request.GET.get("sort")
    if sort == "likes":
        blogs = blogs.order_by("-num_likes")
    elif sort == "comments":
        blogs = blogs.order_by("-num_comments")
    elif sort == "newest":
        blogs = blogs.order_by("-created_at")
    elif sort == "oldest":
        blogs = blogs.order_by("created_at")

    # Pagination
    paginator = Paginator(blogs, 6)  # 6 articles par page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Toutes les catégories disponibles
    themes = dict(Blog.THEMES)

    return render(request, 'blog/blogapp/blog_list.html', {
        'blogs': page_obj.object_list,
        'themes': themes,
        'search_query': search_query,
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
    })



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
    return render(request, 'blog/blogapp/blog_detail.html', {
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
    return render(request, 'blog/blogapp/blog_form.html', {'form': form, 'title': 'Créer un article'})

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
    return render(request, 'blog/blogapp/blog_form.html', {'form': form, 'title': 'Modifier l’article'})

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
    return render(request, 'blog/blogapp/blog_confirm_delete.html', {'blog': blog})



#backoffiche 

def backoffice_tables(request):
    blogs = Blog.objects.all().order_by('-created_at')
    return render(request, 'backoffice/tables_blogs.html', {'blogs': blogs})




# Détail d’un blog

def backoffice_detail(request, pk):
    blog = get_object_or_404(Blog, pk=pk)
    return render(request, 'backoffice/blog_detail.html', {'blog': blog})


# Création d’un blog

def backoffice_create(request):
    if request.method == 'POST':
        form = BlogForm(request.POST)
        if form.is_valid():
            blog = form.save(commit=False)
            blog.author = request.user  # définit l'auteur automatiquement
            blog.save()
            return redirect('blogapp:blogs_list')
    else:
        form = BlogForm()
    
    return render(request, 'backoffice/blog_edit.html', {'form': form})


# Modification d’un blog

def backoffice_edit(request, pk):
    blog = get_object_or_404(Blog, pk=pk)

    if request.method == 'POST':
        form = BlogForm(request.POST, instance=blog)
        if form.is_valid():
            form.save()
            return redirect('blogapp:blogs_list')
    else:
        form = BlogForm(instance=blog)

    return render(request, 'backoffice/blog_edit.html', {
        'blog': blog,
        'form': form,
    })


# Suppression d’un blog

def backoffice_delete(request, pk):
    blog = get_object_or_404(Blog, pk=pk)
    if request.method == 'POST':
        blog.delete()
        return redirect('blogapp:blogs_list')  # Retour à la liste
    return render(request, 'backoffice/blog_confirm_delete.html', {'blog': blog})



# Ajouter un commentaire depuis le détail du blog

def backoffice_comment_create(request, blog_pk):
    blog = get_object_or_404(Blog, pk=blog_pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.blog = blog
            comment.author = request.user  # admin qui crée le commentaire
            comment.save()
            return redirect('blogapp:backoffice_detail', pk=blog.pk)
    else:
        form = CommentForm()
    return render(request, 'backoffice/comment_form.html', {'form': form, 'blog': blog, 'action': 'Ajouter'})

# Modifier un commentaire

def backoffice_comment_edit(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blogapp:backoffice_detail', pk=comment.blog.pk)
    else:
        form = CommentForm(instance=comment)
    return render(request, 'backoffice/comment_form.html', {'form': form, 'blog': comment.blog, 'action': 'Modifier'})

# Supprimer un commentaire

def backoffice_comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    blog_pk = comment.blog.pk
    if request.method == 'POST':
        comment.delete()
        return redirect('blogapp:backoffice_detail', pk=blog_pk)
    return render(request, 'backoffice/comment_confirm_delete.html', {'comment': comment})




def blog_to_pdf(request, pk):
    blog = Blog.objects.get(pk=pk)
    html = render_to_string('blog/blogapp/pdf_template.html', {'blog': blog})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{blog.title}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Erreur lors de la génération du PDF')
    return response



HF_TOKEN = "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"
client = InferenceClient(
    provider="hf-inference",
    api_key=HF_TOKEN,  # Assure-toi que HF_TOKEN est défini
)

def summarize_blog(request, pk):
    blog = get_object_or_404(Blog, pk=pk)

    try:
        text_to_summarize = blog.content

        # Appel API pour résumé
        result = client.summarization(
            text_to_summarize,
            model="facebook/bart-large-cnn"
        )

        # Vérification robuste de la réponse
        if result:
            if isinstance(result, list):
                first_item = result[0]
                summary = first_item.get("summary_text") or first_item.get("generated_text") or "Résumé introuvable."
            elif isinstance(result, dict):
                summary = result.get("summary_text") or result.get("generated_text") or "Résumé introuvable."
            else:
                summary = "Format de réponse inconnu."
        else:
            summary = "Aucun résultat retourné par le modèle."

    except Exception as e:
        summary = f"Erreur lors du résumé : {e}"

    return render(request, "blog/blogapp/blog_summary.html", {
        "blog": blog,
        "summary": summary
    })