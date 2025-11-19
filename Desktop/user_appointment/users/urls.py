from django.urls import path
from . import views

app_name = "users"

urlpatterns = [
    # Auth / Account
    path('auth/', views.auth_view, name='auth'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('delete/', views.delete_profile, name='delete_profile'),

    # Nutritionists CRUD
    path('nutritionists/', views.nutritionist_list, name='nutritionist_list'),
    path('nutritionists/<int:pk>/', views.nutritionist_detail, name='nutritionist_detail'),
    path('nutritionists/new/', views.nutritionist_create, name='nutritionist_create'),
    path('nutritionists/<int:pk>/edit/', views.nutritionist_update, name='nutritionist_update'),
    path('nutritionists/<int:pk>/delete/', views.nutritionist_delete, name='nutritionist_delete'),

    # Backoffice CRUD Users
    path('backoffice/tables_user/', views.users_list, name='users_list'),
    path('modifier/<int:id>/', views.modifier_utilisateur, name='modifier_utilisateur'),
    path('supprimer/<int:id>/', views.supprimer_utilisateur, name='supprimer_utilisateur'),
    path('login/', views.backoffice_login, name='login'),
    path('logout_back/', views.backoffice_logout, name='logout_back'),
    path('ajouter/', views.ajouter_utilisateur, name='ajouter_utilisateur'),
    
    # Backoffice CRUD nutritionists
    path('backoffice/tables_nutritionists/', views.backoffice_tables, name='backoffice_nutritionist_list'),
    path('backoffice/nutritionists/new/', views.backoffice_nutritionist_create, name='backoffice_nutritionist_create'),
    path('backoffice/nutritionists/<int:pk>/edit/', views.backoffice_nutritionist_update, name='backoffice_nutritionist_update'),
    path('backoffice/nutritionists/<int:pk>/', views.backoffice_nutritionist_detail, name='backoffice_nutritionist_detail'),
    path('backoffice/nutritionists/<int:pk>/delete/', views.backoffice_nutritionist_delete, name='backoffice_nutritionist_delete'),
    # Coaches CRUD
    path('coaches/', views.coach_list, name='coach_list'), # Liste des coachs (alias 'trainers' si besoin)
    path('coaches/add/', views.coach_create, name='coach_create'),
    path('coaches/<int:pk>/', views.coach_detail, name='coach_detail'),
    path('coaches/<int:pk>/edit/', views.coach_update, name='coach_update'),
    path('coaches/<int:pk>/delete/', views.coach_delete, name='coach_delete'),
    # Backoffice CRUD Coaches
    path('backoffice/coaches/', views.manage_coaches, name='manage_coaches'),
    path('coaches/add/', views.add_coach, name='add_coach'),
    path('coaches/edit/<int:pk>/', views.coach_edit, name='coach_edit'),
    path('coaches/delete/<int:pk>/', views.coaches_coach_delete, name='coaches_coach_delete'),
]
