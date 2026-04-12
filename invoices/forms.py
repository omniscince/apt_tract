from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem
from customers.models import Customer
from cars.models import Car


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['customer', 'car', 'status', 'invoice_date', 'due_date', 'po_number', 'work_order_close_date', 'work_completed_by', 'notes']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control', 'id': 'id_customer'}),
            'car': forms.Select(attrs={'class': 'form-control', 'id': 'id_car'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'invoice_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'po_number': forms.TextInput(attrs={'class': 'form-control'}),
            'work_order_close_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'work_completed_by': forms.Select(attrs={'class': 'form-control'}),
        }


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