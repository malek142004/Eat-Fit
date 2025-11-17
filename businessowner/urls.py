from django.urls import path
from . import views

urlpatterns = [
    path('', views.create_or_edit_business, name='create_business'),

]
