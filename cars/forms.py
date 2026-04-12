from django import forms
from .models import Car
from customers.models import Customer


class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ['customer', 'make', 'model', 'year', 'vin', 'stock_number']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'make': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. BMW'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. X5'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2020'}),
            'vin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VIN Number'}),
            'stock_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Stock #'}),
        }