from django.shortcuts import render, redirect, get_object_or_404
from businessowner.models import BusinessOwner
from businessowner.forms import BusinessOwnerForm
from product.models import Product
from product.forms import ProductForm
from django.db.models import Avg
# Create your views here.

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

def backoffice_tables(request):
    return render(request, 'backoffice/tables.html')


def backoffice_manage_businessowners(request):
    owners = BusinessOwner.objects.all()
    return render(request, 'backoffice/manage_businessowners.html', {'owners': owners})


def backoffice_add_businessowner(request):
    if request.method == 'POST':
        form = BusinessOwnerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('manage_businessowners')
    else:
        form = BusinessOwnerForm()
    
    return render(request, 'backoffice/form_businessowner.html', {'form': form, 'title': 'Add Business Owner'})


def backoffice_edit_businessowner(request, owner_id):
    owner = get_object_or_404(BusinessOwner, id=owner_id)

    if request.method == 'POST':
        form = BusinessOwnerForm(request.POST, request.FILES, instance=owner)
        if form.is_valid():
            form.save()
            return redirect('manage_businessowners')
    else:
        form = BusinessOwnerForm(instance=owner)

    return render(request, 'backoffice/form_businessowner.html', {'form': form, 'title': 'Edit Business Owner'})


def backoffice_delete_businessowner(request, owner_id):
    owner = get_object_or_404(BusinessOwner, id=owner_id)
    owner.delete()
    return redirect('manage_businessowners')

def backoffice_manage_products(request):
    products = Product.objects.all().annotate(avg_rating=Avg("ratings__rating"))
    return render(request, 'backoffice/manage_products.html', {'products': products})


def backoffice_add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('backoffice_manage_products')
    else:
        form = ProductForm()

    return render(request, 'backoffice/form_product.html', {
        'form': form,
        'title': 'Add Product'
    })


def backoffice_edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('backoffice_manage_products')
    else:
        form = ProductForm(instance=product)

    return render(request, 'backoffice/form_product.html', {
        'form': form,
        'title': 'Edit Product'
    })


def backoffice_delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return redirect('backoffice_manage_products')


def backoffice_product_details(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    ratings = product.ratings.all()
    return render(request, 'backoffice/product_details.html', {
        'product': product,
        'ratings': ratings
    })