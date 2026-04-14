from django import forms
from .models import Customer, CustomerEmail


class CustomerEmailForm(forms.ModelForm):
    class Meta:
        model = CustomerEmail
        fields = ['email', 'is_primary']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


CustomerEmailFormSet = forms.inlineformset_factory(
    Customer,
    CustomerEmail,
    form=CustomerEmailForm,
    extra=1,
    can_delete=True,
)


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'name', 'business_number',
            'phone', 'address', 'city', 'province',
            'postal_code', 'country'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'business_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Business Number (BN)'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'province': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Province'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postal Code'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
        }