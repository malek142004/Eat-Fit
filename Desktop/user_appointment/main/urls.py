from django.urls import path
from . import views
app_name = "main"

urlpatterns = [
   

  
    path('about/', views.about, name='about'),
    path('blog/', views.blog, name='blog'),
    path('classes-details/', views.classes_details, name='classes-details'),
    path('classes/', views.classes, name='classes'),
    path('contact/', views.contact, name='contact'),
    path('event-details/', views.event_details, name='event-details'),
    path('events/', views.events, name='events'),
    path('', views.index, name='index'),
    path('main/', views.main_page, name='main'),
    path('single-blog/', views.single_blog, name='single-blog'),
    path('trainer-details/', views.trainer_details, name='trainer-details'),
    path('trainer/', views.trainer, name='trainer'),
    # Route racine du backoffice : redirige vers la page de login backoffice
    path('backoffice/', views.backoffice_dashboard, name='backoffice_root'),
    path('backoffice/blank/', views.backoffice_blank, name='backoffice_blank'),
    path('backoffice/cards/', views.backoffice_cards, name='backoffice_cards'),
    path('backoffice/charts/', views.backoffice_charts, name='backoffice_charts'),
    path('backoffice/forgot-password/', views.backoffice_forgot_password, name='backoffice_forgot_password'),
    path('backoffice/login/', views.backoffice_login, name='backoffice_login'),
    path('backoffice/register/', views.backoffice_register, name='backoffice_register'),
    path("backoffice/tables_user/", views.users_list, name="users_list"),
    path('backoffice/tables_nutritionists/', views.backoffice_tables, name='backoffice_nutritionist_list'),
   


    # Backoffice Appointment CRUD URLs
    path('backoffice/appointments/', views.backoffice_appointments_list, name='backoffice_appointments_list'),
    path('backoffice/appointments/add/', views.backoffice_appointment_create, name='backoffice_appointment_create'),
    path('backoffice/appointments/modify/<int:pk>/', views.backoffice_appointment_update, name='backoffice_appointment_update'),
    path('backoffice/appointments/delete/<int:pk>/', views.backoffice_appointment_delete, name='backoffice_appointment_delete'),
]