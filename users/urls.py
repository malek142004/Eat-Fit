from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    path('', views.index, name='index'),      # → Page accueil
    path('auth/', views.auth_view, name='auth'), # → Page login/signup
    path('about/', views.about, name='about'),
    path('classes/', views.classes, name='classes'),
    path('blog/', views.blog, name='blog'),
    path('contact/', views.contact, name='contact'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('delete/', views.delete_profile, name='delete_profile'),
    path('backoffice/', views.backoffice_dashboard, name='backoffice_dashboard'),
    path('backoffice/blank/', views.backoffice_blank, name='backoffice_blank'),
    path('backoffice/cards/', views.backoffice_cards, name='backoffice_cards'),
    path('backoffice/charts/', views.backoffice_charts, name='backoffice_charts'),
    path('backoffice/forgot-password/', views.backoffice_forgot_password, name='backoffice_forgot_password'),
    path('backoffice/login/', views.backoffice_login, name='backoffice_login'),
    path('backoffice/register/', views.backoffice_register, name='backoffice_register'),
    path('backoffice/tables/', views.users_list, name='users_list'),
    path('modifier/<int:id>/', views.modifier_utilisateur, name='modifier_utilisateur'),
    path('supprimer/<int:id>/', views.supprimer_utilisateur, name='supprimer_utilisateur'),
    path('login/', views.backoffice_login, name='login'),
    path('logout_back/', views.backoffice_logout, name='logout_back'),
    path('ajouter/', views.ajouter_utilisateur, name='ajouter_utilisateur'),
]

