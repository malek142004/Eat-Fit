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


]

