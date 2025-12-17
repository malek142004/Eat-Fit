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
import torch
from transformers import BertTokenizer, BertForSequenceClassification
from torch.nn.functional import sigmoid

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
    comments = blog.comments.filter(is_active=True)  # IMPORTANT: Filtrer seulement les commentaires actifs
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "Vous devez être connecté pour commenter.")
            return redirect('login')
        
        content = request.POST.get('content', '').strip()
        if content:
            try:
                toxicity = analyze_toxicity(content)
                
                if toxicity > 0.6:
                    # NE PAS créer le commentaire OU le créer avec is_active=False
                    # Option 1: Ne pas créer du tout (recommandé)
                    messages.error(
                        request,
                        "Votre commentaire contient un contenu inapproprié et ne peut pas être publié. "
                        "Veuillez modifier votre texte et réessayer."
                    )
                    # OU Option 2: Créer mais invisible (pour modération admin)
                    # Comment.objects.create(
                    #     blog=blog,
                    #     author=request.user,
                    #     content=content,
                    #     toxicity_score=toxicity,
                    #     is_flagged=True,
                    #     is_active=False  # CRITIQUE: Doit être False
                    # )
                else:
                    # Créer le commentaire normalement
                    Comment.objects.create(
                        blog=blog,
                        author=request.user,
                        content=content,
                        toxicity_score=toxicity,
                        is_flagged=False,
                        is_active=True
                    )
                    messages.success(request, "Commentaire ajouté avec succès.")
                
                return redirect('blogapp:blog_detail', pk=blog.pk)
                
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Comment toxicity analysis failed: {str(e)}")
                
                messages.warning(
                    request,
                    "Impossible de vérifier le contenu pour le moment. Veuillez réessayer plus tard."
                )
                return redirect('blogapp:blog_detail', pk=blog.pk)
        else:
            messages.error(request, "Le commentaire est vide.")
            return redirect('blogapp:blog_detail', pk=blog.pk)
    
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
    if request.method == 'POST':
        form = BlogForm(request.POST)
        if form.is_valid():
            blog = form.save(commit=False)
            blog.author = request.user

            try:
                # Check toxicity in all text fields
                content_toxicity = analyze_toxicity(blog.content)
                title_toxicity = analyze_toxicity(blog.title)
                preview_toxicity = analyze_toxicity(blog.preview) if blog.preview else 0
                
                # Use the highest toxicity score
                toxicity = max(content_toxicity, title_toxicity, preview_toxicity)
                blog.toxicity_score = toxicity

                if toxicity > 0.6:
                    blog.is_flagged = True
                    messages.error(
                        request,
                        "Votre article contient un contenu inapproprié et ne peut pas être publié. "
                        "Veuillez modifier votre texte et réessayer."
                    )
                    # Return form with user's data preserved
                    return render(request, 'blog/blogapp/blog_form.html', {
                        'form': form,
                        'title': 'Créer un article'
                    })

                blog.save()
                messages.success(request, "Article créé avec succès.")
                return redirect('blogapp:blog_detail', pk=blog.pk)
                
            except Exception as e:
                # Log the error for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Toxicity analysis failed: {str(e)}")
                
                messages.warning(
                    request,
                    "Impossible de vérifier le contenu pour le moment. Veuillez réessayer plus tard."
                )
                return render(request, 'blog/blogapp/blog_form.html', {
                    'form': form,
                    'title': 'Créer un article'
                })
    else:
        form = BlogForm()

    return render(request, 'blog/blogapp/blog_form.html', {
        'form': form,
        'title': 'Créer un article'
    })

# UPDATE
@login_required
def blog_update(request, pk):
    """
    - Vérifie que l'utilisateur est l'auteur
    - GET : pré-remplit le formulaire avec instance=blog
    - POST: sauvegarde les modifications si valide, avec détection de bad words
    """
    blog = get_object_or_404(Blog, pk=pk)
    if blog.author != request.user:
        return HttpResponseForbidden("Vous n'êtes pas autorisé à modifier cet article.")

    if request.method == 'POST':
        form = BlogForm(request.POST, instance=blog)
        if form.is_valid():
            blog_temp = form.save(commit=False)
            
            try:
                # Analyse de toxicité sur tous les champs textuels
                content_toxicity = analyze_toxicity(blog_temp.content)
                title_toxicity = analyze_toxicity(blog_temp.title)
                preview_toxicity = analyze_toxicity(blog_temp.preview) if blog_temp.preview else 0
                
                toxicity = max(content_toxicity, title_toxicity, preview_toxicity)
                blog_temp.toxicity_score = toxicity

                if toxicity > 0.6:
                    blog_temp.is_flagged = True
                    messages.error(
                        request,
                        "Votre article contient un contenu inapproprié et ne peut pas être publié. "
                        "Veuillez modifier votre texte et réessayer."
                    )
                    return render(request, 'blog/blogapp/blog_form.html', {
                        'form': form,
                        'title': 'Modifier l’article'
                    })

                # Enregistrer normalement si OK
                blog_temp.save()
                messages.success(request, "Article mis à jour avec succès.")
                return redirect('blogapp:blog_detail', pk=blog.pk)

            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Toxicity analysis failed: {str(e)}")
                messages.warning(
                    request,
                    "Impossible de vérifier le contenu pour le moment. Veuillez réessayer plus tard."
                )
                return render(request, 'blog/blogapp/blog_form.html', {
                    'form': form,
                    'title': 'Modifier l’article'
                })

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



MODEL_NAME = "MaryemOuichka/toxic-bert-custom"

tokenizer = BertTokenizer.from_pretrained(MODEL_NAME)
model = BertForSequenceClassification.from_pretrained(MODEL_NAME)

model.eval()  # mode inference

LABEL_COLS = [
    "toxic",
    "severe_toxic",
    "obscene",
    "threat",
    "insult",
    "identity_hate"
]


def analyze_toxicity(text: str) -> float:
    """
    Retourne un score global de toxicité entre 0 et 1
    """
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=128
    )

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.sigmoid(outputs.logits)[0]

    return probs.max().item()