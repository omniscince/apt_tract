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
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Make (e.g. BMW)',
            'id': 'id_car_make',
        }),
        label='Car Make'
    )
    car_model = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Model (e.g. X5)',
            'id': 'id_car_model',
        }),
        label='Car Model'
    )
    car_year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Year (e.g. 2020)',
            'id': 'id_car_year',
        }),
        label='Car Year'
    )
    car_vin = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'VIN Number',
            'id': 'id_car_vin',
        }),
        label='VIN'
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

    class Meta:
        model = Invoice
        fields = [
            'invoice_date', 'due_date', 'po_number',
            'last_edit_date', 'work_completed_by', 'notes'
        ]
        widgets = {
            'invoice_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'po_number': forms.TextInput(attrs={'class': 'form-control'}),
            'last_edit_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'work_completed_by': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.now().date()
        if not self.instance.pk:
            self.fields['invoice_date'].initial = today
            self.fields['due_date'].initial = today + relativedelta(months=1)

        # If editing, prefill customer and car fields
        if self.instance and self.instance.pk:
            self.fields['customer_name'].initial = self.instance.get_customer_display()
            if self.instance.car:
                self.fields['car_make'].initial = self.instance.car.make
                self.fields['car_model'].initial = self.instance.car.model
                self.fields['car_year'].initial = self.instance.car.year
                self.fields['car_vin'].initial = self.instance.car.vin
                self.fields['car_stock'].initial = self.instance.car.stock_number
            elif self.instance.car_info:
                self.fields['car_make'].initial = self.instance.car_info


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['description', 'price']
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Service description'
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