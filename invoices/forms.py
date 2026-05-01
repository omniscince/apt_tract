from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import Invoice, InvoiceItem


class InvoiceForm(forms.ModelForm):
    customer_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Start typing customer name...',
            'id': 'id_customer_name',
            'autocomplete': 'off',
        }),
        label='Customer'
    )
    car_make = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Make (e.g. BMW)',
            'id': 'id_car_make',
            'style': 'text-transform:uppercase;',
            'oninput': 'this.value=this.value.toUpperCase()',
        }),
        label='Car Make'
    )
    car_model = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Model (e.g. X5)',
            'id': 'id_car_model',
            'style': 'text-transform:uppercase;',
            'oninput': 'this.value=this.value.toUpperCase()',
        }),
        label='Car Model'
    )
    car_vin = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'VIN (min 8 characters)',
            'id': 'id_car_vin',
            'minlength': '8',
        }),
        label='VIN',
        min_length=0,
    )
    car_stock = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Stock #',
            'id': 'id_car_stock',
        }),
        label='Stock #'
    )

    invoice_number_override = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 2026-000005',
            'id': 'id_invoice_number_override',
        }),
        label='Invoice Number'
    )

    class Meta:
        model = Invoice
        fields = [
            'invoice_date', 'due_date', 'po_number',
            'last_edit_date', 'work_completed_by', 'notes'
        ]
        widgets = {
            'invoice_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'po_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PO Number'}),
            'last_edit_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Internal notes (not shown in PDF)'}),
            'work_completed_by': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        today = timezone.now().date()
        if not self.instance.pk:
            self.fields['invoice_date'].initial = today
            self.fields['due_date'].initial = today + relativedelta(months=1)
            self.fields['last_edit_date'].initial = today
        if self.user and self.user.role == 'staff':
            self.fields['work_completed_by'].disabled = True
            self.fields['work_completed_by'].initial = self.user

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        invoice_date = self.cleaned_data.get('invoice_date')
        if not due_date and invoice_date:
            return invoice_date + relativedelta(months=1)
        return due_date

        if self.instance and self.instance.pk:
            self.initial['customer_name'] = self.instance.get_customer_display()
            self.initial['invoice_number_override'] = self.instance.invoice_number
            if self.instance.car:
                self.initial['car_make'] = self.instance.car.make
                self.initial['car_model'] = self.instance.car.model
                self.initial['car_vin'] = self.instance.car.vin
                self.initial['car_stock'] = self.instance.car.stock_number
            elif self.instance.car_info:
                self.initial['car_make'] = self.instance.car_info

    def clean_car_vin(self):
        vin = self.cleaned_data.get('car_vin', '').strip()
        if vin and len(vin) < 8:
            raise forms.ValidationError('VIN must be at least 8 characters.')
        return vin


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['description', 'price']
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Service description',
                'autocomplete': 'off'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
        }


InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    extra=3,
    can_delete=True,
)