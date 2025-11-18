from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from blogapp.models import Blog, Comment
from blogapp.forms import BlogForm,CommentForm


# Dashboard
@login_required
def backoffice_dashboard(request):
    return render(request, 'backoffice/dashboard.html')

def backoffice_blank(request):
    return render(request, 'backoffice/blank.html')

def backoffice_cards(request):
    return render(request, 'backoffice/cards.html')

def backoffice_charts(request):
    return render(request, 'backoffice/charts.html')

def backoffice_forgot_password(request):
    return render(request, 'backoffice/forgot-password.html')

def backoffice_login(request):
    return render(request, 'backoffice/login.html')

def backoffice_register(request):
    return render(request, 'backoffice/register.html')


# Tables avec tous les blogs
@login_required
def backoffice_tables(request):
    blogs = Blog.objects.all().order_by('-created_at')
    return render(request, 'backoffice/tables.html', {'blogs': blogs})


# Détail d’un blog
@login_required
def backoffice_detail(request, pk):
    blog = get_object_or_404(Blog, pk=pk)
    return render(request, 'backoffice/blog_detail.html', {'blog': blog})


# Création d’un blog
@login_required
def backoffice_create(request):
    if request.method == 'POST':
        form = BlogForm(request.POST)
        if form.is_valid():
            blog = form.save(commit=False)
            blog.author = request.user  # définit l'auteur automatiquement
            blog.save()
            return redirect('dashboard:backoffice_tables')
    else:
        form = BlogForm()
    
    return render(request, 'backoffice/blog_edit.html', {'form': form})


# Modification d’un blog
@login_required
def backoffice_edit(request, pk):
    blog = get_object_or_404(Blog, pk=pk)

    if request.method == 'POST':
        form = BlogForm(request.POST, instance=blog)
        if form.is_valid():
            form.save()
            return redirect('dashboard:backoffice_tables')
    else:
        form = BlogForm(instance=blog)

    return render(request, 'backoffice/blog_edit.html', {
        'blog': blog,
        'form': form,
    })


# Suppression d’un blog
@login_required
def backoffice_delete(request, pk):
    blog = get_object_or_404(Blog, pk=pk)
    if request.method == 'POST':
        blog.delete()
        return redirect('dashboard:backoffice_tables')  # Retour à la liste
    return render(request, 'backoffice/blog_confirm_delete.html', {'blog': blog})



# Ajouter un commentaire depuis le détail du blog
@login_required
def backoffice_comment_create(request, blog_pk):
    blog = get_object_or_404(Blog, pk=blog_pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.blog = blog
            comment.author = request.user  # admin qui crée le commentaire
            comment.save()
            return redirect('dashboard:backoffice_detail', pk=blog.pk)
    else:
        form = CommentForm()
    return render(request, 'backoffice/comment_form.html', {'form': form, 'blog': blog, 'action': 'Ajouter'})

# Modifier un commentaire
@login_required
def backoffice_comment_edit(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('dashboard:backoffice_detail', pk=comment.blog.pk)
    else:
        form = CommentForm(instance=comment)
    return render(request, 'backoffice/comment_form.html', {'form': form, 'blog': comment.blog, 'action': 'Modifier'})

# Supprimer un commentaire
@login_required
def backoffice_comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    blog_pk = comment.blog.pk
    if request.method == 'POST':
        comment.delete()
        return redirect('dashboard:backoffice_detail', pk=blog_pk)
    return render(request, 'backoffice/comment_confirm_delete.html', {'comment': comment})