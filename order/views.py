from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from cart.models import Cart
from .models import Order, OrderItem

@login_required
def create_order(request):
    cart, created = Cart.objects.get_or_create(user=request.user)

    if cart.items.count() == 0:
        return redirect('cart_detail')

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        notes = request.POST.get("notes")

        order = Order.objects.create(
            customer=request.user,
            full_name=full_name,
            phone=phone,
            address=address,
            notes=notes
        )

        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                business_owner=item.product.business_owner,
                quantity=item.quantity,
                price=item.product.price
            )

        cart.items.all().delete()

        return render(request, "order/checkout.html", {
            "cart": cart,
            "success": True,
            "order_id": order.id
        })

    return render(request, "order/checkout.html", {"cart": cart})
