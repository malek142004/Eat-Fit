from django.urls import path
from . import views

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
]