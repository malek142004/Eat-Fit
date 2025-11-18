from django.urls import path
from . import views

app_name = 'blogapp'

urlpatterns = [
    path('', views.blog_list, name='blog_list'),
    path('blog/new/', views.blog_create, name='blog_create'),
    path('blog/<int:pk>/', views.blog_detail, name='blog_detail'),
    path('blog/<int:pk>/edit/', views.blog_update, name='blog_update'),
    path('blog/<int:pk>/delete/', views.blog_delete, name='blog_delete'),
    path('blog/<int:pk>/like/', views.toggle_like, name='toggle_like'),
]
