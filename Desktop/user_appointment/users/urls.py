from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
       # → Page accueil
    path('auth/', views.auth_view, name='auth'), # → Page login/signup
    
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('delete/', views.delete_profile, name='delete_profile'),
   


    path('modifier/<int:id>/', views.modifier_utilisateur, name='modifier_utilisateur'),
    path('supprimer/<int:id>/', views.supprimer_utilisateur, name='supprimer_utilisateur'),
    path('login/', views.backoffice_login, name='login'),
    path('logout_back/', views.backoffice_logout, name='logout_back'),
    path('ajouter/', views.ajouter_utilisateur, name='ajouter_utilisateur'),

    path('backoffice/tables_user/', views.users_list, name='users_list'),
    path('modifier/<int:id>/', views.modifier_utilisateur, name='modifier_utilisateur'),
    path('supprimer/<int:id>/', views.supprimer_utilisateur, name='supprimer_utilisateur'),
    path('login/', views.backoffice_login, name='login'),
    path('logout_back/', views.backoffice_logout, name='logout_back'),
    path('ajouter/', views.ajouter_utilisateur, name='ajouter_utilisateur'),
]

