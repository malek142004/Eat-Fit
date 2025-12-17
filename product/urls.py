from django.urls import path
from . import views
app_name = 'product'
urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('add/', views.product_create, name='product_create'),
    path('update/<int:pk>/', views.product_update, name='product_update'),
    path('delete/<int:pk>/', views.product_delete, name='product_delete'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    path('generate-product-info/', views.generate_product_info, name='generate_product_info'),
    

]
