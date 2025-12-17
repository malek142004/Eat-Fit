from django.urls import path
from . import views

app_name = 'blogapp'

urlpatterns = [
    path('', views.blog_list, name='blog_list'),
    path('new/', views.blog_create, name='blog_create'),
    path('<int:pk>/', views.blog_detail, name='blog_detail'),
    path('<int:pk>/edit/', views.blog_update, name='blog_update'),
    path('<int:pk>/delete/', views.blog_delete, name='blog_delete'),
    path('<int:pk>/like/', views.toggle_like, name='toggle_like'),
    path('blog/<int:pk>/pdf/', views.blog_to_pdf, name='blog_pdf'),
    path('blog/<int:pk>/summary/', views.summarize_blog, name='blog_summary'),

   
    path('backoffice/tables_blogs/', views.backoffice_tables, name='blogs_list'),
    path('backoffice/blog/<int:pk>/', views.backoffice_detail, name='backoffice_detail'),
    path('backoffice/blog/<int:pk>/edit/', views.backoffice_edit, name='backoffice_edit'),
    path('backoffice/blog/<int:pk>/delete/', views.backoffice_delete, name='backoffice_delete'),
    path('backoffice/blog/create/', views.backoffice_create, name='backoffice_create'),
    path('backoffice/blog/<int:blog_pk>/comment/add/', views.backoffice_comment_create, name='backoffice_comment_create'),
    path('backoffice/comment/<int:pk>/edit/', views.backoffice_comment_edit, name='backoffice_comment_edit'),
    path('backoffice/comment/<int:pk>/delete/', views.backoffice_comment_delete, name='backoffice_comment_delete'),
]
