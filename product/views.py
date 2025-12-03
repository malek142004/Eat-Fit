# main/products/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q

from users.models import BusinessOwner
from .models import Product, Rating
from .forms import ProductForm, RatingForm


def product_list(request):
    products = Product.objects.all()

    # BUSINESS OWNER VIEW → show only his products
    if request.user.is_authenticated and request.user.role == 'business_owner':
        try:
            owner = request.user.businessowner
            products = products.filter(business_owner=owner)
        except BusinessOwner.DoesNotExist:
            products = Product.objects.none()

    # ----- Filters -----
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    business = request.GET.get('business', '')
    sort = request.GET.get('sort', '')

    if search:
        products = products.filter(product_name__icontains=search)

    if category:
        products = products.filter(category=category)

    if business and not (request.user.is_authenticated and request.user.role == 'business_owner'):
        products = products.filter(business_owner_id=business)

    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')

    # Dropdowns
    categories = [c[0] for c in Product.CATEGORY_CHOICES]
    businesses = BusinessOwner.objects.all()

    return render(request, 'main/products/product_list.html', {
        'products': products,
        'categories': categories,
        'businesses': businesses,
        'request': request  # pour garder search/filters dans le template
    })


def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            if request.user.role == 'business_owner':
                product.business_owner = request.user.businessowner
            product.save()
            return redirect('product:product_list')
    else:
        form = ProductForm()
    return render(request, 'main/products/product_form.html', {'form': form})


def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product:product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'main/products/product_form.html', {'form': form})


def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect('product:product_list')


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    similar_products = Product.objects.filter(
        Q(category=product.category) | Q(business_owner=product.business_owner)
    ).exclude(pk=product.pk)[:3]

    form = None
    if request.user.is_authenticated:
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
                return redirect('product:product_detail', pk=pk)
        else:
            try:
                user_rating = Rating.objects.get(product=product, user=request.user)
                form = RatingForm(instance=user_rating)
            except Rating.DoesNotExist:
                form = RatingForm()

    return render(request, 'main/products/product_detail.html', {
        'product': product,
        'similar_products': similar_products,
        'form': form
    })
