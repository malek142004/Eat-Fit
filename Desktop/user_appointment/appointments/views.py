
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import ValidationError
from .forms import AppointmentCreateForm, AppointmentUpdateForm, ClientUpdateForm
from .models import Appointment, Client

from django.contrib.auth.decorators import login_required
from django.contrib import messages


@login_required
def create_appointment_request(request):
    user = request.user  # utilisateur connecté

    # 🔒 Vérifier si rôle autorisé
    if user.role not in ["client", "admin"]:
        messages.error(request, "Vous n'avez pas l'autorisation de créer un rendez-vous.")
        return redirect("main:index")

    # Pré-remplir le formulaire avec les infos utilisateur
    initial_data = {
        "nom_complet": user.nom_complet,
        "email": user.email,
        "num_tel": user.num_tel,
        "ville": user.ville,
    }

    if request.method == 'POST':
        form = AppointmentCreateForm(request.POST)
        if form.is_valid():
            nom_complet = form.cleaned_data['nom_complet']
            email = form.cleaned_data['email']
            num_tel = form.cleaned_data['num_tel']
            ville = form.cleaned_data['ville']
            
            # Check if client exists
            client, created = Client.objects.get_or_create(
                email=email,
                defaults={
                    'nom_complet': nom_complet,
                    'num_tel': num_tel,
                    'ville': ville,
                }
            )

            # If client exists → update fields if needed
            if not created:
                updated = False
                if client.nom_complet != nom_complet:
                    client.nom_complet = nom_complet
                    updated = True
                if client.num_tel != num_tel:
                    client.num_tel = num_tel
                    updated = True
                if client.ville != ville:
                    client.ville = ville
                    updated = True
                
                if updated:
                    client.save()

            # Create the appointment
            appointment = form.save(commit=False)
            appointment.client = client
            appointment.save()

            return redirect('appointment_list')

    else:
        # Formulaire pré-rempli pour GET
        form = AppointmentCreateForm(initial=initial_data)

    return render(request, 'main/addappointment.html', {'form': form})

# Read
def appointment_list(request):
    appointments = Appointment.objects.all().order_by('-appointment_date')
    return render(request, 'main/listappointment.html', {'appointments': appointments})

# Update
def appointment_update(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    client = appointment.client # Get the associated client

    if request.method == 'POST':
        appointment_form = AppointmentUpdateForm(request.POST, instance=appointment)
        client_form = ClientUpdateForm(request.POST, instance=client)
        
        if appointment_form.is_valid() and client_form.is_valid():
            appointment_form.save()
            client_form.save()
            return redirect('appointment_list')
    else:
        appointment_form = AppointmentUpdateForm(instance=appointment)
        client_form = ClientUpdateForm(instance=client)
    
    return render(request, 'main/modifyappointment.html', {
        'appointment_form': appointment_form,
        'client_form': client_form,
        'appointment': appointment, # Pass appointment object for context if needed
    })

# Delete
def appointment_delete(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    client = appointment.client # Get the associated client

    if request.method == 'POST':
        appointment.delete()
        
        # Check if this was the last appointment for the client
        if not client.appointments.exists():
            client.delete() # Delete the client if no more appointments

        return redirect('appointment_list')
    return render(request, 'main/deleteappointment.html', {'appointment': appointment})
