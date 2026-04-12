from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem
from customers.models import Customer
from cars.models import Car


class InvoiceForm(forms.ModelForm):
    customer_name_manual = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter customer name manually',
            'id': 'id_customer_name_manual',
        }),
        label='Customer Name (manual)'
    )
    car_info_manual = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 2020 BMW 3 Series',
            'id': 'id_car_info_manual',
        }),
        label='Car Info (manual)'
    )

    class Meta:
        model = Invoice
        fields = [
            'customer', 'customer_name', 'car', 'car_info',
            'status', 'invoice_date', 'due_date', 'po_number',
            'work_order_close_date', 'work_completed_by', 'notes'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control', 'id': 'id_customer'}),
            'customer_name': forms.HiddenInput(),
            'car': forms.Select(attrs={'class': 'form-control', 'id': 'id_car'}),
            'car_info': forms.HiddenInput(),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'invoice_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'po_number': forms.TextInput(attrs={'class': 'form-control'}),
            'work_order_close_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'work_completed_by': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        customer = cleaned_data.get('customer')
        customer_name_manual = cleaned_data.get('customer_name_manual', '').strip()

        if not customer and not customer_name_manual:
            raise forms.ValidationError('Please select an existing customer or enter a customer name manually.')

        if not customer and customer_name_manual:
            cleaned_data['customer_name'] = customer_name_manual

        car = cleaned_data.get('car')
        car_info_manual = cleaned_data.get('car_info_manual', '').strip()
        if not car and car_info_manual:
            cleaned_data['car_info'] = car_info_manual

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        customer_name_manual = self.cleaned_data.get('customer_name_manual', '').strip()
        car_info_manual = self.cleaned_data.get('car_info_manual', '').strip()

        if not instance.customer and customer_name_manual:
            instance.customer_name = customer_name_manual
        if not instance.car and car_info_manual:
            instance.car_info = car_info_manual

        if commit:
            instance.save()
        return instance


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['description', 'price']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Service description'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
        }


InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    extra=3,
    can_delete=True,
)