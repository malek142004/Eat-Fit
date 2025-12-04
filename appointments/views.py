def training_program_detail_view(request, pk):
    training_program = get_object_or_404(TrainingProgram, pk=pk)
    return render(request, 'main/training_program_detail.html', {'training_program': training_program})
import logging
logger = logging.getLogger(__name__)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from datetime import datetime, timedelta, time
from io import BytesIO
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils.dateparse import parse_date, parse_time
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
import random
import string

from .forms import AppointmentCreateForm, AppointmentUpdateForm
from .models import Appointment

from django.shortcuts import render, redirect, get_object_or_404
from django.forms import ValidationError
from .forms import AppointmentCreateForm, AppointmentUpdateForm, ClientUpdateForm, TrainingProgramForm
from .models import Appointment, Client, TrainingProgram

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse, FileResponse
from .models import Feedback
from .serializers import FeedbackSerializer
import weasyprint
import io
from reportlab.pdfgen import canvas

User = get_user_model()

def is_admin(user):
    return user.is_authenticated and user.is_staff

@login_required
def create_appointment_request(request, professional_id=None):
    user = request.user
    if user.role != 'client':
        messages.error(request, "Only clients can create appointments.")
        return redirect("main:index")

    professional = None
    if professional_id:
        professional = User.objects.filter(id=professional_id, role__in=['coach', 'nutritionist']).first()
        if not professional:
            messages.error(request, "The selected professional does not exist or is not a coach/nutritionist.")
            return redirect("main:index") # Redirect to home or a generic appointment page

    if request.method == 'POST':
        form = AppointmentCreateForm(request.POST, user=user, professional=professional) # Pass user and professional to form
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.client = user
            if professional:
                appointment.professional = professional
            appointment.save()
            messages.success(request, "Appointment created successfully!")
            return redirect('appointments:appointment_list')
    else:
        form = AppointmentCreateForm(user=user, professional=professional) # Pass user and professional to form

    return render(request, 'main/addappointment.html', {'form': form, 'professional': professional})


def appointment_list(request):
    appointments = Appointment.objects.filter(client=request.user)
    
    date_query = request.GET.get('date')
    sort_order = request.GET.get('sort')

    if date_query:
        appointments = appointments.filter(appointment_date=date_query)

    if sort_order == 'asc':
        appointments = appointments.order_by('appointment_date', 'start_time')
    else:
        appointments = appointments.order_by('-appointment_date', '-start_time')

    return render(request, 'main/listappointment.html', {
        'appointments': appointments,
        'date_query': date_query,
        'current_sort': sort_order
    })


def appointment_update(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, client=request.user)

    if request.method == 'POST':
        form = AppointmentUpdateForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, "Appointment updated successfully!")
            return redirect('appointments:appointment_list')
    else:
        form = AppointmentUpdateForm(instance=appointment)
    
    return render(request, 'main/modifyappointment.html', {
        'form': form,
        'appointment': appointment,
    })


def appointment_delete(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, client=request.user)
    if request.method == 'POST':
        appointment.delete()
        messages.success(request, "Appointment deleted successfully.")
        return redirect('appointments:appointment_list')
    return render(request, 'main/deleteappointment.html', {'appointment': appointment})


def initiate_payment(request, pk):
    if request.method == 'POST':
        appointment = get_object_or_404(Appointment, pk=pk)
        
        # Generate a 4-digit confirmation code
        confirmation_code = ''.join(random.choices(string.digits, k=4))
        
        # Store the code in the session
        request.session[f'payment_code_{pk}'] = confirmation_code
        
        # Simulate sending email (requires email backend configuration in settings.py)
        subject = 'Eat&Fit - Votre code de confirmation de paiement'
        plain_message = f"""Bonjour {appointment.client.nom_complet},

Votre code de confirmation de paiement pour le rendez-vous du {appointment.appointment_date} à {appointment.start_time} est : {confirmation_code}

Veuillez entrer ce code sur la plateforme pour confirmer votre paiement.

Merci,
L'équipe Eat&Fit"""

        html_message = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
                .header {{ background-color: #f65d5d; color: white; padding: 10px 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ padding: 20px; }}
                .code {{ font-size: 24px; font-weight: bold; color: #f65d5d; text-align: center; margin: 20px 0; padding: 10px; background-color: #f9f9f9; border-radius: 5px; }}
                .footer {{ text-align: center; font-size: 12px; color: #777; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Eat&Fit - Confirmation de Paiement</h2>
                </div>
                <div class="content">
                    <p>Bonjour {appointment.client.nom_complet},</p>
                    <p>Nous avons bien reçu votre demande de paiement pour le rendez-vous suivant :</p>
                    <ul>
                        <li><strong>Date :</strong> {appointment.appointment_date}</li>
                        <li><strong>Heure :</strong> {appointment.start_time}</li>
                    </ul>
                    <p>Veuillez utiliser le code de confirmation ci-dessous pour finaliser votre paiement sur la plateforme :</p>
                    <div class="code">{confirmation_code}</div>
                    <p>Ce code est nécessaire pour confirmer votre transaction.</p>
                    <p>Si vous avez des questions, n'hésitez pas à nous contacter.</p>
                </div>
                <div class="footer">
                    <p>Merci de faire confiance à Eat&Fit.</p>
                    <p>&copy; {datetime.now().year} Eat&Fit. Tous droits réservés.</p>
                </div>
            </div>
        </body>
        </html>
        """
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [appointment.client.email]
        
        try:
            send_mail(subject, plain_message, from_email, recipient_list, fail_silently=False, html_message=html_message)
            return JsonResponse({'status': 'success', 'message': 'Code sent to email.'})
        except Exception as e:
            # If email sending fails, still proceed with the flow for simulation purposes
            # In a real app, you might want to return an error here
            print(f"Error sending email: {e}")
            return JsonResponse({'status': 'success', 'message': 'Code generated (email simulation failed).'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def confirm_payment(request, pk):
    if request.method == 'POST':
        appointment = get_object_or_404(Appointment, pk=pk)
        data = json.loads(request.body)
        entered_code = data.get('code')
        
        stored_code = request.session.get(f'payment_code_{pk}')
        
        if stored_code and entered_code == stored_code:
            appointment.is_paid = True
            appointment.save()
            # Clear the code from session after successful confirmation
            del request.session[f'payment_code_{pk}']
            return JsonResponse({'status': 'success', 'message': 'Appointment successfully paid!'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid confirmation code.'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


def generate_pdf_report(request):
    appointments = Appointment.objects.all()
    
    date_query = request.GET.get('date')
    email_query = request.GET.get('email')
    sort_order = request.GET.get('sort')

    if date_query:
        appointments = appointments.filter(appointment_date=date_query)
    
    if email_query:
        appointments = appointments.filter(client__email__icontains=email_query)

    if sort_order == 'asc':
        appointments = appointments.order_by('appointment_date')
    else:
        appointments = appointments.order_by('-appointment_date')

    template = get_template('reports/appointment_report.html')
    html_content = template.render({'appointments': appointments, 'now': datetime.now()})

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_content.encode("UTF-8")), result)
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="appointments_report.pdf"'
        return response
    
    return HttpResponse("Error Generating PDF", status=500)

def backoffice_appointments_list(request):
    appointments = Appointment.objects.all()
    
    date_query = request.GET.get('date')
    email_query = request.GET.get('email')
    sort_order = request.GET.get('sort')

    if date_query:
        appointments = appointments.filter(appointment_date=date_query)
    
    if email_query:
        appointments = appointments.filter(client__email__icontains=email_query)

    if sort_order == 'asc':
        appointments = appointments.order_by('appointment_date')
    else:
        appointments = appointments.order_by('-appointment_date')

    return render(request, 'backoffice/tables.html', {
        'appointments': appointments,
        'date_query': date_query,
        'email_query': email_query,
        'current_sort': sort_order
    })

def backoffice_appointment_create(request):
    if request.method == 'POST':
        form = AppointmentCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Appointment created successfully!")
            return redirect('appointments:backoffice_appointment_list')
    else:
        form = AppointmentCreateForm()
    return render(request, 'backoffice/appointment_form.html', {'form': form, 'action': 'Add'})

def backoffice_appointment_update(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)

    if request.method == 'POST':
        form = AppointmentUpdateForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, "Appointment updated successfully!")
            return redirect('appointments:backoffice_appointment_list')
    else:
        form = AppointmentUpdateForm(instance=appointment)
    
    return render(request, 'backoffice/appointment_form.html', {
        'form': form,
        'appointment': appointment,
        'action': 'Edit'
    })

def backoffice_appointment_delete(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        appointment.delete()
        messages.success(request, "Appointment deleted successfully!")
        return redirect('appointments:backoffice_appointment_list')
    return render(request, 'backoffice/appointment_confirm_delete.html', {'appointment': appointment})

@csrf_exempt
@csrf_exempt
def api_available_slots(request):
    start_date_str = request.GET.get('start_date')
    if not start_date_str:
        return JsonResponse({'status': 'error', 'message': 'start_date parameter is required.'}, status=400)

    try:
        start_date = parse_date(start_date_str)
        if not start_date:
            raise ValueError("Invalid date format")
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Invalid start_date format. Use YYYY-MM-DD.'}, status=400)

    # Calculate the start and end of the week (Monday to Sunday)
    # Assuming start_date can be any day in the week
    week_start = start_date - timedelta(days=start_date.weekday()) # Monday
    week_end = week_start + timedelta(days=6) # Sunday

    # Define working hours and slot duration
    working_start_time = time(9, 0) # 9 AM
    working_end_time = time(17, 0) # 5 PM
    slot_duration = timedelta(minutes=60) # 1 hour slots

    # Fetch all appointments within the week
    appointments_in_week = Appointment.objects.filter(
        appointment_date__range=[week_start, week_end]
    ).order_by('appointment_date', 'start_time')

    occupied_slots = []
    for app in appointments_in_week:
        # Convert date and time to datetime objects for easier comparison
        app_start_dt = datetime.combine(app.appointment_date, app.start_time)
        app_end_dt = datetime.combine(app.appointment_date, app.end_time)
        occupied_slots.append({'start': app_start_dt, 'end': app_end_dt})

    available_slots = []
    current_day = week_start
    while current_day <= week_end:
        # Start from the beginning of working hours for each day
        current_slot_dt = datetime.combine(current_day, working_start_time)
        while current_slot_dt.time() < working_end_time:
            current_slot_end_dt = current_slot_dt + slot_duration
            
            is_available = True
            for occupied in occupied_slots:
                # Check for overlap
                if not (current_slot_end_dt <= occupied['start'] or current_slot_dt >= occupied['end']):
                    is_available = False
                    break
            
            if is_available:
                available_slots.append({
                    'start': current_slot_dt.isoformat(),
                    'end': current_slot_end_dt.isoformat(),
                    'date': current_day.strftime('%Y-%m-%d'),
                    'time': current_slot_dt.strftime('%H:%M')
                })
            
            current_slot_dt += slot_duration # Increment the datetime object
        current_day += timedelta(days=1)

    return JsonResponse({'status': 'success', 'available_slots': available_slots})


@csrf_exempt
def api_appointments(request, pk=None):
    if request.method == 'GET':
        appointments = Appointment.objects.select_related('client').all()
        events = []
        for appointment in appointments:
            color = ''
            if appointment.status == 'confirmed':
                color = 'green'
            elif appointment.status == 'cancelled':
                color = 'red'
            elif appointment.status == 'pending':
                color = 'yellow'
            elif appointment.status == 'untreated':
                color = 'blue'

            events.append({
                'id': appointment.id,
                'title': f"{appointment.get_mode_display()} {appointment.client.nom_complet}, {appointment.client.ville}",
                'start': f"{appointment.appointment_date}T{appointment.start_time}",
                'end': f"{appointment.appointment_date}T{appointment.end_time}",
                'color': color,
                'extendedProps': {
                    'client_name': appointment.client.nom_complet,
                    'client_email': appointment.client.email,
                    'client_num_tel': appointment.client.num_tel,
                    'client_ville': appointment.client.ville,
                    'mode': appointment.mode,
                    'visio_link': appointment.visio_link,
                    'status': appointment.status,
                }
            })
        return JsonResponse(events, safe=False)

    elif request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('client_email')
        if not email:
            return JsonResponse({'status': 'error', 'message': 'Email is required.'}, status=400)

        client, created = User.objects.get_or_create(
            email=email,
            defaults={
                'nom_complet': data.get('client_name'),
                'num_tel': data.get('client_num_tel'),
                'ville': data.get('client_ville'),
                'role': 'client'
            }
        )
        if created:
            client.set_unusable_password()
            client.save()

        try:
            appointment = Appointment.objects.create(
                client=client,
                appointment_date=parse_date(data.get('date')),
                start_time=parse_time(data.get('start_time')),
                end_time=parse_time(data.get('end_time')),
                mode=data.get('mode'),
                status=data.get('status', 'untreated'),
                visio_link=data.get('visio_link')
            )
            return JsonResponse({'status': 'success', 'id': appointment.id}, status=201)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    elif request.method == 'PUT':
        data = json.loads(request.body)
        appointment_id = data.get('id')
        try:
            appointment = get_object_or_404(Appointment, id=appointment_id)
            client = appointment.client

            # Update client data
            client.nom_complet = data.get('client_name', client.nom_complet)
            client.email = data.get('client_email', client.email)
            client.num_tel = data.get('client_num_tel', client.num_tel)
            client.ville = data.get('client_ville', client.ville)
            client.save()

            # Update appointment data
            appointment.appointment_date = parse_date(data.get('date'))
            appointment.start_time = parse_time(data.get('start_time'))
            appointment.end_time = parse_time(data.get('end_time'))
            appointment.mode = data.get('mode')
            appointment.status = data.get('status', 'untreated')
            appointment.visio_link = data.get('visio_link')
            appointment.save()

            return JsonResponse({'status': 'success', 'id': appointment.id})
        except Appointment.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Appointment not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    elif request.method == 'DELETE':
        data = json.loads(request.body)
        appointment_id = data.get('id')
        try:
            appointment = get_object_or_404(Appointment, id=appointment_id)
            appointment.delete()
            return JsonResponse({'status': 'success', 'message': 'Appointment deleted successfully!'})
        except Appointment.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Appointment not found'}, status=404)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

class GenerateTrainingPDFView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        training_program_id = request.data.get('training_program_id')
        try:
            training_program = TrainingProgram.objects.get(id=training_program_id, user=request.user)
        except TrainingProgram.DoesNotExist:
            return Response({'error': 'Training program not found or access denied.'}, status=404)

        # Generate PDF content
        html_content = f"""
        <html>
        <head><title>{training_program.title}</title></head>
        <body>
            <h1>{training_program.title}</h1>
            <p>{training_program.description}</p>
            <p>Created at: {training_program.created_at}</p>
        </body>
        </html>
        """
        pdf_file = weasyprint.HTML(string=html_content).write_pdf()

        # Return PDF as response
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{training_program.title}.pdf"'
        return response

from rest_framework import generics, permissions

class FeedbackListCreateView(generics.ListCreateAPIView):
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Feedback.objects.filter(coach=self.kwargs['coach_id'])

    def perform_create(self, serializer):
        # Allow any authenticated client to leave feedback for a coach
        serializer.save(client=self.request.user)

class FeedbackDeleteView(generics.DestroyAPIView):
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Feedback.objects.filter(client=self.request.user)

def training_programs_view(request):
    training_programs = TrainingProgram.objects.all()
    return render(request, 'main/training_programs.html', {'training_programs': training_programs})

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import Feedback

def feedback_view(request, coach_id):
    coach = get_object_or_404(get_user_model(), id=coach_id)
    feedback_list = Feedback.objects.filter(coach=coach)
    return render(request, 'feedback.html', {'feedback_list': feedback_list, 'coach_id': coach_id})

def coach_detail_view(request, coach_id):
    coach = get_object_or_404(get_user_model(), id=coach_id)
    feedbacks = Feedback.objects.filter(coach=coach).order_by('-created_at')
    can_leave_feedback = True  # Always allow feedback for testing

    if request.method == 'POST' and 'leave_feedback' in request.POST and can_leave_feedback:
        rating = int(request.POST.get('rating', 0))
        comment = request.POST.get('comment', '')
        Feedback.objects.create(
            coach=coach,
            client=request.user,
            rating=rating,
            comment=comment
        )
        return redirect('appointments:coach_detail', coach_id=coach_id)

    avg_rating = feedbacks.aggregate_avg('rating') if feedbacks.exists() else None
    latest_feedbacks = feedbacks[:3]
    more_feedbacks = feedbacks.count() > 3
    all_feedbacks = feedbacks

    return render(request, 'main/coach_detail.html', {
        'coach': coach,
        'all_feedbacks': all_feedbacks,
        'latest_feedbacks': latest_feedbacks,
        'more_feedbacks': more_feedbacks,
        'avg_rating': avg_rating,
        'can_leave_feedback': can_leave_feedback,
    })

from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.urls import reverse_lazy

class TrainingProgramCreateView(CreateView):
    model = TrainingProgram
    form_class = TrainingProgramForm
    template_name = 'main/training_program_form.html'
    success_url = reverse_lazy('appointments:training_program_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class TrainingProgramUpdateView(UpdateView):
    model = TrainingProgram
    form_class = TrainingProgramForm
    template_name = 'main/training_program_form.html'
    success_url = reverse_lazy('appointments:training_program_list')

class TrainingProgramDeleteView(DeleteView):
    model = TrainingProgram
    template_name = 'main/training_program_confirm_delete.html'
    success_url = reverse_lazy('appointments:training_program_list')

class TrainingProgramListView(ListView):
    model = TrainingProgram
    template_name = 'main/training_program_list.html'

    def get_queryset(self):
        queryset = TrainingProgram.objects.filter(user=self.request.user)
        logger.debug(f"Training programs for user {self.request.user}: {queryset}")
        return queryset

def generate_training_program_pdf(request, pk):
    training_program = get_object_or_404(TrainingProgram, pk=pk)

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import cm

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"<b>Training Program:</b> {training_program.name}", styles['Title']))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"<b>Price:</b> ${training_program.price}", styles['Normal']))
    story.append(Paragraph(f"<b>Level:</b> {training_program.get_level_display()}", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("<b>Description:</b>", styles['Heading2']))
    story.append(Paragraph(training_program.description.replace('\n', '<br/>'), styles['BodyText']))

    doc.build(story)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"{training_program.name}.pdf")

def coach_training_programs_view(request, coach_id):
    coach = get_object_or_404(get_user_model(), id=coach_id)
    training_programs = TrainingProgram.objects.filter(user=coach)
    return render(request, 'main/coach_training_programs.html', {
        'training_programs': training_programs,
        'coach': coach
    })
