# products/views.py
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product
from .forms import ProductForm
from django.db.models import Q
from .models import Product, Rating
from .forms import RatingForm
def product_list(request):
    query = request.GET.get('search', '')
    products = Product.objects.all()
    if query:
        products = products.filter(product_name__icontains=query)
    return render(request, 'products/product_list.html', {'products': products})

def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'products/product_form.html', {'form': form})

def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'products/product_form.html', {'form': form})

def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect('product_list')


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    similar_products = Product.objects.filter(
        Q(category=product.category) | Q(business_owner=product.business_owner)
    ).exclude(pk=product.pk)[:3]

    form = None
    if request.user.is_authenticated:
        # Gestion du POST
        if request.method == 'POST':
            form = RatingForm(request.POST)
            if form.is_valid():
                Rating.objects.update_or_create(
                    product=product,
                    user=request.user,
                    defaults={
                        'rating': form.cleaned_data['rating'],
                        'comment': form.cleaned_data['comment']
                    }
                )
                return redirect('product_detail', pk=pk)
        else:
            # Préremplir le rating si existant
            try:
                user_rating = Rating.objects.get(product=product, user=request.user)
                form = RatingForm(instance=user_rating)
            except Rating.DoesNotExist:
                form = RatingForm()

    return render(request, 'products/product_detail.html', {
        'product': product,
        'similar_products': similar_products,
        'form': form
    })
