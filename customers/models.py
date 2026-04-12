from django.db import models


class Customer(models.Model):
    name = models.CharField(max_length=200)
    company = models.CharField(max_length=200, blank=True)
    business_number = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='Canada')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_primary_email(self):
        email = self.emails.first()
        return email.email if email else ''

    def get_all_emails(self):
        return [e.email for e in self.emails.all()]

    class Meta:
        ordering = ['name']


class CustomerEmail(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='emails')
    email = models.EmailField()
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return self.email

    class Meta:
        ordering = ['-is_primary', 'email']