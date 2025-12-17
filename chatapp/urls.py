from django.urls import path
from . import views
app_name = "chatapp"

urlpatterns = [
    path('chatb/', views.chatb, name='chatb'),   # page HTML
    path('chat/', views.chat, name='chat'),      # endpoint JSON
]
