from django.db import models
from customers.models import Customer


class Car(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='cars')
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100, blank=True)
    year = models.IntegerField(blank=True, null=True)
    stock_number = models.CharField(max_length=50, blank=True)
    vin = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        parts = [self.make]
        if self.model:
            parts.append(self.model)
        if self.year:
            parts.append(str(self.year))
        return ' '.join(parts)

    def get_display_with_details(self):
        result = str(self)
        extras = []
        if self.stock_number:
            extras.append(f'Stock#: {self.stock_number}')
        if self.vin:
            extras.append(f'VIN: {self.vin}')
        if extras:
            result += f' ( {", ".join(extras)})'
        return result

    def get_last_invoice_date(self):
        last = self.invoices.order_by('-invoice_date').first()
        return last.invoice_date if last else None

    class Meta:
        ordering = ['-created_at']