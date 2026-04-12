from django.db import models
from django.utils import timezone
from customers.models import Customer
from cars.models import Car
from users.models import User


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('declined', 'Declined'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    customer_name = models.CharField(max_length=200, blank=True)
    car = models.ForeignKey(Car, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    car_info = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_invoices')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    invoice_date = models.DateField(default=timezone.now)
    due_date = models.DateField(blank=True, null=True)
    po_number = models.CharField(max_length=50, blank=True, default='N/A')
    last_edit_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    work_completed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_invoices'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Invoice #{self.invoice_number} - {self.get_customer_display()}'

    def get_customer_display(self):
        if self.customer:
            return self.customer.name
        return self.customer_name or 'Unknown'

    def get_car_display(self):
        if self.car:
            return self.car.get_display_with_details()
        return self.car_info or '—'

    @property
    def subtotal(self):
        return sum(item.total for item in self.items.all())

    @property
    def hst(self):
        from decimal import Decimal
        from django.conf import settings
        rate = getattr(settings, 'HST_RATE', Decimal('0.13'))
        return round(self.subtotal * Decimal(str(rate)), 2)

    @property
    def total(self):
        return round(self.subtotal + self.hst, 2)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            year = timezone.now().year
            last = Invoice.objects.filter(
                invoice_number__startswith=f'{year}-'
            ).order_by('-invoice_number').first()
            if last:
                try:
                    last_num = int(last.invoice_number.split('-')[1])
                    self.invoice_number = f'{year}-{str(last_num + 1).zfill(6)}'
                except (IndexError, ValueError):
                    self.invoice_number = f'{year}-000001'
            else:
                self.invoice_number = f'{year}-000001'
        if not self.due_date:
            from dateutil.relativedelta import relativedelta
            self.due_date = self.invoice_date + relativedelta(months=1)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=500)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.description} - ${self.price}'

    @property
    def total(self):
        return self.price