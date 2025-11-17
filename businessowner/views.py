from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import BusinessOwnerForm
from .models import BusinessOwner
# Create your views here.


@login_required
def create_or_edit_business(request):
    # Vérifie que l'utilisateur est bien business owner
    if request.user.role != 'business_owner':
        return redirect('index')

    # Vérifie si le business existe déjà
    try:
        business = request.user.businessowner
        form = BusinessOwnerForm(instance=business)
    except BusinessOwner.DoesNotExist:
        business = None
        form = BusinessOwnerForm()

    if request.method == "POST":
        form = BusinessOwnerForm(request.POST, request.FILES, instance=business)
        if form.is_valid():
            new_business = form.save(commit=False)
            new_business.user = request.user
            new_business.save()
            # Redirect to the correct URL name
            return redirect('product_list')

    return render(request, 'businessowner/businessowner.html', {'form': form})
