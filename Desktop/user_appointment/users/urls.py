from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
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
    path('backoffice/users-pdf/', views.users_pdf, name='users_pdf'),
    path('backoffice/users-stats/', views.users_stats, name='users_stats'),

    
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

    # Business Owners CRUD
    path('businessowner/businessowner/', views.create_or_edit_business, name='create_business'),

    #business owner backoffice
    path('manage-business/', views.backoffice_manage_businessowners, name='manage_businessowners'),
    path('manage-business/add/', views.backoffice_add_businessowner, name='backoffice_add_businessowner'),
    path('manage-business/edit/<int:owner_id>/', views.backoffice_edit_businessowner, name='backoffice_edit_businessowner'),
    path('manage-business/delete/<int:owner_id>/', views.backoffice_delete_businessowner, name='backoffice_delete_businessowner'),
    path('manage-products/', views.backoffice_manage_products, name='backoffice_manage_products'),
    path('manage-products/add/', views.backoffice_add_product, name='backoffice_add_product'),
    path('manage-products/edit/<int:product_id>/', views.backoffice_edit_product, name='backoffice_edit_product'),
    path('manage-products/delete/<int:product_id>/', views.backoffice_delete_product, name='backoffice_delete_product'),
    path('manage-products/details/<int:product_id>/', views.backoffice_product_details, name='backoffice_product_details'),

    # Password reset paths
    path('forgot/', views.forgot, name='forgot'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset/<uidb64>/<token>/', views.reset_password, name='reset_password'),
]
