from django.shortcuts import render, redirect, get_object_or_404
from appointments.models import Appointment, Client
from appointments.forms import AppointmentCreateForm, AppointmentUpdateForm, ClientUpdateForm

def about(request):
    return render(request, 'main/about.html')

def blog(request):
    return render(request, 'main/blog.html')

def classes_details(request):
    return render(request, 'main/classes-details.html')

def classes(request):
    return render(request, 'main/classes.html')

def contact(request):
    return render(request, 'main/contact.html')

def event_details(request):
    return render(request, 'main/event-details.html')

def events(request):
    return render(request, 'main/events.html')

def index(request):
    return render(request, 'main/index.html')

def main_page(request):
    return render(request, 'main/main.html')

def single_blog(request):
    return render(request, 'main/single-blog.html')

def trainer_details(request):
    return render(request, 'main/trainer-details.html')

def trainer(request):
    return render(request, 'main/trainer.html')

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

from django.shortcuts import render, redirect, get_object_or_404
from appointments.models import Appointment, Client
from appointments.forms import AppointmentCreateForm, AppointmentUpdateForm, ClientUpdateForm

# ... existing views ...

# Backoffice Appointment CRUD
def backoffice_appointments_list(request):
    appointments = Appointment.objects.all().order_by('-appointment_date')
    return render(request, 'backoffice/tables.html', {'appointments': appointments})

def backoffice_appointment_create(request):
    if request.method == 'POST':
        form = AppointmentCreateForm(request.POST)
        if form.is_valid():
            nom_complet = form.cleaned_data['nom_complet']
            email = form.cleaned_data['email']
            num_tel = form.cleaned_data['num_tel']
            ville = form.cleaned_data['ville']
            
            client, created = Client.objects.get_or_create(
                email=email,
                defaults={
                    'nom_complet': nom_complet,
                    'num_tel': num_tel,
                    'ville': ville,
                }
            )
            if not created and client.nom_complet != nom_complet:
                client.nom_complet = nom_complet
                client.num_tel = num_tel
                client.ville = ville
                client.save()

            appointment = form.save(commit=False)
            appointment.client = client
            appointment.save()
            return redirect('backoffice_appointments_list')
    else:
        form = AppointmentCreateForm()
    return render(request, 'backoffice/appointment_form.html', {'form': form, 'action': 'Add'})

def backoffice_appointment_update(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    client = appointment.client

    if request.method == 'POST':
        appointment_form = AppointmentUpdateForm(request.POST, instance=appointment)
        client_form = ClientUpdateForm(request.POST, instance=client)
        
        if appointment_form.is_valid() and client_form.is_valid():
            appointment_form.save()
            client_form.save()
            return redirect('backoffice_appointments_list')
    else:
        appointment_form = AppointmentUpdateForm(instance=appointment)
        client_form = ClientUpdateForm(instance=client)
    
    return render(request, 'backoffice/appointment_form.html', {
        'appointment_form': appointment_form,
        'client_form': client_form,
        'appointment': appointment,
        'action': 'Modify'
    })

def backoffice_appointment_delete(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    client = appointment.client

    if request.method == 'POST':
        appointment.delete()
        if not client.appointments.exists():
            client.delete()
        return redirect('backoffice_appointments_list')
    return render(request, 'backoffice/appointment_confirm_delete.html', {'appointment': appointment})

def users_list(request):
    users = User.objects.all()
    return render(request, "backoffice/tables_user.html", {"users": users})

def backoffice_tables(request):
    # Pass all nutritionists to the backoffice tables view
    nutritionists = Nutritionist.objects.all()
    return render(request, 'backoffice/tables_nutritionists.html', {'nutritionists': nutritionists})
