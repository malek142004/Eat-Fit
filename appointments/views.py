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

from .forms import AppointmentCreateForm, AppointmentUpdateForm, ClientUpdateForm, TrainingProgramForm, ManualPredictionFeaturesForm
from .models import Appointment, Client, TrainingProgram
from .models import Appointment, Client, TrainingProgram, Wallet, Coupon
import joblib
import numpy as np
import os

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
import io
from reportlab.pdfgen import canvas
import uuid
import openai
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import transaction
from django.views.decorators.http import require_http_methods

User = get_user_model()

def is_admin(user):
    return user.is_authenticated and user.is_staff

@login_required
def create_appointment_request(request, professional_id=None):
    user = request.user
    # Allow only clients or admins (staff) to create appointments
    if not (user.role == 'client' or user.is_staff):
        messages.error(request, "Only clients or admins can create appointments.")
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

    # Wallet points (for current user)
    wallet_points = 0
    if request.user.is_authenticated:
        try:
            wallet_points = request.user.wallet.points
        except Wallet.DoesNotExist:
            wallet_points = 0

    return render(request, 'main/listappointment.html', {
        'appointments': appointments,
        'date_query': date_query,
        'current_sort': sort_order,
        'wallet_points': wallet_points,
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


@require_POST
def quiz_generate(request):
    """Generate a quiz (uses OpenAI if key provided); returns questions and stores answers in session.
    Ensures questions match the requested difficulty; falls back to a per-difficulty local bank on mismatch."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        payload = json.loads(request.body)
    except Exception:
        payload = {}

    theme = payload.get('theme', 'sport')
    # normalize theme keys (e.g., 'healthy lifestyle' -> 'healthylifestyle')
    if isinstance(theme, str):
        theme = theme.replace(' ', '').lower()
    difficulty = payload.get('difficulty', 'easy')
    num_questions = int(payload.get('num_questions', 5))

    # Local per-difficulty bank
    bank = {
        'sport': {
            'easy': [
                { 'question': 'Quel sport utilise un ballon ovale?', 'choices': ['Football', 'Rugby', 'Basketball', 'Tennis'], 'correct_index': 1 },
                { 'question': 'Quel sport a des paniers?', 'choices': ['Tennis', 'Basketball', 'Handball', 'Football'], 'correct_index': 1 },
                { 'question': 'Quel sport se joue en double sur gazon?', 'choices': ['Tennis', 'Natation', 'Boxe', 'Rugby'], 'correct_index': 0 },
            ],
            'medium': [
                { 'question': 'Combien de joueurs par équipe en football?', 'choices': ['9', '10', '11', '12'], 'correct_index': 2 },
                { 'question': 'Combien de temps dure un match de basket NBA (minutes)?', 'choices': ['40', '48', '60', '90'], 'correct_index': 1 },
                { 'question': 'Quel est le score maximum possible pour un set de tennis sans tie-break?', 'choices': ['6-0', '10-8', '7-5', '8-6'], 'correct_index': 2 },
            ],
            'hard': [
                { 'question': 'Quel pays a remporté la première coupe du monde de football (FIFA)?', 'choices': ['France', 'Uruguay', 'Brésil', 'Angleterre'], 'correct_index': 1 },
                { 'question': 'Quelle est la distance d\'un marathon officiel en kilomètres?', 'choices': ['42.195', '40', '50', '45.5'], 'correct_index': 0 },
                { 'question': 'Combien de joueurs composent une équipe de rugby à XV?', 'choices': ['13', '15', '11', '14'], 'correct_index': 1 },
            ]
        },
        'healthylifestyle': {
            'easy': [
                { 'question': 'Quel aliment est une bonne source de fibres?', 'choices': ['Pain blanc', 'Lentilles', 'Beurre', 'Sucre'], 'correct_index': 1 },
                { 'question': 'Combien de portions de légumes est-il recommandé de manger par jour?', 'choices': ['0-1', '1-2', '3-5', '6+'], 'correct_index': 2 },
                { 'question': 'Quelle boisson est la meilleure pour l\'hydratation quotidienne?', 'choices': ['Soda', 'Jus industriel', 'Eau', 'Boisson énergétique'], 'correct_index': 2 },
            ],
            'medium': [
                { 'question': 'Quel conseil favorise un bon petit-déjeuner équilibré?', 'choices': ['Sauter le petit-déjeuner', 'Mélanger protéines et glucides', 'Boire seulement du café', 'Manger uniquement des sucreries'], 'correct_index': 1 },
                { 'question': 'Que signifie "aliments transformés"?', 'choices': ['Aliments préparés à partir de produits bruts', 'Aliments 100% naturels', 'Aliments sans calories', 'Aliments uniquement végétariens'], 'correct_index': 0 },
                { 'question': 'Comment réduire l\'apport en sucre ajouté?', 'choices': ['Éviter boissons sucrées', 'Manger plus de gâteaux', 'Ajouter du sirop', 'Boire uniquement des jus'], 'correct_index': 0 },
            ],
            'hard': [
                { 'question': 'Quelle stratégie est utile pour contrôler les portions?', 'choices': ['Utiliser une assiette plus petite', 'Manger plus rapidement', 'Ignorer la faim', 'Remplir l\'assiette de desserts'], 'correct_index': 0 },
                { 'question': 'Quel nutriment est important pour la santé des os?', 'choices': ['Vitamine C', 'Calcium', 'Glucose', 'Nicotine'], 'correct_index': 1 },
                { 'question': 'Quel est l\'effet d\'un excès d\'aliments ultra-transformés sur la santé?', 'choices': ['Améliore la santé', 'Augmente le risque de maladies chroniques', 'N\'a aucun effet', 'Diminue l\'appétit'], 'correct_index': 1 },
            ]
        }
    }

    questions = []

    # Try to use OpenAI if available
    if settings.OPENAI_API_KEY:
        try:
            openai.api_key = settings.OPENAI_API_KEY
            prompt = (
                f"Generate {num_questions} multiple-choice questions about {theme} strictly at {difficulty} difficulty. "
                f"Return a JSON array where each item has: question (string), choices (list of 4 strings), correct_index (0-3), difficulty (one of easy|medium|hard). Do NOT include any other text."
            )
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a quiz generator."},
                          {"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=800,
            )
            text = response.choices[0].message.content.strip()
            import re
            m = re.search(r"\[", text)
            if m:
                import json as _json
                parsed = _json.loads(text[text.find('['):])
                valid = True
                for i, q in enumerate(parsed):
                    qdiff = q.get('difficulty', '').lower() if q.get('difficulty') else ''
                    if qdiff != difficulty:
                        valid = False
                        break
                    questions.append({
                        'id': i+1,
                        'question': q.get('question'),
                        'choices': q.get('choices'),
                        'correct_index': int(q.get('correct_index'))
                    })
                if not valid:
                    questions = []
        except Exception:
            questions = []

    # Fallback to local bank per requested difficulty
    if not questions:
        chosen_list = bank.get(theme, bank['sport']).get(difficulty, [])
        for i, q in enumerate(chosen_list[:num_questions]):
            questions.append({'id': i+1, 'question': q['question'], 'choices': q['choices'], 'correct_index': q['correct_index']})

    quiz_id = str(uuid.uuid4())
    # Store authoritative answers in session
    sess_quiz = {'id': quiz_id, 'difficulty': difficulty, 'questions': {str(q['id']): q['correct_index'] for q in questions}}
    request.session['quiz'] = sess_quiz
    request.session.modified = True

    # Remove correct_index when returning to client
    client_questions = [{'id': q['id'], 'question': q['question'], 'choices': q['choices']} for q in questions]

    return JsonResponse({'quiz_id': quiz_id, 'questions': client_questions})


@require_POST
def quiz_submit(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        payload = json.loads(request.body)
    except Exception:
        payload = {}

    answers = payload.get('answers', [])
    correct_map = request.session.get('quiz', {}).get('questions', {})
    correct_count = 0
    total = len(correct_map)
    for ans in answers:
        qid = str(ans.get('id'))
        sel = int(ans.get('answer_index'))
        if qid in correct_map and int(correct_map[qid]) == sel:
            correct_count += 1

    difficulty = request.session.get('quiz', {}).get('difficulty', 'easy')
    per = {'easy': 10, 'medium': 20, 'hard': 30}.get(difficulty, 10)
    points_awarded = correct_count * per

    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    wallet.points += points_awarded
    wallet.save()

    # Clear quiz from session
    try:
        del request.session['quiz']
    except KeyError:
        pass

    return JsonResponse({'correct': correct_count, 'total': total, 'points_awarded': points_awarded, 'new_balance': wallet.points})


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

@login_required
def backoffice_appointments_list(request):
    # Accessible to any logged-in user (no automatic redirect to login for already-authenticated users)
    # --- Appointment List Logic ---
    # Use Subquery to annotate wallet points directly on the queryset to avoid inconsistencies and N+1 queries
    from django.db.models import OuterRef, Subquery, IntegerField, Value
    from django.db.models.functions import Coalesce
    from .models import Wallet

    wallet_points_subq = Wallet.objects.filter(user=OuterRef('client')).values('points')[:1]

    # Annotate wallet points at the DB level and ensure fallback to 0 using Coalesce.
    appointments = (
        Appointment.objects
        .select_related('client', 'professional')
        .prefetch_related('client__coupons', 'client__wallet')
        .annotate(wallet_points=Coalesce(Subquery(wallet_points_subq, output_field=IntegerField()), Value(0), output_field=IntegerField()))
    )

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

    # wallet_points is now guaranteed to be an integer (0 when no Wallet exists)

    context = {
        'appointments': appointments,
        'date_query': date_query,
        'email_query': email_query,
        'current_sort': sort_order,
    }
    return render(request, 'backoffice/tables.html', context)

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


def predict_manual_features_view(request, appointment_id):
    # Accessible without login requirement for prediction flow
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    form = ManualPredictionFeaturesForm()
    context = {
        'form': form,
        'appointment': appointment,
    }
    return render(request, 'backoffice/manual_features_form.html', context)


def prediction_result_view(request, appointment_id):
    # Accessible without login requirement for prediction flow
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    client = appointment.client

    if request.method != 'POST':
        return redirect('appointments:backoffice_predict_manual', appointment_id=appointment.id)

    form = ManualPredictionFeaturesForm(request.POST)
    if form.is_valid():
        manual_data = form.cleaned_data
        age = manual_data['age']
        gender = int(manual_data['gender'])

        # --- Calculate/Define Features ---
        sms_received = 1  # Assume SMS was sent
        date_diff = (appointment.appointment_date - appointment.created_at.date()).days
        appointment_weekday = appointment.appointment_date.weekday()  # Monday=0, Sunday=6
        is_weekend = 1 if appointment_weekday >= 5 else 0

        features = [
            float(client.id),
            float(appointment.id),
            float(gender),
            float(age),
            float(sms_received),
            float(date_diff),
            float(appointment_weekday),
            float(is_weekend)
        ]

        prediction_result = None
        prediction_action = "Aucune action."

        try:
            scaler_path = os.path.join(settings.BASE_DIR, 'appointments', 'scaler.pkl')
            model_path = os.path.join(settings.BASE_DIR, 'appointments', 'no_show_model.pkl')

            # Fallback to .joblib if .pkl not found
            try:
                scaler = joblib.load(scaler_path)
            except FileNotFoundError:
                scaler_path_alt = os.path.join(settings.BASE_DIR, 'appointments', 'scaler.joblib')
                scaler = joblib.load(scaler_path_alt)

            try:
                model = joblib.load(model_path)
            except FileNotFoundError:
                model_path_alt = os.path.join(settings.BASE_DIR, 'appointments', 'no_show_model.joblib')
                model = joblib.load(model_path_alt)

            X = np.array(features).reshape(1, -1)
            X_scaled = scaler.transform(X)

            proba_no_show = model.predict_proba(X_scaled)[0][1]
            prediction_result = round(float(proba_no_show) * 100, 2)

            if proba_no_show >= 0.7:
                prediction_action = "Action forte : Appeler le client et envoyer un rappel par e-mail."
            elif proba_no_show >= 0.4:
                prediction_action = "Action suggérée : Envoyer un rappel par SMS."
            else:
                prediction_action = "Aucune action requise."

        except FileNotFoundError:
            messages.error(request, "Erreur : Le fichier du modèle de prédiction (scaler.pkl ou no_show_model.pkl) est introuvable.")
        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de la prédiction : {e}")

        context = {
            'appointment': appointment,
            'prediction_result': prediction_result,
            'prediction_action': prediction_action,
        }
        return render(request, 'backoffice/prediction_result.html', context)
    else:
        # If form is not valid, redirect back to the manual form page
        messages.error(request, "Données invalides. Veuillez vérifier l'âge et le genre.")
        return redirect('appointments:backoffice_predict_manual', appointment_id=appointment.id)


def send_prediction_email(request, appointment_id):
    # Accessible without login requirement for prediction flow
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    if request.method == 'POST':
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        recipient_email = appointment.client.email

        if not subject or not message:
            messages.error(request, "Le sujet et le message ne peuvent pas être vides.")
            return redirect('appointments:backoffice_prediction_result', appointment_id=appointment.id)

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [recipient_email],
                fail_silently=False,
            )
            messages.success(request, f"Email envoyé avec succès à {recipient_email}.")
        except Exception as e:
            messages.error(request, f"Erreur lors de l'envoi de l'email : {e}")

        return redirect('appointments:backoffice_appointment_list')

    # Redirect if not a POST request
    return redirect('appointments:backoffice_prediction_result', appointment_id=appointment.id)


def quick_predict_view(request, appointment_id):
    """Compute prediction with sensible defaults (no manual input) and render result."""
    # Accessible without login requirement for prediction flow

    appointment = get_object_or_404(Appointment, pk=appointment_id)
    client = appointment.client

    # Defaults: if actual data available, use them; otherwise fallback
    default_age = 30
    default_gender = 1  # 1 = male, 0 = female (consistent with usage elsewhere)

    # --- Calculate/Define Features (same as in prediction_result_view) ---
    try:
        sms_received = 1  # Assume SMS was sent
        date_diff = (appointment.appointment_date - appointment.created_at.date()).days
        appointment_weekday = appointment.appointment_date.weekday()
        is_weekend = 1 if appointment_weekday >= 5 else 0

        features = [
            float(client.id),
            float(appointment.id),
            float(default_gender),
            float(default_age),
            float(sms_received),
            float(date_diff),
            float(appointment_weekday),
            float(is_weekend)
        ]

        prediction_result = None
        prediction_action = "Aucune action."

        scaler_path = os.path.join(settings.BASE_DIR, 'appointments', 'scaler.pkl')
        model_path = os.path.join(settings.BASE_DIR, 'appointments', 'no_show_model.pkl')

        # Fallback to .joblib if .pkl not found
        try:
            scaler = joblib.load(scaler_path)
        except FileNotFoundError:
            scaler_path_alt = os.path.join(settings.BASE_DIR, 'appointments', 'scaler.joblib')
            scaler = joblib.load(scaler_path_alt)

        try:
            model = joblib.load(model_path)
        except FileNotFoundError:
            model_path_alt = os.path.join(settings.BASE_DIR, 'appointments', 'no_show_model.joblib')
            model = joblib.load(model_path_alt)

        X = np.array(features).reshape(1, -1)
        X_scaled = scaler.transform(X)

        proba_no_show = model.predict_proba(X_scaled)[0][1]
        prediction_result = round(float(proba_no_show) * 100, 2)

        if proba_no_show >= 0.7:
            prediction_action = "Action forte : Appeler le client et envoyer un rappel par e-mail."
        elif proba_no_show >= 0.4:
            prediction_action = "Action suggérée : Envoyer un rappel par SMS."
        else:
            prediction_action = "Aucune action requise."

    except FileNotFoundError:
        messages.error(request, "Erreur : Le fichier du modèle de prédiction (scaler.pkl ou no_show_model.pkl) est introuvable.")
        prediction_result = None
        prediction_action = "Le modèle est indisponible."
    except Exception as e:
        messages.error(request, f"Une erreur est survenue lors de la prédiction : {e}")
        prediction_result = None
        prediction_action = "Erreur lors du calcul de la prédiction."

    context = {
        'appointment': appointment,
        'prediction_result': prediction_result,
        'prediction_action': prediction_action,
    }
    return render(request, 'backoffice/prediction_result.html', context)


@require_POST
def coupon_generate(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        payload = json.loads(request.body)
    except Exception:
        payload = {}

    blocks = int(payload.get('blocks', 1))
    if blocks < 1:
        return JsonResponse({'error': 'Invalid blocks value'}, status=400)

    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    available_blocks = wallet.points // 50
    if available_blocks < blocks:
        return JsonResponse({'error': 'Not enough points', 'available_blocks': available_blocks}, status=400)

    # Deduct points atomically
    with transaction.atomic():
        wallet.points -= blocks * 50
        wallet.save()
        amount = blocks * 10  # 10 TND per 50 points
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        coupon = Coupon.objects.create(user=request.user, code=code, amount=amount)

    return JsonResponse({'status': 'success', 'coupon_code': coupon.code, 'amount': float(coupon.amount), 'new_balance': wallet.points})


@require_http_methods(["GET"])
def coupons_list(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    coupons = list(request.user.coupons.filter(redeemed=False).values('code', 'amount', 'created_at'))
    return JsonResponse({'status': 'success', 'coupons': coupons})


@require_POST
def coupon_redeem(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    try:
        payload = json.loads(request.body)
    except Exception:
        payload = {}
    code = payload.get('code')
    if not code:
        return JsonResponse({'error': 'Missing code'}, status=400)
    try:
        coupon = Coupon.objects.get(code=code, user=request.user, redeemed=False)
    except Coupon.DoesNotExist:
        return JsonResponse({'error': 'Coupon not found or already redeemed'}, status=404)
    coupon.redeemed = True
    coupon.redeemed_at = timezone.now()
    coupon.save()
    return JsonResponse({'status': 'success', 'code': coupon.code, 'amount': float(coupon.amount)})


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

def training_program_detail_view(request, pk):
    training_program = get_object_or_404(TrainingProgram, pk=pk)
    return render(request, 'main/training_program_detail.html', {
        'training_program': training_program
    })
