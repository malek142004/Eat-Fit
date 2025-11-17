# main/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='index'),  # changed from 'home' to 'index'
    path('about/', views.about, name='about'),
    path('classes/', views.classes, name='classes'),
    path('class-details/', views.classes_details, name='classes-details'),
    path('trainers/', views.trainers, name='trainer'),
    path('events/', views.events, name='events'),
    path('event-details/', views.single_blog, name='event-details'),
    path('trainer-details/', views.trainer_details, name='trainer-details'),
    path('blog/', views.blog, name='blog'),
    path('single-blog/', views.blog_details, name='single-blog'),
    path('contact/', views.contact, name='contact'),
]

