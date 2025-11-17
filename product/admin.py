from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Columns shown in the product list in admin
    list_display = (
        'product_name', 
        'category', 
        'price', 
        'discount', 
        'business_owner', 
        'calories',       # new
    )
    
    # Filters on the right side
    list_filter = ('category', 'business_owner')
    
    # Search bar
    search_fields = ('product_name', 'business_owner__business_name')
    
    fieldsets = (
        (None, {
            'fields': (
                'business_owner',
                'product_name',
                'description',
                'category',
                'price',
                'discount',
                'image_url',
                'ingredients',   
                'calories',    
            )
        }),
    )
