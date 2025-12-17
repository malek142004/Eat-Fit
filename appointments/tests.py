from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import TrainingProgram, Feedback
from .models import Appointment
from django.urls import reverse
from datetime import date, time, timedelta
import json

User = get_user_model()

class GenerateTrainingPDFViewTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(role='client',password='password',email='client@example.com',nom_complet='Client User')
        self.training_program = TrainingProgram.objects.create(
            user=self.user,
            title='Test Program',
            description='This is a test training program.'
        )

    def test_generate_pdf_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/training/export/pdf', {'training_program_id': self.training_program.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_generate_pdf_unauthenticated(self):
        response = self.client.post('/training/export/pdf', {'training_program_id': self.training_program.id})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_generate_pdf_not_owner(self):
        other_user = User.objects.create_user(role='client', password='otherpassword', email='other@exemple.com', nom_complet='Other User')
        self.client.force_authenticate(user=other_user)
        response = self.client.post('/training/export/pdf', {'training_program_id': self.training_program.id})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class FeedbackTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.client_user = User.objects.create_user(role='client', password='password',email='client@exemple.com', nom_complet='Client User')
        self.coach_user = User.objects.create_user(role='coach', password='password',email='coach@exemple.com', nom_complet='Coach User')
        self.feedback = Feedback.objects.create(
            client=self.client_user,
            coach=self.coach_user,
            rating=5,
            comment='Great coach!'
        )

    def test_create_feedback(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post(f'/feedback/{self.coach_user.id}/', {
            'rating': 4,
            'comment': 'Good coach.'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Feedback.objects.count(), 2)

    def test_list_feedback(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(f'/feedback/{self.coach_user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_delete_feedback(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.delete(f'/feedback/{self.feedback.id}/delete/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Feedback.objects.count(), 0)


class QuickPredictViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create a staff user
        self.staff_user = User.objects.create_user(role='admin', password='password', email='admin@example.com', nom_complet='Admin User', is_staff=True)
        # Create a client user
        self.client_user = User.objects.create_user(role='client', password='password', email='client2@example.com', nom_complet='Client User')
        # Create an appointment for the client
        self.appointment = Appointment.objects.create(
            client=self.client_user,
            appointment_date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0)
        )

    def test_quick_predict_renders_for_staff(self):
        # Login as staff using the Django test client
        self.client.force_authenticate(user=self.staff_user)
        url = reverse('appointments:backoffice_quick_predict', args=[self.appointment.id])
        response = self.client.get(url)
        # Should return 200 (template rendered, even if model file missing)
        self.assertIn(response.status_code, (200, 302))

    def test_prediction_post_without_login(self):
        url = reverse('appointments:backoffice_prediction_result', args=[self.appointment.id])
        # POST minimal valid data
        response = self.client.post(url, {'age': 28, 'gender': '1'})
        # Expect a redirect (to manual form) or a 200 rendering result; accept 200/302
        self.assertIn(response.status_code, (200, 302))


class AddAppointmentAccessTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client_user = User.objects.create_user(role='client', password='password', email='client@example.com', nom_complet='Client')
        self.admin_user = User.objects.create_user(role='admin', password='password', email='admin@example.com', nom_complet='Admin', is_staff=True)

    def test_client_can_access_add(self):
        self.client.force_login(self.client_user)
        url = reverse('appointments:add_appointment')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_admin_can_access_add(self):
        self.client.force_login(self.admin_user)
        url = reverse('appointments:add_appointment')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_anonymous_redirected(self):
        url = reverse('appointments:add_appointment')
        response = self.client.get(url)
        self.assertIn(response.status_code, (302, 401))


class CouponTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(role='client', password='password', email='couponuser@example.com', nom_complet='Coupon User')
        # ensure wallet exists and has points
        from .models import Wallet
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user)
        self.wallet.points = 120
        self.wallet.save()

    def test_generate_single_coupon(self):
        self.client.force_login(self.user)
        response = self.client.post('/appointments/coupons/generate/', data=json.dumps({'blocks': 1}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body.get('status'), 'success')
        self.assertIn('coupon_code', body)
        self.assertEqual(body.get('new_balance'), 70)  # 120 - 50 = 70

    def test_generate_multiple_blocks(self):
        self.client.force_login(self.user)
        response = self.client.post('/appointments/coupons/generate/', data=json.dumps({'blocks': 2}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body.get('status'), 'success')
        self.assertEqual(body.get('new_balance'), 20)  # 120 - 100 = 20

    def test_not_enough_points(self):
        self.client.force_login(self.user)
        response = self.client.post('/appointments/coupons/generate/', data=json.dumps({'blocks': 3}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body.get('error'), 'Not enough points')


class BackofficeWalletDisplayTests(TestCase):
    def setUp(self):
        from django.test import Client
        self.client = Client()
        # create staff user to access backoffice
        self.staff = User.objects.create_user(role='admin', password='password', email='staff@example.com', nom_complet='Staff', is_staff=True)
        self.client_user = User.objects.create_user(role='client', password='password', email='client_wallet@example.com', nom_complet='ClientWallet')
        # create wallet with points
        from .models import Wallet
        Wallet.objects.create(user=self.client_user, points=85)
        # create an appointment for this client
        self.appointment = Appointment.objects.create(
            client=self.client_user,
            appointment_date=date.today() + timedelta(days=2),
            start_time=time(9, 0),
            end_time=time(10, 0)
        )

    def test_backoffice_shows_wallet_points(self):
        self.client.force_login(self.staff)
        url = reverse('appointments:backoffice_appointment_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Ensure the wallet points are displayed with 'pts'
        self.assertContains(response, '85 pts')

    def test_backoffice_reflects_updated_wallet_points(self):
        # Create an appointment and then update wallet points afterwards
        from .models import Wallet
        # ensure appointment exists
        appt = self.appointment
        # initially set wallet to 0
        w = Wallet.objects.get(user=self.client_user)
        w.points = 0
        w.save()

        self.client.force_login(self.staff)
        url = reverse('appointments:backoffice_appointment_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '0 pts')

        # now update wallet to 30 and re-request the page
        w.points = 30
        w.save()
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, 200)
        self.assertContains(response2, '30 pts')
