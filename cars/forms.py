from django import forms
from .models import Car
from customers.models import Customer


class CarForm(forms.ModelForm):
    customer_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Start typing customer name...',
            'id': 'id_car_customer_name',
            'autocomplete': 'off',
        }),
        label='Customer'
    )

    class Meta:
        model = Car
        fields = ['make', 'model', 'year', 'vin', 'stock_number']
        widgets = {
            'make': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. BMW'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. X5'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2020'}),
            'vin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VIN Number'}),
            'stock_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Stock #'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.customer:
            self.fields['customer_name'].initial = self.instance.customer.name  