from django import forms
from .models import Product,Rating

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'business_owner',
            'product_name',
            'description',
            'category',
            'price',
            'discount',
            'image_url',
            'ingredients',
            'calories',
        ]
        widgets = {
            'ingredients': forms.Textarea(attrs={'rows': 3}),
            'calories': forms.NumberInput(attrs={'min':0}),
        }


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=[(1,'★'), (2,'★★'), (3,'★★★'), (4,'★★★★'), (5,'★★★★★')]),
            'comment': forms.Textarea(attrs={'rows':2, 'placeholder':'Optional comment'}),
        }
