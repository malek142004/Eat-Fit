from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from order.models import Order, OrderItem
from product.models import Product
from .models import Cart, CartItem
# Create your views here.

@login_required
def add_to_cart(request, product_id):
    # Business owners cannot buy anything
    if request.user.role == "business_owner":
        return redirect('product_detail', pk=product_id)

    product = get_object_or_404(Product, pk=product_id)

    cart, created = Cart.objects.get_or_create(user=request.user)

    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
    item.save()

    return redirect('cart_detail')


@login_required
def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, "cart/cart_detail.html", {"cart": cart})


@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    if item.cart.user == request.user:
        item.delete()
    return redirect('cart_detail')


@login_required
def checkout(request):
    cart, created = Cart.objects.get_or_create(user=request.user)

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        notes = request.POST.get("notes")

        # Create order
        order = Order.objects.create(
            customer=request.user,
            full_name=full_name,
            phone=phone,
            address=address,
            notes=notes
        )

        # Move Cart items -> Order items
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                business_owner=item.product.business_owner,
                quantity=item.quantity,
                price=item.product.price
            )

        # Empty the cart
        cart.items.all().delete()
        return render(request, "cart/checkout.html", {
            "cart": cart,
            "success": True,
            "order_id": order.id
        })


    return render(request, "cart/checkout.html", {"cart": cart})
