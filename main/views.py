from django.shortcuts import render, redirect, get_object_or_404
from appointments.models import Appointment, Client, Feedback
from users.models import Coach
from appointments.forms import AppointmentCreateForm, AppointmentUpdateForm, ClientUpdateForm, FeedbackForm
from users.forms import CustomUserUpdateForm
from blogapp.models import Blog
from product.models import Product
from users.models import CustomUser as User, Coach, Nutritionist
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg
from django.db.models.functions import TruncMonth
import json
from datetime import datetime

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
    
    # Initialisation du contexte
    context = {}
    
    # --- 1. Récupération des Blogs ---
    try:
        # On récupère les 3 derniers blogs créés
        blogs = Blog.objects.all().order_by('-created_at')[:3] 
        context['blogs'] = blogs
    except Exception as e:
        print(f"Erreur lors de la récupération des blogs: {e}")
        context['blogs'] = []
    
    # --- 2. Récupération des Produits Vedettes ---
    # Nous utilisons 'price' comme critère de tri, car 'is_featured' n'est pas un champ existant
    try:
        featured_products = Product.objects.all().order_by('price')[:4]
        context['featured_products'] = featured_products
    except Exception as e:
        print(f"Erreur lors de la récupération des produits: {e}")
        context['featured_products'] = []
    
    
    # --- 3. Récupération des Coachs ---
    try:
        # On filtre les utilisateurs qui ont le rôle 'coach'
        coaches = Coach.objects.all().order_by('nom_complet')
        context['coaches'] = coaches
    except Exception as e:
        print(f"Erreur lors de la récupération des coachs: {e}")
        context['coaches'] = []

    
    # --- 4. Récupération des Nutritionnistes ---
    try:
        # On filtre les utilisateurs qui ont le rôle 'nutritionist'
        nutritionists = Nutritionist.objects.all().order_by('nom_complet')
        context['nutritionists'] = nutritionists
    except Exception as e:
        print(f"Erreur lors de la récupération des nutritionnistes: {e}")
        context['nutritionists'] = []
    
    
    # --- 5. Rendre le template ---
    # Le dictionnaire 'context' est maintenant complet
    return render(request, 'main/index.html', context)



def main_page(request):
    return render(request, 'main/main.html')

def single_blog(request):
    return render(request, 'main/single-blog.html')

def trainer_details(request):
    return render(request, 'main/trainer-details.html')

def trainer(request):
    return render(request, 'main/trainer.html')



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
            
            client, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'nom_complet': nom_complet,
                    'num_tel': num_tel,
                    'ville': ville,
                    'role': 'client',
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
            return redirect('main:backoffice_appointments_list')
    else:
        form = AppointmentCreateForm()
    return render(request, 'backoffice/appointment_form.html', {'form': form, 'action': 'Add'})

def backoffice_appointment_update(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    client = appointment.client

    if request.method == 'POST':
        appointment_form = AppointmentUpdateForm(request.POST, instance=appointment)
        client_form = CustomUserUpdateForm(request.POST, instance=client)
        
        if appointment_form.is_valid() and client_form.is_valid():
            appointment_form.save()
            client_form.save()
            return redirect('main:backoffice_appointments_list')
    else:
        appointment_form = AppointmentUpdateForm(instance=appointment)
        client_form = CustomUserUpdateForm(instance=client)
    
    return render(request, 'backoffice/appointment_form.html', {
        'appointment_form': appointment_form,
        'client_form': client_form,
        'appointment': appointment,
        'action': 'Modify'
    })

def backoffice_appointment_delete(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)

    if request.method == 'POST':
        appointment.delete()
        return redirect('main:backoffice_appointments_list')
    return render(request, 'backoffice/appointment_confirm_delete.html', {'appointment': appointment})

def users_list(request):
    users = User.objects.all()
    return render(request, "backoffice/tables_user.html", {"users": users})

def backoffice_tables(request):
    # Pass all nutritionists to the backoffice tables view
    nutritionists = Nutritionist.objects.all()
    return render(request, 'backoffice/tables_nutritionists.html', {'nutritionists': nutritionists})

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.views.decorators.csrf import csrf_protect

def backoffice_calendar(request):
    return render(request, 'backoffice/calendar.html')

def backoffice_dashboard(request):
    # Appointments per month
    appointments_by_month = Appointment.objects.annotate(month=TruncMonth('appointment_date')).values('month').annotate(count=Count('id')).order_by('month')
    month_labels = [a['month'].strftime('%B %Y') for a in appointments_by_month]
    month_data = [a['count'] for a in appointments_by_month]

    # Appointments by city
    appointments_by_city = Appointment.objects.values('client__ville').annotate(count=Count('id')).order_by('-count')
    city_labels = [a['client__ville'] for a in appointments_by_city]
    city_data = [a['count'] for a in appointments_by_city]

    # Appointments by type
    appointments_by_type = Appointment.objects.values('mode').annotate(count=Count('id'))
    type_labels = [a['mode'] for a in appointments_by_type]
    type_data = [a['count'] for a in appointments_by_type]

    # Paid vs Unpaid
    total_paid = Appointment.objects.filter(is_paid=True).count()
    total_unpaid = Appointment.objects.filter(is_paid=False).count()

    # Paid vs Unpaid per month
    paid_monthly = Appointment.objects.filter(is_paid=True).annotate(month=TruncMonth('appointment_date')).values('month').annotate(count=Count('id')).order_by('month')
    unpaid_monthly = Appointment.objects.filter(is_paid=False).annotate(month=TruncMonth('appointment_date')).values('month').annotate(count=Count('id')).order_by('month')

    # Create a dictionary for paid and unpaid counts per month
    paid_dict = {item['month'].strftime('%B %Y'): item['count'] for item in paid_monthly}
    unpaid_dict = {item['month'].strftime('%B %Y'): item['count'] for item in unpaid_monthly}

    # Get all unique months from both paid and unpaid
    all_months = sorted(list(set(paid_dict.keys()) | set(unpaid_dict.keys())), key=lambda x: datetime.strptime(x, '%B %Y'))

    paid_monthly_data = [paid_dict.get(month, 0) for month in all_months]
    unpaid_monthly_data = [unpaid_dict.get(month, 0) for month in all_months]


    context = {
        'month_labels': json.dumps(month_labels),
        'month_data': json.dumps(month_data),
        'city_labels': json.dumps(city_labels),
        'city_data': json.dumps(city_data),
        'type_labels': json.dumps(type_labels),
        'type_data': json.dumps(type_data),
        'total_paid': total_paid,
        'total_unpaid': total_unpaid,
        'paid_monthly_data': json.dumps(paid_monthly_data),
        'unpaid_monthly_data': json.dumps(unpaid_monthly_data),
        'monthly_labels': json.dumps(all_months),
    }

    return render(request, 'backoffice/dashboard.html', context)

def coach_list(request):
    coaches = Coach.objects.filter(show_on_website=True).annotate(avg_rating=Avg('feedback_received__rating'))
    return render(request, 'main/coach_list.html', {'coaches': coaches})

def coach_detail(request, coach_id):
    coach = get_object_or_404(Coach, id=coach_id)
    feedbacks = Feedback.objects.filter(coach=coach).order_by('-created_at')
    latest_feedbacks = feedbacks[:3]
    more_feedbacks = feedbacks.count() > 3
    avg_rating = feedbacks.aggregate(Avg('rating'))['rating__avg']

    can_leave_feedback = False
    feedback_form = None
    if request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == 'client':
        # Check if the logged-in client had an appointment with this coach
        try:
            client_obj = Client.objects.get(email=request.user.email)
            has_appointment = Appointment.objects.filter(client=client_obj, coach_id=coach_id).exists()
            if has_appointment:
                can_leave_feedback = True
                if request.method == 'POST' and 'leave_feedback' in request.POST:
                    feedback_form = FeedbackForm(request.POST)
                    if feedback_form.is_valid():
                        feedback = feedback_form.save(commit=False)
                        feedback.client = request.user
                        feedback.coach = coach
                        feedback.save()
                        messages.success(request, 'Votre avis a été enregistré.')
                        return redirect('coach_detail', coach_id=coach_id)
                else:
                    feedback_form = FeedbackForm()
        except Client.DoesNotExist:
            pass

    return render(request, 'main/coach_detail.html', {
        'coach': coach,
        'latest_feedbacks': latest_feedbacks,
        'more_feedbacks': more_feedbacks,
        'all_feedbacks': feedbacks,
        'avg_rating': avg_rating,
        'can_leave_feedback': can_leave_feedback,
        'feedback_form': feedback_form,
    })
