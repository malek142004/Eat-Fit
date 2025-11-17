from django.urls import path
from . import views

urlpatterns = [
    path('', views.backoffice_dashboard, name='backoffice_dashboard'),
    path('blank/', views.backoffice_blank, name='backoffice_blank'),
    path('cards/', views.backoffice_cards, name='backoffice_cards'),
    path('charts/', views.backoffice_charts, name='backoffice_charts'),
    path('forgot-password/', views.backoffice_forgot_password, name='backoffice_forgot_password'),
    path('login/', views.backoffice_login, name='backoffice_login'),
    path('register/', views.backoffice_register, name='backoffice_register'),
    path('tables/', views.backoffice_tables, name='backoffice_tables'),
    path('manage-business/', views.backoffice_manage_businessowners, name='manage_businessowners'),
    path('manage-business/', views.backoffice_manage_businessowners, name='manage_businessowners'),
    path('manage-business/add/', views.backoffice_add_businessowner, name='backoffice_add_businessowner'),
    path('manage-business/edit/<int:owner_id>/', views.backoffice_edit_businessowner, name='backoffice_edit_businessowner'),
    path('manage-business/delete/<int:owner_id>/', views.backoffice_delete_businessowner, name='backoffice_delete_businessowner'),
    path('manage-products/', views.backoffice_manage_products, name='backoffice_manage_products'),
    path('manage-products/add/', views.backoffice_add_product, name='backoffice_add_product'),
    path('manage-products/edit/<int:product_id>/', views.backoffice_edit_product, name='backoffice_edit_product'),
    path('manage-products/delete/<int:product_id>/', views.backoffice_delete_product, name='backoffice_delete_product'),
    path('manage-products/details/<int:product_id>/', views.backoffice_product_details, name='backoffice_product_details'),

]
