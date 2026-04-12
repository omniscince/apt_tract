from django.db import models
from customers.models import Customer


class Car(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='cars')
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField(blank=True, null=True)
    stock_number = models.CharField(max_length=50, blank=True)
    vin = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.make} {self.model} - {self.customer.name}'

    class Meta:
        ordering = ['-created_at']