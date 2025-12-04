from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import TrainingProgram, Feedback

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
