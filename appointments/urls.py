from django.urls import path
from . import views
from .views import GenerateTrainingPDFView, FeedbackListCreateView, FeedbackDeleteView, training_programs_view, feedback_view
from .views import TrainingProgramCreateView, TrainingProgramUpdateView, TrainingProgramDeleteView, TrainingProgramListView

app_name = 'appointments'

urlpatterns = [
    path('', views.appointment_list, name='appointment_list'),
    path('add/<int:professional_id>/', views.create_appointment_request, name='add_appointment_with_professional'),
    path('add/', views.create_appointment_request, name='add_appointment'),
    path('modify/<int:pk>/', views.appointment_update, name='appointment_update'),
    path('delete/<int:pk>/', views.appointment_delete, name='appointment_delete'),
    path('report/pdf/', views.generate_pdf_report, name='generate_pdf_report'),
    path('backoffice/', views.backoffice_appointments_list, name='backoffice_appointment_list'),
    path('backoffice/add/', views.backoffice_appointment_create, name='backoffice_appointment_create'),
    path('backoffice/modify/<int:pk>/', views.backoffice_appointment_update, name='backoffice_appointment_update'),
    path('backoffice/delete/<int:pk>/', views.backoffice_appointment_delete, name='backoffice_appointment_delete'),
    path('initiate_payment/<int:pk>/', views.initiate_payment, name='initiate_payment'),
    path('confirm_payment/<int:pk>/', views.confirm_payment, name='confirm_payment'),
    path('api/appointments/', views.api_appointments, name='api_appointments_list'),
    path('api/appointments/<int:pk>/', views.api_appointments, name='api_appointments_detail'),
    path('api/available_slots/', views.api_available_slots, name='api_available_slots'),
    
    path('training/export/pdf', GenerateTrainingPDFView.as_view(), name='generate_training_pdf'),
    
    path('feedback/<int:coach_id>/', FeedbackListCreateView.as_view(), name='feedback-list-create'),
    path('feedback/<int:pk>/delete/', FeedbackDeleteView.as_view(), name='feedback-delete'),
    
    path('training_programs/create/', TrainingProgramCreateView.as_view(), name='training_program_create'),
    path('training_programs/<int:pk>/edit/', TrainingProgramUpdateView.as_view(), name='training_program_edit'),
    path('training_programs/<int:pk>/delete/', TrainingProgramDeleteView.as_view(), name='training_program_delete'),
    path('training_programs/', TrainingProgramListView.as_view(), name='training_program_list'),
    path('training_programs/<int:pk>/pdf/', views.generate_training_program_pdf, name='training_program_pdf'),
    path('training_programs/<int:pk>/', views.training_program_detail_view, name='training_program_detail'),
    
    path('coaches/<int:coach_id>/', views.coach_detail_view, name='coach_detail'),
    path('coaches/<int:coach_id>/training_programs/', views.coach_training_programs_view, name='coach_training_programs'),
]