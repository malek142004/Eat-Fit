from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [


    path('backoffice/', views.backoffice_dashboard, name='backoffice_dashboard'),
    path('backoffice/blank/', views.backoffice_blank, name='backoffice_blank'),
    path('backoffice/cards/', views.backoffice_cards, name='backoffice_cards'),
    path('backoffice/charts/', views.backoffice_charts, name='backoffice_charts'),
    path('backoffice/forgot-password/', views.backoffice_forgot_password, name='backoffice_forgot_password'),
    path('backoffice/login/', views.backoffice_login, name='backoffice_login'),
    path('backoffice/register/', views.backoffice_register, name='backoffice_register'),
    path('backoffice/tables/', views.backoffice_tables, name='backoffice_tables'),
    path('backoffice/blog/<int:pk>/', views.backoffice_detail, name='backoffice_detail'),
path('backoffice/blog/<int:pk>/edit/', views.backoffice_edit, name='backoffice_edit'),
path('backoffice/blog/<int:pk>/delete/', views.backoffice_delete, name='backoffice_delete'),
path('backoffice/blog/<int:pk>/', views.backoffice_detail, name='backoffice_detail'),
    path('backoffice/blog/create/', views.backoffice_create, name='backoffice_create'),
    path('backoffice/blog/<int:blog_pk>/comment/add/', views.backoffice_comment_create, name='backoffice_comment_create'),
    path('backoffice/comment/<int:pk>/edit/', views.backoffice_comment_edit, name='backoffice_comment_edit'),
    path('backoffice/comment/<int:pk>/delete/', views.backoffice_comment_delete, name='backoffice_comment_delete'),

]