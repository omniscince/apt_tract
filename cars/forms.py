from django import forms
from .models import Car
from customers.models import Customer


class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ['customer', 'make', 'model', 'year', 'stock_number', 'vin']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'make': forms.TextInput(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_number': forms.TextInput(attrs={'class': 'form-control'}),
            'vin': forms.TextInput(attrs={'class': 'form-control'}),
        }