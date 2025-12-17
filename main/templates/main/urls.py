from django.urls import path
from . import views

urlpatterns = [
    # Accept common misspelling so the site still responds at the requested URL
    path('nutrtionnists/', views.nutritionist_list),
    path('nutrtionnists/<int:pk>/', views.nutritionist_detail),

    path('nutritionists/', views.nutritionist_list, name='nutritionist_list'),
    path('nutritionists/<int:pk>/', views.nutritionist_detail, name='nutritionist_detail'),
    path('nutritionists/new/', views.nutritionist_create, name='nutritionist_create'),
    path('nutritionists/<int:pk>/edit/', views.nutritionist_update, name='nutritionist_update'),
    path('nutritionists/<int:pk>/delete/', views.nutritionist_delete, name='nutritionist_delete'),
    path('nutritionists/geocode/', views.geocode_address, name='geocode_address'),
    #path recherche
    path("search-nutritionists/", views.ajax_search_nutritionists, name="ajax_search_nutritionists"),
    #path pdf
    path('nutritionists/pdf/', views.nutritionist_list_pdf, name='nutritionist_list_pdf'),
    path('nutritionists/download/pdf/', views.nutritionist_list_pdf, name='backoffice_nutritionist_list_pdf'),

    # Food analysis
    path('analyze-food-image/', views.analyze_food_image, name='analyze_food_image'),
    path('generate-nutrition-pdf/', views.generate_nutrition_pdf, name='generate_nutrition_pdf'),

    # Backoffice URLs
    path('backoffice/', views.backoffice_dashboard, name='backoffice_dashboard'),
    path('backoffice/blank/', views.backoffice_blank, name='backoffice_blank'),
    path('backoffice/cards/', views.backoffice_cards, name='backoffice_cards'),
    path('backoffice/charts/', views.backoffice_charts, name='backoffice_charts'),
    path('backoffice/forgot-password/', views.backoffice_forgot_password, name='backoffice_forgot_password'),
    path('backoffice/login/', views.backoffice_login, name='backoffice_login'),
    path('backoffice/register/', views.backoffice_register, name='backoffice_register'),
    path('backoffice/tables_nutritionists/', views.backoffice_nutritionist_list, name='backoffice_tables'),
    path('backoffice/tables_nutritionists/', views.backoffice_nutritionist_list, name='backoffice_nutritionist_list'),

    #---------------------------------------
    path('nutritionists/stats/cities/', views.nutritionist_city_stats, name='backoffice_nutritionist_city_stats'),

    # Backoffice-specific nutritionist delete (keeps front/back separation)
    path('backoffice/nutritionists/new/', views.backoffice_nutritionist_create, name='backoffice_nutritionist_create'),
    path('backoffice/nutritionists/<int:pk>/edit/', views.backoffice_nutritionist_update, name='backoffice_nutritionist_update'),
    path('backoffice/nutritionists/<int:pk>/', views.backoffice_nutritionist_detail, name='backoffice_nutritionist_detail'),
    path('backoffice/nutritionists/<int:pk>/delete/', views.backoffice_nutritionist_delete, name='backoffice_nutritionist_delete'),

]